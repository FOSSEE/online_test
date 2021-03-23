import io
import re
import os
import json
import yaml
import requests
import more_itertools
import ruamel.yaml

from django.core.exceptions import ObjectDoesNotExist

from yaksh.models import Lesson, Course, LearningUnit, LearningModule, Quiz, TableOfContents

_HEADER_RE = re.compile(r"^---\s*$")
_BLANK_RE = re.compile(r"^\s*$")
_JUPYTER_RE = re.compile(r"^meta\s*:\s*$")
_LEFTSPACE_RE = re.compile(r"^\s")
DATA_SEP = '~#~#~#'


def recursive_update(target, update):
    """ Update recursively a (nested) dictionary with the content of another.
    Inspired from https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """
    for key in update:
        value = update[key]
        if value is None:
            del target[key]
        elif isinstance(value, dict):
            target[key] = recursive_update(target.get(key, {}), value)
        else:
            target[key] = value
    return target

def _metadata_to_dict(lines):
    metadata= {}
    ended = False
    injupyter = False
    # jupyter = []
    meta_lines = []

    for i, line in enumerate(lines):
        if i == 0 and _HEADER_RE.match(line):
            continue

        if (i > 0) and _HEADER_RE.match(line):
            ended = True

        if _JUPYTER_RE.match(line):
            injupyter = True
        elif line and not _LEFTSPACE_RE.match(line):
            injupyter = False

        if injupyter:
            meta_lines.append(line)

    if ended:
        if meta_lines:
            recursive_update(metadata, yaml.safe_load("\n".join(meta_lines)))
    return metadata

def _display_content_to_dict(lines):
    ended = False
    display_content = []

    for i, line in enumerate(lines):
        if (i > 0) and _HEADER_RE.match(line):
            ended = True
            continue

        if ended:
            display_content.append(line)

    return ''.join(display_content)


class LessonData():
    type = "lesson"
    display_content_field = 'description'
    def __init__(self, obj, order, course_id):
        toc_file = TableOfContents.objects.get_all_tocs_as_yaml(
                course_id, obj.id, '{0}_lesson_toc.yaml'.format(obj.id)
            )
        self.data = {
            "id": obj.id,
            "name": obj.name,
            "active": obj.active,
            "order": order,
        }
        if toc_file:
            self.data.update(
                {"toc": toc_file,}
            )
        self.display_content = obj.description if obj.description else None


class QuizData():
    type = "quiz"
    display_content_field = 'instructions'
    def __init__(self, obj, order):
        self.data = {
            "id": obj.id,
            "description": obj.description,
            "active": obj.active,
            "start_date_time": obj.start_date_time,
            "end_date_time": obj.end_date_time,
            "duration": obj.duration,
            "pass_criteria": obj.pass_criteria,
            "attempts_allowed": obj.attempts_allowed,
            "allow_skip": obj.allow_skip,
            "view_answerpaper": obj.view_answerpaper,
            "order": order,
        }
        self.display_content = obj.instructions if obj.instructions else None


class UnitData():

    @classmethod
    def get_lesson_or_quiz_data(cls, units, course_id):
        return [
            LessonData(unit_obj.lesson, unit_obj.order, course_id) 
            if unit_obj.lesson else QuizData(unit_obj.quiz, unit_obj.order)
            for unit_obj in units
        ]        

    @classmethod
    def md_to_dict(cls, lines):
        all_unit_data = list(
            more_itertools.split_at(
                    lines, 
                    lambda x: x.strip('\n') == DATA_SEP
                )
        )
        learning_units = []
        module_data = None
        for unit_lines in all_unit_data:
            if unit_lines:
                metadata = _metadata_to_dict(unit_lines)
                display_content = _display_content_to_dict(unit_lines)
                clean_display_content = display_content.strip('\n')
                try:
                    unit_data = metadata.get('meta', {}).get('data', {})
                    order = unit_data.pop('order', 0)
                    unit_type = metadata.get('meta', {}).get('type', None)
                    unit_cls = LessonData if unit_type == 'lesson' else QuizData
                except KeyError:
                    print("[ERROR] Data not found. Please check the MD file")

                unit_data.update(
                    {getattr(unit_cls,'display_content_field'): clean_display_content,}
                )
                if unit_type == 'lesson':
                    learning_unit_data = {
                        "order": order,
                        "type": unit_type,
                        "quiz": None,
                        "lesson": unit_data,
                    }
                    learning_units.append(learning_unit_data)
                elif unit_type == 'quiz':
                    learning_unit_data = {
                        "order": order,
                        "type": unit_type,
                        "quiz": unit_data,
                        "lesson": None,
                    }
                    learning_units.append(learning_unit_data)
                elif unit_type == 'module':
                    module_data = ModuleData.md_to_dict(unit_lines)

        return {'module': module_data, 'learning_units': learning_units}

    @classmethod
    def md_to_dict_from_file(cls, file):
        with open(file, 'r') as f:
            lines = f.readlines()
        return cls.md_to_dict(lines)


class ModuleData():
    type = "module"
    display_content_field = 'description'
    def __init__(self, obj, course_id):
        self.data = {
            "id": obj.id,
            "name": obj.name,
            "order": obj.order,
            "active":obj.active,
        }
        self.display_content = obj.description if obj.description else None
        self.units = self.set_lessons(obj.get_learning_units(), course_id)

    def set_lessons(self, units, course_id):
        return UnitData.get_lesson_or_quiz_data(units, course_id)


    @classmethod
    def md_to_dict(cls, lines):
        metadata = _metadata_to_dict(lines)
        display_content = _display_content_to_dict(lines)
        clean_display_content = display_content.strip('\n')
        try:
            data = metadata.get('meta', {}).get('data', {})
        except KeyError:
            print("[ERROR] Data not found. Please check the MD file")

        data.update({cls.display_content_field: clean_display_content})
        return data

    @classmethod
    def md_to_dict_from_file(cls, file):
        with open(file, 'r') as f:
            lines = f.readlines()
        return cls.md_to_dict(lines)


class CourseData():
    type = "course"
    display_content_field = "instructions"
    def __init__(self, obj):
        self.data = {
            "id": obj.id,
            "name": obj.name,
            "enrollment": obj.enrollment,
            "active": obj.active,
            "start_enroll_time": obj.start_enroll_time,
            "end_enroll_time": obj.end_enroll_time,
        }
        self.display_content = obj.instructions if obj.instructions else None
        self.modules = self.set_modules(obj.get_learning_modules(), obj.id)

    def set_modules(self, modules, course_id):
        return [ModuleData(module_obj, course_id) for module_obj in modules]

    @classmethod
    def md_to_dict(cls, file):
        with open(file, 'r') as f:
            lines = f.readlines()
        metadata = _metadata_to_dict(lines)
        display_content = _display_content_to_dict(lines)
        clean_display_content = display_content.strip('\n')
        try:
            data = metadata.get('meta', {}).get('data', {})
        except KeyError:
            print("[ERROR] Data not found. Please check the MD file")

        data.update({cls.display_content_field: clean_display_content})
        return data


def create_header(data, dtype):
    header = []
    metadata = {
        "type": dtype,
        "data": data
    }
    yaml=ruamel.yaml.YAML()
    yaml.default_flow_style = False
    io_obj = io.StringIO()

    yaml.dump({"meta": metadata}, io_obj)

    if metadata['data'].get('id', None):
        raw_yaml_data = yaml.load(io_obj.getvalue())
        raw_yaml_data['meta']['data'].yaml_add_eol_comment('Do Not Change This Value', 'id')
        io_obj = io.StringIO()
        yaml.dump(raw_yaml_data, io_obj)

    header.extend(io_obj.getvalue().splitlines())
    header = ["---"] + header + ["---"]

    return header


def get_course_data(course_id):
    course_obj = Course.objects.get(id=course_id)
    return CourseData(course_obj)


def _create_clean_file_name(name, ext):
    clean_name = re.sub(r'[^\w\s-]', '', name).strip().lower()
    return re.sub(r'[-\s]+', '_', clean_name) + '.' + ext

def _get_file_name_from_object(content_object, ext):
    name =  ' '.join(
        [content_object.type, content_object.data.get('name')]
    )
    return _create_clean_file_name(name, ext)



def create_md(content_object, file_name=None, multiple_obj=False):
    file_content = []
    if not file_name:
        dest_file_name = _get_file_name_from_object(content_object, 'md')
    else:
        dest_file_name = file_name
    data = content_object.data
    dtype = content_object.type
    seperator = '\n{0}\n'.format(DATA_SEP) if multiple_obj else ''
    header = create_header(data, dtype)
    if content_object.display_content:
        file_content.append(content_object.display_content)

    file_content = (
        '\n'.join(header) + '\n\n' + '\n'.join(file_content) + 
        seperator
    )

    with open(dest_file_name, 'a+') as f:
        f.write(file_content)

    return dest_file_name


def write_course_to_file(course_id):
    # Create the course md file
    course = get_course_data(course_id)
    course_file = create_md(course)

    course_map = {'course': course_file, 'modules': []}

    # Create the modules and lessons md files
    for module in course.modules:
        mod_file = create_md(module, multiple_obj=True)
        for lesson in module.units:
            create_md(lesson, mod_file, multiple_obj=True)

        course_map['modules'].append(
            {'file': mod_file,}
        )

    with open('toc.yml', 'w') as f:
        f.write(yaml.safe_dump(course_map))


def convert_md_to_dict(toc, user):
    course_file = toc.get('course')
    course_data = CourseData.md_to_dict(course_file)
    module_obj_list = []
    for module in toc.get('modules', []):
        module_file = module.get('file')
        module_data = UnitData.md_to_dict_from_file(
                module_file
            ).get('module')
        module_id = module_data.get('id', None)
        if module_id:
            mod_created = False
            module_obj = LearningModule.objects.get(id=module_id)
            module_obj.__dict__.update(module_data)
            module_obj.save()

        else:
            mod_created = True
            module_data.update({'creator': user})
            module_obj = LearningModule.objects.create(
                **module_data
            )

        unit_file = module.get('units', None)
        unit_list = UnitData.md_to_dict_from_file(module_file).get('learning_units')
        unit_obj_list = []
        for unit in unit_list:
            unit_type = unit.get('type')
            lesson_or_quiz_obj = None
            if unit_type == 'lesson':
                lq_data = unit.pop('lesson')
                lq_data.update({'creator': user})
                if lq_data.get('id'): # Lesson already exists
                    lesson_or_quiz_obj = Lesson.objects.get(id=lq_data.get('id'))
                    lesson_or_quiz_obj.__dict__.update(lq_data)
                    lesson_or_quiz_obj.save()

                    toc_file = lq_data.get('toc', None)
                    if toc_file:
                        with open(toc_file, 'r') as tocf:
                            toc_data = ruamel.yaml.safe_load_all(tocf.read())
                            results = TableOfContents.objects.add_contents(
                                course_data.get('id'), lesson_or_quiz_obj.id , user, toc_data)
                            for status, msg in results:
                                if status == False:
                                    raise Exception(msg)
                else:
                    lesson_or_quiz_obj = Lesson.objects.create(
                        **lq_data,
                    )
                    unit['lesson'] = lesson_or_quiz_obj

                    toc_file = lq_data.get('toc', None)
                    if toc_file:
                        with open(toc_file, 'r') as tocf:
                            toc_data = ruamel.yaml.safe_load_all(tocf.read())
                            results = TableOfContents.objects.add_contents(
                                course_data.get('id'), lesson_or_quiz_obj.id , user, toc_data)
                            for status, msg in results:
                                if status == False:
                                    raise Exception(msg)
            else:
                lq_data = unit.pop('quiz')
                lq_data.update({'creator': user})
                if lq_data.get('id'): # Quiz already exists
                    lesson_or_quiz_obj = Quiz.objects.get(id=lq_data.get('id'))
                    lesson_or_quiz_obj.__dict__.update(lq_data)
                    lesson_or_quiz_obj.save()
                else:
                    lesson_or_quiz_obj = Quiz.objects.create(
                        **lq_data,
                    )
                    unit['quiz'] = lesson_or_quiz_obj

            if not lq_data.get('id'):
                unit_obj, unit_created = LearningUnit.objects.create(
                    **unit
                ), True
            else:
                lesson_or_quiz_class_map = {
                    'lesson': Lesson,
                    'quiz': Quiz,
                }
                unit_created = False
                lq_obj_id = lq_data.get('id')
                lq_obj = lesson_or_quiz_class_map.get(unit_type).objects.get(id=lq_obj_id)
                m_units = module_obj.learning_unit.values_list('id', flat=True)
                lq_units = lq_obj.learningunit_set.values_list('id', flat=True)
                unit_id = list(set(m_units) & set(lq_units))[0]

                unit_obj = LearningUnit.objects.get(id=unit_id)
                unit_obj.__dict__.update({'order': unit.get('order', 0)})
                unit_obj.save()

            if unit_created:
                unit_obj_list.append(unit_obj)

        module_obj.learning_unit.add(*unit_obj_list)
        if mod_created:
            module_obj_list.append(module_obj)

    if course_data.get('id', None):
        course_obj = Course.objects.get(id=course_data.get('id'))
        course_obj.__dict__.update(course_data)
        course_obj.save()
    else:
        course_data.update({'creator': user})
        course_obj, course_created = Course.objects.create(
            **course_data
        ), True

    course_obj.learning_module.add(*module_obj_list)

    return course_obj


def check_data(toc):
    course_file = toc.get('course')
    course_data = CourseData.md_to_dict(course_file)
    course_id = course_data.get('id')
    module_id_list = []
    for data_elem in toc.get('modules', []):
        _file = data_elem.get('file')
        _data = UnitData.md_to_dict_from_file(_file)
        
        module_id = _data.get('module', None).get('id', None)
        if module_id:
            module_id_list.append(module_id)

        lesson_id_list = []
        quiz_id_list = []
        for unit in _data.get('learning_units'):
            unit_id = unit.get('id', None)
            unit_type = unit.get('type', None)
            if unit_id:
                if unit_type == 'lesson':
                    lesson_id_list.append(unit_id)
                else:
                    quiz_id_list.append(unit_id)

            try:
                if not has_relationship(module_id, 'learning_module', lesson_id_list, unit_type):
                    msg = "Lesson IDs used in metadata do not belong to current course, Kindly inspect and reupload"
                    return False, msg
                if not has_relationship(module_id, 'learning_module', quiz_id_list, unit_type):
                    msg = "Quiz IDs used in metadata do not belong to current course, Kindly inspect and reupload"
                    return False, msg
            except ObjectDoesNotExist:
                msg = "Object does not exist in DB"
                return False, msg

        try:
            if not has_relationship(course_id, 'course', module_id_list):
                msg = "Module IDs used in metadata do not belong to current course, Kindly inspect and reupload"
                return False, msg

            if has_duplicate_id(course_id, 'course', module_id_list):
                msg = "Modules metadata contains duplicate IDs, Kindly inspect and reupload"
                return False, msg
        except ObjectDoesNotExist:
            msg = "Object does not exist in DB"
            return False, msg
    return True, 'File check successful'


def get_parent_child_data_from_db(parent_id, parent_type, child_id_list, child_type=None):
    if parent_type == 'learning_module':
        mod_obj = LearningModule.objects.get(id=parent_id)
        relationship_id_list = [ e for e in
            mod_obj.learning_unit.order_by(
                "order"
            ).values_list(
                child_type + '__id', flat=True,
            ) if e != None
        ]
        return relationship_id_list

    elif parent_type == 'course':
        course_obj = Course.objects.get(id=parent_id)
        relationship_id_list = course_obj.get_learning_modules().values_list(
            'id', flat=True,
        )
        return relationship_id_list

def has_duplicate_id(parent_id, parent_type, child_id_list, child_type=None):
    relationship_id_list = get_parent_child_data_from_db(
        parent_id, parent_type, child_id_list, child_type
    )
    if len(child_id_list) != len(set(relationship_id_list)):
        return True # duplicates exist
    else: 
        return False # duplicates do not exist

def has_relationship(parent_id, parent_type, child_id_list, child_type=None):
    relationship_id_list = get_parent_child_data_from_db(
        parent_id, parent_type, child_id_list, child_type
    )

    for _id in child_id_list:
        if _id not in relationship_id_list:
            return False
    return True

def read_toc(file):
    with open(file, 'r') as f:
        toc = yaml.load(f, Loader=yaml.FullLoader)
    return toc

def upload_course(user):
    toc = read_toc('toc.yml')
    status, msg = check_data(toc)
    course_data = convert_md_to_dict(toc, user)
    return status, msg
    
