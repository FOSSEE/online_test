# Python Imports
import os
from datetime import datetime
import pytz
from textwrap import dedent

# Django Imports
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from django.db.models.fields.files import FieldFile
from taggit.managers import TaggableManager


# Local Imports
from grades.models import GradingSystem

languages = (
        ("python", "Python"),
        ("bash", "Bash"),
        ("c", "C Language"),
        ("cpp", "C++ Language"),
        ("java", "Java Language"),
        ("scilab", "Scilab"),
        ("r", "R"),
        ("other", "Other")
    )

question_types = (
    ("mcq", "Single Correct Choice"),
    ("mcc", "Multiple Correct Choices"),
    ("code", "Code"),
    ("upload", "Assignment Upload"),
    ("integer", "Answer in Integer"),
    ("string", "Answer in String"),
    ("float", "Answer in Float"),
    ("arrange", "Arrange in Correct Order"),
)


test_case_types = (
    ("standardtestcase", "Standard Testcase"),
    ("stdiobasedtestcase", "StdIO Based Testcase"),
    ("mcqtestcase", "MCQ Testcase"),
    ("hooktestcase", "Hook Testcase"),
    ("integertestcase", "Integer Testcase"),
    ("stringtestcase", "String Testcase"),
    ("floattestcase", "Float Testcase"),
    ("arrangetestcase", "Arrange Testcase"),
)


string_check_type = (
    ("lower", "Case Insensitive"),
    ("exact", "Case Sensitive"),
    )


def get_lesson_file_dir(instance, filename):
    if isinstance(instance, Lesson):
        upload_dir = f"lesson_{instance.id}"
    else:
        upload_dir = f"lesson_{instance.lesson.id}"
    return os.sep.join((upload_dir, filename))


def file_cleanup(sender, instance, *args, **kwargs):
    '''
        Deletes the file(s) associated with a model instance. The model
        is not saved after deletion of the file(s) since this is meant
        to be used with the pre_delete signal.
    '''
    for field_name, _ in instance.__dict__.items():
        field = getattr(instance, field_name)
        if issubclass(field.__class__, FieldFile) and field.name:
            field.delete(save=False)


class Course(models.Model):
    enrollment_methods = (
        ("default", "Enroll Request"),
        ("open", "Open Enrollment"),
    )
    name = models.CharField(max_length=255)
    enrollment = models.CharField(max_length=32, choices=enrollment_methods)
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=128, null=True, blank=True)
    hidden = models.BooleanField(default=False)
    owner = models.ForeignKey(User, related_name='course_creator',
                                on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    is_trial = models.BooleanField(default=False)
    instructions = models.TextField(default=None, null=True, blank=True)
    view_grade = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    start_enroll_time = models.DateTimeField(
        "Start Date and Time for enrollment of course",
        default=timezone.now,
        null=True
    )
    end_enroll_time = models.DateTimeField(
        "End Date and Time for enrollment of course",
        default=datetime(
            2199, 1, 1,
            tzinfo=pytz.timezone(timezone.get_current_timezone_name())
        ),
        null=True
    )

    grading = models.OneToOneField(GradingSystem, null=True, blank=True,
                                related_name="course_grade",
                                on_delete=models.CASCADE)

    def get_modules(self):
        return self.modules.order_by("order")

    @property
    def creator_name(self):
        return self.owner.get_full_name()

    def is_valid_user(self, user_id):
        is_creator = self.owner_id == user_id
        is_teacher = CourseTeacher.objects.filter(
            course_id=self.id, teacher_id=user_id
        ).exists()
        return is_creator or is_teacher

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    enrollment_status = (
        (1, "Pending"),
        (2, "Rejected"),
        (3, "Enrolled"),
    )
    student = models.ForeignKey(
        User, related_name='enrollment', on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course, related_name='course', on_delete=models.CASCADE
    )
    status = models.IntegerField(choices=enrollment_status)

    def __str__(self):
        return f"Enrollment status of {self.student} in {self.course}"


class CourseTeacher(models.Model):
    teacher = models.ForeignKey(
        User, related_name='teacher', on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course, related_name='allotted', on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.allotted_user.get_full_name()} teacher in {self.course}"


class Module(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default=None, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course, related_name="modules", on_delete=models.CASCADE
    )
    order = models.IntegerField(default=0)
    html_data = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    @property
    def has_units(self):
        return self.units.exists()

    def __str__(self):
        return f"{self.name} created by {self.owner}"


class Unit(models.Model):
    module = models.ForeignKey(
        Module, related_name="units", on_delete=models.CASCADE
    )
    order = models.IntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    check_prerequisite = models.BooleanField(default=False)

    def __str__(self):
        return f"Unit for {self.module.name}"


class Lesson(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    html_data = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="lesson_creator"
    )
    active = models.BooleanField(default=True)
    video_file = models.FileField(
        upload_to=get_lesson_file_dir, max_length=255, default=None,
        null=True, blank=True
        )
    video_path = models.JSONField(
        default={}, null=True, blank=True,
        )
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    content = GenericRelation(Unit, related_query_name='lessons')

    def __str__(self):
        return f"{self.name} created by {self.owner}"

pre_delete.connect(file_cleanup, sender=Lesson)


class LessonFile(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="lesson",
                               on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_lesson_file_dir, default=None)

    def __str__(self):
        return f"{self.file.name} for {self.lesson.name}"

pre_delete.connect(file_cleanup, sender=LessonFile)


class TOCManager(models.Manager):

    def get_data(self, course_id, lesson_id):
        contents = TableOfContent.objects.filter(
            lesson_id=lesson_id, content__in=[2, 3, 4]
        )
        data = {}
        for toc in contents:
            data[toc] = LessonQuizAnswer.objects.filter(
                toc_id=toc.id).values_list(
                "student_id", flat=True).distinct().count()
        return data

    def get_all_tocs_as_yaml(self, course_id, lesson_id, file_path):
        all_tocs = TableOfContent.objects.filter(
            course_id=course_id, lesson_id=lesson_id,
        )
        if not all_tocs.exists():
            return None
        for toc in all_tocs:
            toc.get_toc_as_yaml(file_path)
        return file_path

    def get_question_stats(self, toc_id):
        answers = LessonQuizAnswer.objects.get_queryset().filter(
            toc_id=toc_id).order_by('id')
        question = TableOfContent.objects.get(id=toc_id).content_object
        if answers.exists():
            answers = answers.values(
                "student__first_name", "student__last_name", "student__email",
                "student_id", "student__profile__roll_number", "toc_id"
                )
            df = pd.DataFrame(answers)
            answers = df.drop_duplicates().to_dict(orient='records')
        return question, answers

    def get_per_tc_ans(self, toc_id, question_type, is_percent=True):
        answers = LessonQuizAnswer.objects.filter(toc_id=toc_id).values(
            "student_id", "answer__answer"
        ).order_by("id")
        data = None
        if answers.exists():
            df = pd.DataFrame(answers)
            grp = df.groupby(["student_id"]).tail(1)
            total_count = grp.count().answer__answer
            data = grp.groupby(["answer__answer"]).count().to_dict().get(
                "student_id")
            if question_type == "mcc":
                tc_ids = []
                mydata = {}
                for i in data.keys():
                    tc_ids.extend(literal_eval(i))
                for j in tc_ids:
                    if j not in mydata:
                        mydata[j] = 1
                    else:
                        mydata[j] += 1
                data = mydata.copy()
            if is_percent:
                for key, value in data.items():
                    data[key] = (value/total_count)*100
        return data, total_count

    def get_answer(self, toc_id, user_id):
        submission = LessonQuizAnswer.objects.filter(
            toc_id=toc_id, student_id=user_id).last()
        question = submission.toc.content_object
        attempted_answer = submission.answer
        if question.type == "mcq":
            submitted_answer = literal_eval(attempted_answer.answer)
            answers = [
                tc.options
                for tc in question.get_test_cases(id=submitted_answer)
            ]
            answer = ",".join(answers)
        elif question.type == "mcc":
            submitted_answer = literal_eval(attempted_answer.answer)
            answers = [
                tc.options
                for tc in question.get_test_cases(id__in=submitted_answer)
            ]
            answer = ",".join(answers)
        else:
            answer = attempted_answer.answer
        return answer, attempted_answer.correct

    def add_contents(self, course_id, lesson_id, user, contents):
        toc = []
        messages = []
        for content in contents:
            name = content.get('name') or content.get('summary')
            if "content_type" not in content or "time" not in content:
                messages.append(
                    (False,
                     f"content_type or time key is missing in {name}")
                )
            else:
                content_type = content.pop('content_type')
                time = content.pop('time')
                if not is_valid_time_format(time):
                    messages.append(
                        (False,
                         f"Invalid time format in {name}. "
                         "Format should be 00:00:00")
                        )
                else:
                    if content_type == 1:
                        topic = Topic.objects.create(**content)
                        toc.append(TableOfContent(
                            course_id=course_id,
                            lesson_id=lesson_id, time=time,
                            content_object=topic, content=content_type
                        ))
                        messages.append(
                            (True, f"{topic.name} added successfully")
                        )
                    else:
                        content['user'] = user
                        test_cases = content.pop("testcase")
                        que_type = content.get('type')
                        if "files" in content:
                            content.pop("files")
                        if "tags" in content:
                            content.pop("tags")
                        if (que_type in ['code', 'upload']):
                            messages.append(
                                (False, f"{que_type} question is not allowed. "
                                 f"{content.get('summary')} is not added")
                            )
                        else:
                            que = Question.objects.create(**content)
                            for test_case in test_cases:
                                test_case_type = test_case.pop(
                                    'test_case_type'
                                )
                                model_class = get_model_class(test_case_type)
                                model_class.objects.get_or_create(
                                    question=que,
                                    **test_case, type=test_case_type
                                )
                            toc.append(TableOfContent(
                                course_id=course_id, lesson_id=lesson_id,
                                time=time, content_object=que,
                                content=content_type
                            ))
                        messages.append(
                            (True, f"{que.summary} added successfully")
                        )
        if toc:
            TableOfContent.objects.bulk_create(toc)
        return messages


class TableOfContent(models.Model):
    toc_types = (
        (1, "Topic"),
        (2, "Graded Quiz"),
        (3, "Exercise"),
        (4, "Poll")
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               related_name='content')
    time = models.CharField(max_length=100, default=0)
    content = models.IntegerField(choices=toc_types)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    objects = TOCManager()

    def get_toc_text(self):
        if self.content == 1:
            content_name = self.content_object.name
        else:
            content_name = self.content_object.summary
        return content_name

    def get_toc_as_yaml(self, file_path):
        data = {'content_type': self.content, 'time': self.time}
        if self.topics.exists():
            content = self.topics.first()
            data.update(
                {
                    'name': content.name,
                    'description': content.description,
                }
            )
        elif self.questions.exists():
            content = self.questions.first()
            tc_data = []
            for tc in content.get_test_cases():
                _tc_as_dict = model_to_dict(
                    tc, exclude=['id', 'testcase_ptr', 'question'],
                )
                tc_data.append(_tc_as_dict)
            data.update(
                {
                    'summary': content.summary,
                    'type': content.type,
                    'language': content.language,
                    'description': content.description,
                    'points': content.points,
                    'testcase': tc_data,
                }
            )
        yaml_block = dict_to_yaml(data)
        with open(file_path, "a") as yaml_file:
            yaml_file.write(yaml_block)
            return yaml_file

    def __str__(self):
        return f"TOC for {self.lesson.name} as {self.get_content_display()}"


class Topic(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    content = GenericRelation(TableOfContent, related_query_name='topics')

    def __str__(self):
        return f"{self.name}"


class Question(models.Model):
    """Question for a quiz."""

    # A one-line summary of the question.
    summary = models.CharField(max_length=256)

    # The question text, should be valid HTML.
    description = models.TextField()

    # Number of points for the question.
    points = models.FloatField(default=1.0)

    # The language for question.
    language = models.CharField(max_length=24,
                                choices=languages)

    topic = models.CharField(max_length=50, blank=True, null=True)

    # The type of question.
    type = models.CharField(max_length=24, choices=question_types)

    # Is this question active or not. If it is inactive it will not be used
    # when creating a QuestionPaper.
    active = models.BooleanField(default=True)

    # Tags for the Question.
    tags = TaggableManager(blank=True, related_name="labels")

    # Snippet of code provided to the user.
    snippet = models.TextField(blank=True)

    # user for particular question
    user = models.ForeignKey(User, related_name="moderator",
                             on_delete=models.CASCADE)

    # Does this question allow partial grading
    partial_grading = models.BooleanField(default=False)

    # Check assignment upload based question
    grade_assignment_upload = models.BooleanField(default=False)

    min_time = models.IntegerField("time in minutes", default=0)

    # Solution for the question.
    solution = models.TextField(blank=True)

    content = GenericRelation(
        "TableOfContent", related_query_name='questions'
    )

    tc_code_types = {
        "python": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "c": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "cpp": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "java": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "r": [
            ("standardtestcase", "Standard TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "bash": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "scilab": [
            ("standardtestcase", "Standard TestCase"),
            ("hooktestcase", "Hook TestCase")
        ]
    }

    def consolidate_answer_data(self, user_answer, user=None, regrade=False):
        question_data = {}
        metadata = {}
        test_case_data = []
        test_cases = self.get_test_cases()

        for test in test_cases:
            test_case_as_dict = test.get_field_value()
            test_case_data.append(test_case_as_dict)

        question_data['test_case_data'] = test_case_data
        metadata['user_answer'] = user_answer
        metadata['language'] = self.language
        metadata['partial_grading'] = self.partial_grading
        files = FileUpload.objects.filter(question=self)
        if files:
            if settings.USE_AWS:
                metadata['file_paths'] = [
                    (file.file.url, file.extract)
                     for file in files
                ]
            else:
                metadata['file_paths'] = [
                    (self.get_file_url(file.file.url), file.extract)
                     for file in files
                ]
        if self.type == "upload" and regrade:
            file = AssignmentUpload.objects.only(
                "assignmentFile").filter(
                assignmentQuestion_id=self.id, answer_paper__user_id=user.id
                ).order_by("-id").first()
            if file:
                if settings.USE_AWS:
                    metadata['assign_files'] = [file.assignmentFile.url]
                else:
                    metadata['assign_files'] = [
                        self.get_file_url(file.assignmentFile.url)
                    ]
        question_data['metadata'] = metadata
        return json.dumps(question_data)

    def get_file_url(self, path):
        return f'{settings.DOMAIN_HOST}{path}'

    def dump_questions(self, question_ids, user):
        questions = Question.objects.filter(id__in=question_ids,
                                            user_id=user.id, active=True
                                            )
        questions_dict = []
        zip_file_name = string_io()
        zip_file = zipfile.ZipFile(zip_file_name, "a")
        for question in questions:
            test_case = question.get_test_cases()
            file_names = question._add_and_get_files(zip_file)
            q_dict = model_to_dict(question, exclude=['id', 'user'])
            testcases = []
            for case in test_case:
                testcases.append(case.get_field_value())
            q_dict['testcase'] = testcases
            q_dict['files'] = file_names
            q_dict['tags'] = [tag.name for tag in q_dict['tags']]
            questions_dict.append(q_dict)
        question._add_yaml_to_zip(zip_file, questions_dict)
        return zip_file_name

    def load_questions(self, questions_list, user, file_path=None,
                       files_list=None):
        try:
            questions = ruamel.yaml.safe_load_all(questions_list)
            msg = "Questions Uploaded Successfully"
            for question in questions:
                question['user'] = user
                file_names = question.pop('files') \
                    if 'files' in question else None
                tags = question.pop('tags') if 'tags' in question else None
                test_cases = question.pop('testcase')
                que, result = Question.objects.get_or_create(**question)
                if file_names and file_path:
                    que._add_files_to_db(file_names, file_path)
                if tags:
                    que.tags.add(*tags)
                for test_case in test_cases:
                    try:
                        test_case_type = test_case.pop('test_case_type')
                        model_class = get_model_class(test_case_type)
                        new_test_case, obj_create_status = \
                            model_class.objects.get_or_create(
                                question=que, **test_case
                            )
                        new_test_case.type = test_case_type
                        new_test_case.save()

                    except Exception:
                        msg = "Unable to parse test case data"
        except Exception as exc_msg:
            msg = "Error Parsing Yaml: {0}".format(exc_msg)
        return msg

    def get_test_cases(self, **kwargs):
        tc_list = []
        for tc in self.testcase_set.values_list("type", flat=True).distinct():
            test_case_ctype = ContentType.objects.get(app_label="yaksh",
                                                      model=tc)
            test_case = test_case_ctype.get_all_objects_for_this_type(
                question=self,
                **kwargs
            )
            tc_list.extend(test_case)
        return tc_list

    def get_test_cases_as_dict(self, **kwargs):
        tc_list = []
        for tc in self.testcase_set.values_list("type", flat=True).distinct():
            test_case_ctype = ContentType.objects.get(app_label="yaksh",
                                                      model=tc)
            test_case = test_case_ctype.get_all_objects_for_this_type(
                question=self,
                **kwargs
            )
            for tc in test_case:
                tc_list.append(model_to_dict(tc))
            return tc_list

    def get_test_case(self, **kwargs):
        for tc in self.testcase_set.all():
            test_case_type = tc.type
            test_case_ctype = ContentType.objects.get(
                app_label="yaksh",
                model=test_case_type
            )
            test_case = test_case_ctype.get_object_for_this_type(
                question=self,
                **kwargs
            )

        return test_case


    def get_maximum_test_case_weight(self, **kwargs):
        max_weight = 0.0
        for test_case in self.get_test_cases():
            max_weight += test_case.weight

        return max_weight

    def _add_and_get_files(self, zip_file):
        files = FileUpload.objects.filter(question=self)
        files_list = []
        for f in files:
            zip_file.writestr(
                os.path.join("additional_files", os.path.basename(f.file.name)),
                f.file.read()
            )
            files_list.append(((os.path.basename(f.file.name)), f.extract))
        return files_list

    def _add_files_to_db(self, file_names, path):
        for file_name, extract in file_names:
            q_file = glob.glob(os.path.join(path, "**", file_name))[0]
            if os.path.exists(q_file):
                que_file = open(q_file, 'rb')
                # Converting to Python file object with
                # some Django-specific additions
                django_file = File(que_file)
                file_upload = FileUpload()
                file_upload.question = self
                file_upload.extract = extract
                file_upload.file.save(file_name, django_file, save=True)

    def _add_yaml_to_zip(self, zip_file, q_dict, path_to_file=None):
        tmp_file_path = tempfile.mkdtemp()
        yaml_path = os.path.join(tmp_file_path, "questions_dump.yaml")
        for elem in q_dict:
            relevant_dict = CommentedMap()
            relevant_dict['summary'] = elem.pop('summary')
            relevant_dict['type'] = elem.pop('type')
            relevant_dict['language'] = elem.pop('language')
            relevant_dict['description'] = elem.pop('description')
            relevant_dict['points'] = elem.pop('points')
            relevant_dict['testcase'] = elem.pop('testcase')
            relevant_dict.update(CommentedMap(sorted(elem.items(),
                                                     key=lambda x: x[0]
                                                     ))
                                 )

            yaml_block = dict_to_yaml(relevant_dict)
            with open(yaml_path, "a") as yaml_file:
                yaml_file.write(yaml_block)
        zip_file.write(yaml_path, os.path.basename(yaml_path))
        zip_file.close()
        shutil.rmtree(tmp_file_path)

    def read_yaml(self, file_path, user, files=None):
        msg = "Failed to upload Questions"
        for ext in ["yaml", "yml"]:
            for yaml_file in glob.glob(os.path.join(file_path,
                                                    "*.{0}".format(ext)
                                                    )):
                if os.path.exists(yaml_file):
                    with open(yaml_file, 'r') as q_file:
                        questions_list = q_file.read()
                        msg = self.load_questions(questions_list, user,
                                                  file_path, files
                                                  )

        if files:
            delete_files(files, file_path)
        return msg

    def create_demo_questions(self, user):
        zip_file_path = os.path.join(
            FIXTURES_DIR_PATH, 'demo_questions.zip'
        )
        files, extract_path = extract_files(zip_file_path)
        self.read_yaml(extract_path, user, files)

    def get_test_case_options(self):
        options = None
        if self.type == "code":
            options = self.tc_code_types.get(self.language)
        elif self.type == "mcq" or self.type == "mcc":
            options = [("mcqtestcase", "Mcq TestCase")]
        elif self.type == "integer":
            options = [("integertestcase", "Integer TestCase")]
        elif self.type == "float":
            options = [("floattestcase", "Float TestCase")]
        elif self.type == "string":
            options = [("stringtestcase", "String TestCase")]
        elif self.type == "arrange":
            options = [("arrangetestcase", "Arrange TestCase")]
        elif self.type == "upload":
            options = [("hooktestcase", "Hook TestCase")]
        return options

    def __str__(self):
        return self.summary


class TestCase(models.Model):
    question = models.ForeignKey(Question, blank=True, null=True,
                                 on_delete=models.CASCADE,
                                 related_name="test_cases")
    type = models.CharField(max_length=24, choices=test_case_types, null=True)


class StandardTestCase(TestCase):
    test_case = models.TextField()
    weight = models.FloatField(default=1.0)
    test_case_args = models.TextField(blank=True)
    hidden = models.BooleanField(default=False)

    def get_field_value(self):
        return {"test_case_type": "standardtestcase",
                "test_case": self.test_case,
                "weight": self.weight,
                "hidden": self.hidden,
                "test_case_args": self.test_case_args}

    def __str__(self):
        return u'Standard TestCase | Test Case: {0}'.format(self.test_case)


class StdIOBasedTestCase(TestCase):
    expected_input = models.TextField(default=None, blank=True, null=True)
    expected_output = models.TextField(default=None)
    weight = models.IntegerField(default=1.0)
    hidden = models.BooleanField(default=False)

    def get_field_value(self):
        return {"test_case_type": "stdiobasedtestcase",
                "expected_output": self.expected_output,
                "expected_input": self.expected_input,
                "hidden": self.hidden,
                "weight": self.weight}

    def __str__(self):
        return u'StdIO Based Testcase | Exp. Output: {0} | Exp. Input: {1}'.\
            format(
                self.expected_output, self.expected_input
            )


class McqTestCase(TestCase):
    options = models.TextField(default=None)
    correct = models.BooleanField(default=False)

    def get_field_value(self):
        return {"test_case_type": "mcqtestcase",
                "options": self.options, "correct": self.correct}

    def __str__(self):
        return u'MCQ Testcase | Correct: {0}'.format(self.correct)


class HookTestCase(TestCase):
    hook_code = models.TextField(default=dedent(
        """\
        def check_answer(user_answer):
           ''' Evaluates user answer to return -
           success - Boolean, indicating if code was executed correctly
           mark_fraction - Float, indicating fraction of the
                          weight to a test case
           error - String, error message if success is false

           In case of assignment upload there will be no user answer '''

           success = False
           err = "Incorrect Answer" # Please make this more specific
           mark_fraction = 0.0

           # write your code here

           return success, err, mark_fraction

        """)

    )
    weight = models.FloatField(default=1.0)
    hidden = models.BooleanField(default=False)

    def get_field_value(self):
        return {"test_case_type": "hooktestcase", "hook_code": self.hook_code,
                "hidden": self.hidden, "weight": self.weight}

    def __str__(self):
        return u'Hook Testcase | Correct: {0}'.format(self.hook_code)


class IntegerTestCase(TestCase):
    correct_ans = models.IntegerField(default=None)

    def get_field_value(self):
        return {"test_case_type": "integertestcase", "correct": self.correct_ans}

    def __str__(self):
        return u'Integer Testcase | Correct: {0}'.format(self.correct_ans)


class StringTestCase(TestCase):
    correct_ans = models.TextField(default=None)
    string_check = models.CharField(max_length=200, choices=string_check_type)

    def get_field_value(self):
        return {"test_case_type": "stringtestcase", "correct": self.correct_ans,
                "string_check": self.string_check}

    def __str__(self):
        return u'String Testcase | Correct: {0}'.format(self.correct_ans)


class FloatTestCase(TestCase):
    correct_ans = models.FloatField(default=None)
    error_margin = models.FloatField(default=0.0, null=True, blank=True,
                                     help_text="Margin of error")

    def get_field_value(self):
        return {"test_case_type": "floattestcase", "correct": self.correct_ans,
                "error_margin": self.error_margin}

    def __str__(self):
        return u'Testcase | Correct: {0} | Error Margin: +or- {1}'.format(
                self.correct_ans, self.error_margin
                )


class ArrangeTestCase(TestCase):
    options = models.TextField(default=None)

    def get_field_value(self):
        return {"test_case_type": "arrangetestcase",
                "options": self.options}

    def __str__(self):
        return u'Arrange Testcase | Option: {0}'.format(self.options)


class Answer(models.Model):
    """Answers submitted by the users."""

    # The question for which user answers.
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # The answer submitted by the user.
    answer = models.TextField(null=True, blank=True)

    # Error message when auto-checking the answer.
    error = models.TextField()

    # Marks obtained for the answer. This can be changed by the teacher if the
    # grading is manual.
    marks = models.FloatField(default=0.0)

    # Is the answer correct.
    correct = models.BooleanField(default=False)

    # Whether skipped or not.
    skipped = models.BooleanField(default=False)

    comment = models.TextField(null=True, blank=True)

    def set_marks(self, marks):
        if marks > self.question.points:
            self.marks = self.question.points
        else:
            self.marks = marks

    def set_comment(self, comments):
        self.comment = comments

    def __str__(self):
        return "Answer for question {0}".format(self.question.summary)



class LessonQuizAnswer(models.Model):
    toc = models.ForeignKey("TableOfContent", on_delete=models.CASCADE)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="student"
    )
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    def check_answer(self, user_answer):
        result = {'success': False, 'error': ['Incorrect answer'],
                  'weight': 0.0}
        question = self.toc.content_object
        if question.type == 'mcq':
            expected_answer = question.get_test_case(correct=True).id
            if user_answer.strip() == str(expected_answer).strip():
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'mcc':
            expected_answers = [
                str(opt.id) for opt in question.get_test_cases(correct=True)
            ]
            if set(user_answer) == set(expected_answers):
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'integer':
            expected_answers = [
                int(tc.correct) for tc in question.get_test_cases()
            ]
            if int(user_answer) in expected_answers:
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'string':
            tc_status = []
            for tc in question.get_test_cases():
                if tc.string_check == "lower":
                    if tc.correct.lower().splitlines()\
                       == user_answer.lower().splitlines():
                        tc_status.append(True)
                else:
                    if tc.correct.splitlines()\
                       == user_answer.splitlines():
                        tc_status.append(True)
            if any(tc_status):
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'float':
            user_answer = float(user_answer)
            tc_status = []
            for tc in question.get_test_cases():
                if abs(tc.correct - user_answer) <= tc.error_margin:
                    tc_status.append(True)
            if any(tc_status):
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'arrange':
            testcase_ids = sorted(
                              [tc.id for tc in question.get_test_cases()]
                              )
            if user_answer == testcase_ids:
                result['success'] = True
                result['error'] = ['Correct answer']
        self.answer.error = result
        ans_status = result.get("success")
        self.answer.correct = ans_status
        if ans_status:
            self.answer.marks = self.answer.question.points
        self.answer.save()
        return result

    def __str__(self):
        return f"Lesson answer of {self.toc} by {self.student.get_full_name()}"
