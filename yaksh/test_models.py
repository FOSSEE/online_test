import unittest
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from yaksh.models import User, Profile, Question, Quiz, QuestionPaper,\
    QuestionSet, AnswerPaper, Answer, Course, StandardTestCase,\
    StdIOBasedTestCase, FileUpload, McqTestCase, AssignmentUpload,\
    LearningModule, LearningUnit, Lesson, LessonFile, CourseStatus, \
    create_group, legend_display_types, Post, Comment, MicroManager, QRcode, \
    QRcodeHandler
from yaksh.code_server import (
    ServerPool, get_result as get_result_from_code_server
    )
import json
import ruamel.yaml as yaml
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
from django.db import IntegrityError
from django.conf import settings as dj_settings
from django.core.files import File
from textwrap import dedent
import zipfile
import os
import shutil
import tempfile
import hashlib
from threading import Thread
from collections import defaultdict
from yaksh import settings


def setUpModule():
    Group.objects.get_or_create(name='moderator')

    # create user profile
    user = User.objects.create_user(username='creator',
                                    password='demo',
                                    email='demo@test.com')
    User.objects.create_user(username='demo_user2',
                             password='demo',
                             email='demo@test.com')
    Profile.objects.create(user=user, roll_number=1, institute='IIT',
                           department='Chemical', position='Student')
    student = User.objects.create_user(username='demo_user3',
                                       password='demo',
                                       email='demo3@test.com')
    Profile.objects.create(user=student, roll_number=3, institute='IIT',
                           department='Chemical', position='Student')

    user4 = User.objects.create_user(
        username='demo_user4', password='demo', email='demo4@test.com'
    )
    Profile.objects.create(user=user4, roll_number=4, institute='IIT',
                           department='Chemical', position='Student')

    # create a course
    course = Course.objects.create(name="Python Course",
                                   enrollment="Enroll Request", creator=user)

    # create 20 questions
    for i in range(1, 21):
        Question.objects.create(summary='Q%d' % (i), points=1,
                                type='code', user=user)

    # create a quiz
    quiz = Quiz.objects.create(
        start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
        end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
        duration=30, active=True,
        attempts_allowed=1, time_between_attempts=0,
        description='demo quiz 1', pass_criteria=0,
        instructions="Demo Instructions")

    Quiz.objects.create(start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0,
                                                 tzinfo=pytz.utc),
                        end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                               tzinfo=pytz.utc),
                        duration=30, active=False,
                        attempts_allowed=-1, time_between_attempts=0,
                        description='demo quiz 2', pass_criteria=40,
                        instructions="Demo Instructions")
    tmp_file1 = os.path.join(tempfile.gettempdir(), "test.txt")
    with open(tmp_file1, 'wb') as f:
        f.write('2'.encode('ascii'))

    # Learing module
    learning_module_one = LearningModule.objects.create(
        name='LM1', description='module one', creator=user
        )
    learning_module_two = LearningModule.objects.create(
        name='LM2', description='module two', creator=user, order=1
        )
    lesson = Lesson.objects.create(name='L1', description='Video Lesson',
                                   creator=user)
    learning_unit_lesson = LearningUnit.objects.create(order=1, lesson=lesson,
                                                       type='lesson')
    learning_unit_quiz = LearningUnit.objects.create(order=2, quiz=quiz,
                                                     type='quiz')
    learning_module_one.learning_unit.add(learning_unit_lesson)
    learning_module_one.learning_unit.add(learning_unit_quiz)
    learning_module_one.save()
    course.learning_module.add(learning_module_one)
    course.learning_module.add(learning_module_two)
    course_user = User.objects.create(username='course_user')
    course.students.add(course_user)
    course.save()
    LessonFile.objects.create(lesson=lesson)
    CourseStatus.objects.create(course=course, user=course_user)
    MicroManager.objects.create(manager=user, course=course, quiz=quiz,
                                student=course_user)


def tearDownModule():
    User.objects.all().delete()
    Question.objects.all().delete()
    Quiz.objects.all().delete()
    Course.objects.all().delete()
    QuestionPaper.objects.all().delete()
    LessonFile.objects.all().delete()
    Lesson.objects.all().delete()
    LearningUnit.objects.all().delete()
    LearningModule.objects.all().delete()
    AnswerPaper.objects.all().delete()
    MicroManager.objects.all().delete()
    Group.objects.all().delete()

###############################################################################
class GlobalMethodsTestCases(unittest.TestCase):
    def test_create_group_when_group_exists(self):
        self.assertEqual(
            create_group('moderator', 'yaksh'),
            Group.objects.get(name='moderator')
        )


###############################################################################
class MicroManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.micromanager = MicroManager.objects.first()
        self.course = self.micromanager.course
        quiz = self.micromanager.quiz
        self.questionpaper = QuestionPaper.objects.create(quiz=quiz)
        question = Question.objects.get(summary='Q1')
        self.questionpaper.fixed_questions.add(question)
        self.questionpaper.update_total_marks()
        self.student = User.objects.get(username='course_user')

    def tearDown(self):
        self.questionpaper.delete()

    def test_micromanager(self):
        # Given
        user = User.objects.get(username='creator')
        course = Course.objects.get(name='Python Course', creator=user)
        quiz = Quiz.objects.get(description='demo quiz 1')
        student = User.objects.get(username='course_user')

        # When
        micromanager = MicroManager.objects.first()

        # Then
        self.assertIsNotNone(micromanager)
        self.assertEqual(micromanager.manager, user)
        self.assertEqual(micromanager.student, student)
        self.assertEqual(micromanager.course, course)
        self.assertEqual(micromanager.quiz, quiz)
        self.assertFalse(micromanager.special_attempt)
        self.assertEqual(micromanager.attempts_permitted, 0)
        self.assertEqual(micromanager.attempts_utilised, 0)
        self.assertEqual(micromanager.wait_time, 0)
        self.assertEqual(micromanager.attempt_valid_for, 90)
        self.assertEqual(user.micromanaging.first(), micromanager)
        self.assertEqual(student.micromanaged.first(), micromanager)

    def test_set_wait_time(self):
        # Given
        micromanager = self.micromanager

        # When
        micromanager.set_wait_time(days=2)

        # Then
        self.assertEqual(micromanager.wait_time, 2)

    def self_increment_attempts_permitted(self):
        # Given
        micromanager = self.micromanager

        # When
        micromanager.increment_attempts_permitted()

        # Then
        self.assertEqual(micromanager.attempts_permitted, 1)

    def test_update_permitted_time(self):
        # Given
        micromanager = self.micromanager
        permit_time = timezone.now()

        # When
        micromanager.update_permitted_time(permit_time)

        # Then
        self.assertEqual(micromanager.permitted_time, permit_time)

    def test_has_student_attempts_exhausted(self):
        # Given
        micromanager = self.micromanager

        # Then
        self.assertFalse(micromanager.has_student_attempts_exhausted())

    def test_has_quiz_time_exhausted(self):
        # Given
        micromanager = self.micromanager

        # Then
        self.assertFalse(micromanager.has_quiz_time_exhausted())

    def test_is_special_attempt_required(self):
        # Given
        micromanager = self.micromanager
        attempt = 1
        ip = '127.0.0.1'

        # Then
        self.assertFalse(micromanager.is_special_attempt_required())

        # When
        answerpaper = self.questionpaper.make_answerpaper(self.student, ip,
                                                          attempt,
                                                          self.course.id)
        answerpaper.update_marks(state='completed')

        # Then
        self.assertTrue(micromanager.is_special_attempt_required())

        answerpaper.delete()

    def test_allow_special_attempt(self):
        # Given
        micromanager = self.micromanager

        # When
        micromanager.allow_special_attempt()

        # Then
        self.assertFalse(micromanager.special_attempt)

    def test_has_special_attempt(self):
        # Given
        micromanager = self.micromanager

        # Then
        self.assertFalse(micromanager.has_special_attempt())

    def test_is_attempt_time_valid(self):
        # Given
        micromanager = self.micromanager

        # Then
        self.assertTrue(micromanager.is_attempt_time_valid())

    def test_can_student_attempt(self):
        # Given
        micromanager = self.micromanager

        # Then
        self.assertFalse(micromanager.can_student_attempt())


class LessonTestCases(unittest.TestCase):
    def setUp(self):
        self.lesson = Lesson.objects.get(name='L1')
        self.creator = User.objects.get(username='creator')

    def test_lesson(self):
        self.assertEqual(self.lesson.name, 'L1')
        self.assertEqual(self.lesson.description, 'Video Lesson')
        self.assertEqual(self.lesson.creator.username, self.creator.username)


class LearningModuleTestCases(unittest.TestCase):
    def setUp(self):
        self.learning_module = LearningModule.objects.get(name='LM1')
        self.learning_module_two = LearningModule.objects.get(name='LM2')
        self.creator = User.objects.get(username='creator')
        self.student = User.objects.get(username='course_user')
        learning_units = self.learning_module.learning_unit.order_by("order")
        self.learning_unit_one = learning_units[0]
        self.learning_unit_two = learning_units[1]
        self.quiz = Quiz.objects.get(description='demo quiz 1')
        self.lesson = Lesson.objects.get(name='L1')
        self.course = Course.objects.get(name='Python Course')
        self.course_status = CourseStatus.objects.get(
            course=self.course, user=self.student)

        self.prereq_course = Course.objects.create(
            name="Prerequisite Course",
            enrollment="Enroll Request", creator=self.creator
        )

        self.prereq_learning_module = LearningModule.objects.create(
            name='LM3', description='module one', creator=self.creator
        )
        self.test_learning_module = LearningModule.objects.create(
            name='LM4', description='module two',
            creator=self.creator, order=1
        )
        course_status = CourseStatus.objects.create(
            course=self.prereq_course, user=self.student
        )
        lesson = Lesson.objects.create(
            name='P1', description='Video Lesson',
            creator=self.creator
        )
        learning_unit_lesson = LearningUnit.objects.create(
            order=2,
            lesson=lesson,
            type='lesson'
        )
        learning_unit_quiz = LearningUnit.objects.create(
            order=1,
            quiz=self.quiz,
            type='quiz'
        )
        self.prereq_learning_module.learning_unit.add(learning_unit_quiz)
        self.prereq_learning_module.learning_unit.add(learning_unit_lesson)
        self.prereq_learning_module.save()
        self.prereq_course.learning_module.add(self.prereq_learning_module)
        self.prereq_course.learning_module.add(self.test_learning_module)
        self.prereq_course.students.add(self.student)
        self.prereq_course.save()

    def tearDown(self):
        # Remove unit from course status completed units
        self.course_status.completed_units.remove(self.learning_unit_one)
        self.course_status.completed_units.remove(self.learning_unit_two)

    def test_learning_module(self):
        self.assertEqual(self.learning_module.description, 'module one')
        self.assertEqual(self.learning_module.creator, self.creator)
        self.assertFalse(self.learning_module.check_prerequisite)
        self.assertEqual(self.learning_module.order, 0)

    def test_prerequisite_passes(self):
        self.assertFalse(
            self.test_learning_module.is_prerequisite_passed(
                self.student, self.prereq_course
            )
        )

    def test_get_quiz_units(self):
        # Given
        quizzes = [self.quiz]
        # When
        module_quizzes = self.learning_module.get_quiz_units()
        # Then
        self.assertSequenceEqual(module_quizzes, quizzes)

    def test_get_learning_units(self):
        # Given
        learning_units = [self.learning_unit_one, self.learning_unit_two]
        # When
        module_units = self.learning_module.get_learning_units()
        # Then
        self.assertSequenceEqual(module_units, learning_units)

    def test_get_added_quiz_lesson(self):
        # Given
        quiz_lessons = [('lesson', self.lesson), ('quiz', self.quiz)]
        # When
        module_quiz_lesson = self.learning_module.get_added_quiz_lesson()
        # Then
        self.assertEqual(module_quiz_lesson, quiz_lessons)

    def test_toggle_check_prerequisite(self):
        self.assertFalse(self.learning_module.check_prerequisite)
        # When
        self.learning_module.toggle_check_prerequisite()
        # Then
        self.assertTrue(self.learning_module.check_prerequisite)

        # When
        self.learning_module.toggle_check_prerequisite()
        # Then
        self.assertFalse(self.learning_module.check_prerequisite)

    def test_get_next_unit(self):
        # Given
        current_unit_id = self.learning_unit_one.id
        next_unit = self.learning_unit_two
        # When
        unit = self.learning_module.get_next_unit(current_unit_id)
        # Then
        self.assertEqual(unit, next_unit)

        # Given
        current_unit_id = self.learning_unit_two.id
        next_unit = self.learning_unit_one
        # When
        unit = self.learning_module.get_next_unit(current_unit_id)
        # Then
        self.assertEqual(unit, next_unit)

    def test_get_module_status(self):
        # Given
        module_status = 'not attempted'
        # When
        self.learning_module.learning_unit.remove(self.learning_unit_two)
        status = self.learning_module.get_status(self.student, self.course)
        # Then
        self.assertEqual(status, module_status)
        self.learning_module.learning_unit.add(self.learning_unit_two)
        # Module in progress

        # Given
        self.course_status.completed_units.add(self.learning_unit_one)
        # When
        status = self.learning_module.get_status(self.student, self.course)
        # Then
        self.assertEqual("inprogress", status)

        # Module is completed

        # Given
        self.course_status.completed_units.add(self.learning_unit_two)
        # When
        status = self.learning_module.get_status(self.student, self.course)
        # Then
        self.assertEqual("completed", status)

        # Module with no units
        self.course.learning_module.add(self.learning_module_two)
        status = self.learning_module_two.get_status(self.student, self.course)
        self.assertEqual("no units", status)

    def test_module_completion_percent(self):
        # for module without learning units
        percent = self.learning_module_two.get_module_complete_percent(
            self.course, self.student
        )
        self.assertEqual(percent, 0)

        # for module with learning units
        self.course_status.completed_units.add(self.learning_unit_one)
        self.course_status.completed_units.add(self.learning_unit_two)
        percent = self.learning_module.get_module_complete_percent(
            self.course, self.student
        )
        self.assertEqual(percent, 100)


class LearningUnitTestCases(unittest.TestCase):
    def setUp(self):
        learning_module = LearningModule.objects.get(name='LM1')
        self.learning_unit_one = learning_module.learning_unit.get(order=1)
        self.learning_unit_two = learning_module.learning_unit.get(order=2)
        self.lesson = Lesson.objects.get(name='L1')
        self.quiz = Quiz.objects.get(description='demo quiz 1')

    def test_learning_unit(self):
        self.assertEqual(self.learning_unit_one.type, 'lesson')
        self.assertEqual(self.learning_unit_two.type, 'quiz')
        self.assertEqual(
            self.learning_unit_one.get_lesson_or_quiz(), self.lesson
        )
        self.assertEqual(
            self.learning_unit_two.get_lesson_or_quiz(), self.quiz
        )
        self.assertIsNone(self.learning_unit_one.quiz)
        self.assertIsNone(self.learning_unit_two.lesson)
        self.assertFalse(self.learning_unit_one.check_prerequisite)
        self.assertFalse(self.learning_unit_two.check_prerequisite)


class ProfileTestCases(unittest.TestCase):
    def setUp(self):
        self.creator = User.objects.get(username='creator')
        self.profile = Profile.objects.get(user=self.creator)
        self.teacher = User.objects.create_user(
                                            username='teacher_profile',
                                            password='teacher_profile',
                                            email='teacher_profile@test.com')
        Profile.objects.create(
            user=self.teacher, roll_number=123, institute='IIT',
            is_moderator=True, department='Chemical', position='Teacher'
        )
        self.course = Course.objects.create(
            name="Course For ProfileTestCase",
            enrollment="Open Course",
            creator=self.creator,
            start_enroll_time=datetime(
                2015, 10, 9, 10, 8, 15, 0,
                tzinfo=pytz.utc
            ),
            end_enroll_time=datetime(
                2015, 11, 9, 10, 8, 15, 0,
                tzinfo=pytz.utc
            ),
        )
        self.course.add_teachers(self.teacher)

    def test_user_profile(self):
        """ Test user profile"""
        self.assertEqual(self.creator.username, 'creator')
        self.assertEqual(self.profile.user.username, 'creator')
        self.assertEqual(int(self.profile.roll_number), 1)
        self.assertEqual(self.profile.institute, 'IIT')
        self.assertEqual(self.profile.department, 'Chemical')
        self.assertEqual(self.profile.position, 'Student')

    def test_profile_is_moderator_removes_teacher(self):
        teacher_profile = self.teacher.profile
        teacher_profile.is_moderator = False
        teacher_profile.save()
        self.assertNotIn(self.teacher, self.course.teachers.all())

    def tearDown(self):
        self.teacher.profile.delete()
        self.teacher.delete()
        self.course.delete()


###############################################################################
class QuestionTestCases(unittest.TestCase):
    def setUp(self):
        # Single question details
        self.user1 = User.objects.get(username="creator")
        self.user2 = User.objects.get(username="demo_user2")
        self.question1 = Question.objects.create(
            summary='Demo Python 1', language='Python', type='Code',
            active=True, description='Write a function', points=1.0,
            snippet='def myfunc()', user=self.user1
        )

        self.question2 = Question.objects.create(
            summary='Yaml Json', language='python', type='code',
            active=True, description='factorial of a no', points=2.0,
            snippet='def fact()', user=self.user2
        )

        # create a temp directory and add files for loading questions test
        file_path = os.path.join(tempfile.gettempdir(), "test.txt")
        self.load_tmp_path = tempfile.mkdtemp()
        shutil.copy(file_path, self.load_tmp_path)
        file1 = os.path.join(self.load_tmp_path, "test.txt")

        # create a temp directory and add files for dumping questions test
        self.dump_tmp_path = tempfile.mkdtemp()
        shutil.copy(file_path, self.dump_tmp_path)
        file2 = os.path.join(dj_settings.MEDIA_ROOT, "test.txt")
        with open(file2, "w") as upload_file:
            django_file = File(upload_file)
            FileUpload.objects.create(file=file2,
                                      question=self.question2
                                      )

        self.question1.tags.add('python', 'function')
        self.assertion_testcase = StandardTestCase(
            question=self.question1,
            test_case='assert myfunc(12, 13) == 15',
            type='standardtestcase'
        )
        self.upload_test_case = StandardTestCase(
            question=self.question2,
            test_case='assert fact(3) == 6',
            type='standardtestcase'
        )
        self.upload_test_case.save()
        self.user_answer = "demo_answer"
        self.test_case_upload_data = [{"test_case": "assert fact(3)==6",
                                       "test_case_type": "standardtestcase",
                                       "test_case_args": "",
                                       "weight": 1.0,
                                       "hidden": False
                                       }]
        questions_data = [{"snippet": "def fact()", "active": True,
                           "points": 1.0,
                           "description": "factorial of a no",
                           "language": "Python", "type": "Code",
                           "testcase": self.test_case_upload_data,
                           "files": [[file1, 0]],
                           "summary": "Yaml Demo",
                           "tags": ['yaml_demo']
                           }]
        questions_data_with_missing_fields = [{
            "active": True, "points": 1.0, "description": "factorial of a no",
            "language": "Python", "type": "Code",
            "testcase": self.test_case_upload_data,
            "summary": "Yaml Demo 2"
            }]
        self.yaml_questions_data = yaml.safe_dump_all(questions_data)
        self.yaml_questions_data_with_missing_fields = yaml.safe_dump_all(
                questions_data_with_missing_fields
                )
        self.bad_yaml_question_data = '''[{
            "active": True, "points": 1.0, "description" "factorial of a no",
            "language": "Python", "type": "Code",
            "testcase": self.test_case_upload_data,
            "summary": "bad yaml"
            }]'''

        self.test_case_without_type = [{"test_case": "assert fact(3)==6",
                                        "test_case_args": "",
                                        "weight": 1.0
                                        }]
        self.yaml_question_data_without_test_case_type = yaml.safe_dump_all([{
            "active": True, "points": 1.0, "description": "factorial of a no",
            "language": "Python", "type": "Code",
            "testcase": self.test_case_without_type,
            "summary": "bad yaml"
            }])

    def tearDown(self):
        shutil.rmtree(self.load_tmp_path)
        shutil.rmtree(self.dump_tmp_path)
        uploaded_files = FileUpload.objects.all()
        que_id_list = [file.question.id for file in uploaded_files]
        for que_id in que_id_list:
            dir_path = os.path.join(os.getcwd(), "yaksh", "data",
                                    "question_{0}".format(que_id)
                                    )
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        uploaded_files.delete()

    def test_question(self):
        """ Test question """
        self.assertEqual(self.question1.summary, 'Demo Python 1')
        self.assertEqual(self.question1.language, 'Python')
        self.assertEqual(self.question1.type, 'Code')
        self.assertEqual(self.question1.description, 'Write a function')
        self.assertEqual(self.question1.points, 1.0)
        self.assertTrue(self.question1.active)
        self.assertEqual(self.question1.snippet, 'def myfunc()')
        tag_list = []
        for tag in self.question1.tags.all():
            tag_list.append(tag.name)
        for tag in tag_list:
            self.assertIn(tag, ['python', 'function'])

    def test_dump_questions(self):
        """ Test dump questions into Yaml """
        question = Question()
        question_id = [self.question2.id]
        questions_zip = question.dump_questions(question_id, self.user2)
        que_file = FileUpload.objects.get(question=self.question2.id)
        zip_file = zipfile.ZipFile(questions_zip, "r")
        tmp_path = tempfile.mkdtemp()
        zip_file.extractall(tmp_path)
        test_case = self.question2.get_test_cases()
        with open("{0}/questions_dump.yaml".format(tmp_path), "r") as f:
            questions = yaml.safe_load_all(f.read())
            for q in questions:
                self.assertEqual(self.question2.summary, q['summary'])
                self.assertEqual(self.question2.language, q['language'])
                self.assertEqual(self.question2.type, q['type'])
                self.assertEqual(self.question2.description, q['description'])
                self.assertEqual(self.question2.points, q['points'])
                self.assertTrue(self.question2.active)
                self.assertEqual(self.question2.snippet, q['snippet'])
                self.assertEqual(os.path.basename(que_file.file.path),
                                 q['files'][0][0])
                self.assertEqual([case.get_field_value()
                                  for case in test_case],
                                 q['testcase']
                                 )
        for file in zip_file.namelist():
            os.remove(os.path.join(tmp_path, file))

    def test_load_questions_with_all_fields(self):
        """ Test load questions into database from Yaml """
        question = Question()
        question.load_questions(self.yaml_questions_data, self.user1,
                                self.load_tmp_path
                                )
        question_data = Question.objects.get(summary="Yaml Demo")
        file = FileUpload.objects.get(question=question_data)
        test_case = question_data.get_test_cases()
        self.assertEqual(question_data.summary, 'Yaml Demo')
        self.assertEqual(question_data.language, 'Python')
        self.assertEqual(question_data.type, 'Code')
        self.assertEqual(question_data.description, 'factorial of a no')
        self.assertEqual(question_data.points, 1.0)
        self.assertTrue(question_data.active)
        tags = question_data.tags.all().values_list("name", flat=True)
        self.assertListEqual(list(tags), ['yaml_demo'])
        self.assertEqual(question_data.snippet, 'def fact()')
        self.assertEqual(os.path.basename(file.file.url), "test.txt")
        self.assertEqual([case.get_field_value() for case in test_case],
                         self.test_case_upload_data
                         )

    def test_load_questions_with_missing_fields(self):
        """ Test load questions into database from Yaml with
            missing fields like files, snippet and tags. """
        question = Question()
        question.load_questions(
            self.yaml_questions_data_with_missing_fields,
            self.user1
            )
        question_data = Question.objects.get(summary="Yaml Demo 2")
        file = FileUpload.objects.filter(question=question_data)
        test_case = question_data.get_test_cases()
        self.assertEqual(question_data.summary, 'Yaml Demo 2')
        self.assertEqual(question_data.language, 'Python')
        self.assertEqual(question_data.type, 'Code')
        self.assertEqual(question_data.description, 'factorial of a no')
        self.assertEqual(question_data.points, 1.0)
        self.assertTrue(question_data.active)
        self.assertEqual(question_data.snippet, '')
        self.assertListEqual(list(file), [])
        self.assertEqual([case.get_field_value() for case in test_case],
                         self.test_case_upload_data
                         )
        tags = question_data.tags.all().values_list("name", flat=True)
        self.assertListEqual(list(tags), [])

    def test_load_questions_with_bad_yaml(self):
        """
            Test if yaml file is parsed correctly
        """
        question = Question()
        msg = question.load_questions(
            self.bad_yaml_question_data,
            self.user1
            )
        self.assertIn("Error Parsing Yaml", msg)

        msg = question.load_questions(
            self.yaml_question_data_without_test_case_type,
            self.user1
            )
        self.assertEqual(msg, "Unable to parse test case data")

    def test_get_test_case_options(self):
        """
            Test if test case options are selected based on
            question type and language
        """

        # Given
        question_types = [
            "mcq", "integer", "float", "string", "arrange", "upload"
        ]
        que_list = []
        for i, q_type in enumerate(question_types, 1):
            que_list.append(Question.objects.create(
                summary='Python Question {0}'.format(i), language='python',
                type=q_type, active=True,
                description='{0} Question'.format(q_type),
                points=1.0, user=self.user1
            ))

        # When
        expected_tc_options = [
            ('standardtestcase', 'Standard TestCase'),
            ('stdiobasedtestcase', 'StdIO TestCase'),
            ('hooktestcase', 'Hook TestCase')
        ]
        other_tc_options = [
            ('mcqtestcase', 'Mcq TestCase'),
            ('integertestcase', 'Integer TestCase'),
            ('floattestcase', 'Float TestCase'),
            ('stringtestcase', 'String TestCase'),
            ('arrangetestcase', 'Arrange TestCase'),
            ('hooktestcase', 'Hook TestCase')
        ]

        # Then
        obtained_tc_options = self.question2.get_test_case_options()
        self.assertEqual(expected_tc_options, obtained_tc_options)
        for que, tc_option in zip(que_list, other_tc_options):
            self.assertEqual(que.get_test_case_options()[0], tc_option)


###############################################################################
class QuizTestCases(unittest.TestCase):
    def setUp(self):
        self.course = Course.objects.get(name="Python Course")
        self.creator = User.objects.get(username="creator")
        self.teacher = User.objects.get(username="demo_user2")
        self.student1 = User.objects.get(username='demo_user3')
        self.student2 = User.objects.get(username='demo_user4')
        self.quiz1 = Quiz.objects.get(description='demo quiz 1')
        self.quiz2 = Quiz.objects.get(description='demo quiz 2')
        self.quiz3 = Quiz.objects.create(
            start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                     tzinfo=pytz.utc),
            end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            duration=30, active=True,
            attempts_allowed=1, time_between_attempts=0,
            description='demo quiz 3', pass_criteria=0,
            instructions="Demo Instructions"
        )
        self.question_paper3 = QuestionPaper.objects.create(quiz=self.quiz3)
        self.quiz4 = Quiz.objects.create(
            start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                     tzinfo=pytz.utc),
            end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            duration=30, active=True,
            attempts_allowed=1, time_between_attempts=0,
            description='demo quiz 4', pass_criteria=0,
            instructions="Demo Instructions"
        )
        self.answerpaper1 = AnswerPaper.objects.create(
            user=self.student1,
            question_paper=self.question_paper3,
            course=self.course,
            attempt_number=1,
            start_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            end_time=datetime(2015, 10, 9, 10, 28, 15, 0, tzinfo=pytz.utc),
            passed=True
        )
        self.answerpaper2 = AnswerPaper.objects.create(
            user=self.student2,
            question_paper=self.question_paper3,
            course=self.course,
            attempt_number=1,
            start_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            end_time=datetime(2015, 10, 9, 10, 28, 15, 0, tzinfo=pytz.utc),
            passed=False
        )
        self.trial_course = Course.objects.create_trial_course(self.creator)

    def tearDown(self):
        self.answerpaper1.delete()
        self.answerpaper2.delete()
        self.trial_course.delete()
        self.quiz3.delete()
        self.quiz4.delete()
        self.question_paper3.delete()

    def test_get_total_students(self):
        self.assertEqual(self.quiz3.get_total_students(self.course), 2)

    def test_get_total_students_without_questionpaper(self):
        self.assertEqual(self.quiz4.get_total_students(self.course), 0)

    def test_get_passed_students(self):
        self.assertEqual(self.quiz3.get_passed_students(self.course), 1)

    def test_get_passed_students_without_questionpaper(self):
        self.assertEqual(self.quiz4.get_passed_students(self.course), 0)

    def test_get_failed_students(self):
        self.assertEqual(self.quiz3.get_failed_students(self.course), 1)

    def test_get_failed_students_without_questionpaper(self):
        self.assertEqual(self.quiz4.get_failed_students(self.course), 0)

    def test_quiz(self):
        """ Test Quiz"""
        self.assertEqual((self.quiz1.start_date_time).strftime('%Y-%m-%d'),
                         '2015-10-09')
        self.assertEqual((self.quiz1.start_date_time).strftime('%H:%M:%S'),
                         '10:08:15')
        self.assertEqual(self.quiz1.duration, 30)
        self.assertTrue(self.quiz1.active)
        self.assertEqual(self.quiz1.description, 'demo quiz 1')
        self.assertEqual(self.quiz1.pass_criteria, 0)
        self.assertEqual(self.quiz1.instructions, "Demo Instructions")

    def test_is_expired(self):
        self.assertFalse(self.quiz1.is_expired())
        self.assertTrue(self.quiz2.is_expired())

    def test_get_active_quizzes(self):
        quizzes = Quiz.objects.get_active_quizzes()
        for quiz in quizzes:
            self.assertTrue(quiz.active)

    def test_create_trial_quiz(self):
        """Test to check if trial quiz is created"""
        trial_quiz = Quiz.objects.create_trial_quiz(self.creator)
        self.assertEqual(trial_quiz.duration, 1000)
        self.assertEqual(trial_quiz.description, "trial_questions")
        self.assertTrue(trial_quiz.is_trial)
        self.assertEqual(trial_quiz.time_between_attempts, 0)

    def test_create_trial_from_quiz_godmode(self):
        """Test to check if a copy of original quiz is created in godmode"""
        trial_quiz = Quiz.objects.create_trial_from_quiz(self.quiz1.id,
                                                         self.creator,
                                                         True, self.course.id
                                                         )[0]
        self.assertEqual(trial_quiz.description,
                         "Trial_orig_id_{}_godmode".format(self.quiz1.id)
                         )
        self.assertTrue(trial_quiz.is_trial)
        self.assertEqual(trial_quiz.duration, 1000)
        self.assertTrue(trial_quiz.active)
        self.assertEqual(trial_quiz.end_date_time,
                         datetime(2199, 1, 1, 0, 0, 0, 0, tzinfo=pytz.utc)
                         )
        self.assertEqual(trial_quiz.time_between_attempts, 0)

    def test_create_trial_from_quiz_usermode(self):
        """Test to check if a copy of original quiz is created in usermode"""
        trial_quiz = Quiz.objects.create_trial_from_quiz(self.quiz2.id,
                                                         self.creator,
                                                         False, self.course.id
                                                         )[0]
        self.assertEqual(trial_quiz.description,
                         "Trial_orig_id_{}_usermode".format(self.quiz2.id))
        self.assertTrue(trial_quiz.is_trial)
        self.assertEqual(trial_quiz.duration, self.quiz2.duration)
        self.assertEqual(trial_quiz.active, self.quiz2.active)
        self.assertEqual(trial_quiz.start_date_time,
                         self.quiz2.start_date_time
                         )
        self.assertEqual(trial_quiz.end_date_time,
                         self.quiz2.end_date_time
                         )
        self.assertEqual(trial_quiz.time_between_attempts, 0)

    def test_view_answerpaper(self):
        self.assertFalse(self.quiz1.view_answerpaper)
        self.assertFalse(self.quiz2.view_answerpaper)

        # When
        self.quiz1.view_answerpaper = True
        self.quiz1.save()

        # Then
        self.assertTrue(self.quiz1.view_answerpaper)


###############################################################################
class QuestionPaperTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.course = Course.objects.get(name="Python Course")
        self.user = User.objects.get(username='creator')
        # All active questions
        self.questions = Question.objects.filter(active=True, user=self.user)
        self.quiz = Quiz.objects.get(description="demo quiz 1")
        self.quiz_with_time_between_attempts = Quiz.objects.create(
            description="demo quiz with time between attempts",
            start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                     tzinfo=pytz.utc),
            end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            duration=30, active=True,
            attempts_allowed=3, time_between_attempts=1.0,
            pass_criteria=0,
            instructions="Demo Instructions"
        )

        # create question paper with only fixed questions
        self.question_paper_fixed_questions = QuestionPaper.objects.create(
                quiz=self.quiz)
        self.question_paper_fixed_questions.fixed_questions.add(
                self.questions.get(summary='Q11'),
                self.questions.get(summary='Q10')
                )

        # create question paper with only random questions
        self.question_paper_random_questions = QuestionPaper.objects.create(
                quiz=self.quiz)
        self.question_set_random = QuestionSet.objects.create(
            marks=2, num_questions=2
            )
        self.question_set_random.questions.add(
            self.questions.get(summary='Q13'),
            self.questions.get(summary='Q5'), self.questions.get(summary='Q7')
            )
        self.question_paper_random_questions.random_questions.add(
                self.question_set_random)

        # create question paper with no questions
        self.question_paper_no_questions = QuestionPaper.objects.create(
                quiz=self.quiz)

        # create question paper
        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=0.0, shuffle_questions=True
        )

        self.question_paper_with_time_between_attempts = \
            QuestionPaper.objects.create(
                quiz=self.quiz_with_time_between_attempts,
                total_marks=0.0,
                shuffle_questions=True
            )
        self.question_paper_with_time_between_attempts.fixed_question_order = \
            "{0}, {1}".format(self.questions[3].id, self.questions[5].id)
        self.question_paper_with_time_between_attempts.fixed_questions.add(
            self.questions[3], self.questions[5]
            )
        self.question_paper.fixed_question_order = "{0}, {1}".format(
                self.questions[3].id, self.questions[5].id
                )
        # add fixed set of questions to the question paper
        self.question_paper.fixed_questions.add(
            self.questions[3], self.questions[5]
            )
        # create two QuestionSet for random questions
        # QuestionSet 1
        self.question_set_1 = QuestionSet.objects.create(
            marks=1, num_questions=2
        )

        # add pool of questions for random sampling
        self.question_set_1.questions.add(
            self.questions[6], self.questions[7],
            self.questions[8], self.questions[9]
        )
        # add question set 1 to random questions in Question Paper
        self.question_paper.random_questions.add(self.question_set_1)

        # QuestionSet 2
        self.question_set_2 = QuestionSet.objects.create(
            marks=1, num_questions=3
        )

        # add pool of questions
        self.question_set_2.questions.add(
            self.questions[11], self.questions[12],
            self.questions[13], self.questions[14]
        )
        # add question set 2
        self.question_paper.random_questions.add(self.question_set_2)

        # ip address for AnswerPaper
        self.ip = '127.0.0.1'

        self.user = User.objects.get(username="creator")

        self.attempted_papers = AnswerPaper.objects.filter(
            question_paper=self.question_paper,
            user=self.user
        )

        # For Trial case
        self.questions_list = [self.questions[3].id, self.questions[5].id]
        self.trial_course = Course.objects.create_trial_course(self.user)
        self.trial_quiz = Quiz.objects.create_trial_quiz(self.user)

    @classmethod
    def tearDownClass(self):
        self.quiz.questionpaper_set.all().delete()

    def test_get_question_bank(self):
        # Given
        summaries = ['Q11', 'Q10']
        questions = list(Question.objects.filter(summary__in=summaries))
        # When
        question_bank = self.question_paper_fixed_questions.get_question_bank()
        # Then
        self.assertSequenceEqual(questions, question_bank)

        # Given
        summaries = ['Q13', 'Q5', 'Q7']
        questions = list(Question.objects.filter(summary__in=summaries))
        # When
        question_bank = \
            self.question_paper_random_questions.get_question_bank()
        # Then
        self.assertSequenceEqual(questions, question_bank)

        # Given
        questions = []
        # When
        question_bank = self.question_paper_no_questions.get_question_bank()
        # Then
        self.assertSequenceEqual(questions, question_bank)

    def test_questionpaper(self):
        """ Test question paper"""
        self.assertEqual(self.question_paper.quiz.description, 'demo quiz 1')
        self.assertSequenceEqual(self.question_paper.fixed_questions.all(),
                                 [self.questions[3], self.questions[5]]
                                 )
        self.assertTrue(self.question_paper.shuffle_questions)

    def test_update_total_marks(self):
        """ Test update_total_marks() method of Question Paper"""
        self.assertEqual(self.question_paper.total_marks, 0)
        self.question_paper.update_total_marks()
        self.assertEqual(self.question_paper.total_marks, 7.0)

    def test_get_random_questions(self):
        """ Test get_random_questions() method of Question Paper"""
        random_questions_set_1 = self.question_set_1.get_random_questions()
        random_questions_set_2 = self.question_set_2.get_random_questions()
        total_random_questions = len(random_questions_set_1 +
                                     random_questions_set_2)
        self.assertEqual(total_random_questions, 5)

        # To check whether random questions are from random_question_set
        questions_set_1 = set(self.question_set_1.questions.all())
        random_set_1 = set(random_questions_set_1)
        random_set_2 = set(random_questions_set_2)
        boolean = questions_set_1.intersection(random_set_1) == random_set_1
        self.assertTrue(boolean)
        self.assertEqual(len(random_set_1), 2)
        # To check that the questions are random.
        # If incase not random then check that the order is diferent
        try:
            self.assertFalse(random_set_1 == random_set_2)
        except AssertionError:
            self.assertTrue(random_questions_set_1 != random_questions_set_2)

    def test_make_answerpaper(self):
        """ Test make_answerpaper() method of Question Paper"""
        already_attempted = self.attempted_papers.count()
        attempt_num = already_attempted + 1
        answerpaper = self.question_paper.make_answerpaper(self.user, self.ip,
                                                           attempt_num,
                                                           self.course.id)
        self.assertIsInstance(answerpaper, AnswerPaper)
        paper_questions = answerpaper.questions.all()
        self.assertEqual(len(paper_questions), 7)
        fixed_questions = set(self.question_paper.fixed_questions.all())
        self.assertTrue(fixed_questions.issubset(set(paper_questions)))
        answerpaper.passed = True
        answerpaper.save()
        # test can_attempt_now(self):
        result = (False,
                  u'You cannot attempt demo quiz 1 quiz more than 1 time(s)')
        self.assertEquals(
            self.question_paper.can_attempt_now(self.user, self.course.id),
            result
        )
        # trying to create an answerpaper with same parameters passed.
        answerpaper2 = self.question_paper.make_answerpaper(
            self.user, self.ip, attempt_num, self.course.id
            )
        # check if make_answerpaper returned an object instead of creating one.
        self.assertEqual(answerpaper, answerpaper2)

    def test_time_between_attempt(self):
        """ Test make_answerpaper() method of Question Paper"""
        attempt_num = 1

        self.first_start_time = timezone.now()
        self.first_end_time = self.first_start_time + timedelta(minutes=20)
        self.second_start_time = self.first_start_time + timedelta(minutes=30)
        self.second_end_time = self.second_start_time + timedelta(minutes=20)

        # create answerpaper
        self.first_answerpaper = AnswerPaper(
            user=self.user,
            question_paper=self.question_paper_with_time_between_attempts,
            start_time=self.first_start_time,
            end_time=self.first_end_time,
            user_ip=self.ip,
            course=self.course,
            attempt_number=attempt_num
        )
        self.first_answerpaper.passed = True
        self.first_answerpaper.save()

        self.second_answerpaper = AnswerPaper(
            user=self.user,
            question_paper=self.question_paper_with_time_between_attempts,
            start_time=self.second_start_time,
            end_time=self.second_end_time,
            user_ip=self.ip,
            course=self.course,
            attempt_number=attempt_num + 1
        )
        self.second_answerpaper.passed = True
        self.second_answerpaper.save()
        msg = u'You cannot start the next attempt ' +\
            'for this quiz before1.0 hour(s)'
        result = (False, msg)
        self.assertEquals(
            self.question_paper_with_time_between_attempts.can_attempt_now(
                self.user, self.course.id), result
        )

    def test_create_trial_paper_to_test_quiz(self):
        qu_list = [str(self.questions_list[0]), str(self.questions_list[1])]
        trial_paper = \
            QuestionPaper.objects.create_trial_paper_to_test_quiz(
                self.trial_quiz, self.quiz_with_time_between_attempts.id
                )
        trial_paper.random_questions.add(self.question_set_1)
        trial_paper.random_questions.add(self.question_set_2)
        trial_paper.fixed_question_order = ",".join(qu_list)
        self.assertEqual(trial_paper.quiz, self.trial_quiz)
        self.assertSequenceEqual(
            trial_paper.get_ordered_questions(),
            self.question_paper.get_ordered_questions()
            )
        trial_paper_ran = [q_set.id for q_set in
                           trial_paper.random_questions.all()]
        qp_ran = [q_set.id for q_set in
                  self.question_paper.random_questions.all()]

        self.assertSequenceEqual(trial_paper_ran, qp_ran)

    def test_create_trial_paper_to_test_questions(self):
        qu_list = [str(self.questions_list[0]), str(self.questions_list[1])]
        trial_paper = \
            QuestionPaper.objects.create_trial_paper_to_test_questions(
                self.trial_quiz, qu_list
            )
        self.assertEqual(trial_paper.quiz, self.trial_quiz)
        fixed_q = self.question_paper.fixed_questions.values_list(
            'id', flat=True)
        self.assertSequenceEqual(self.questions_list, fixed_q)

    def test_fixed_order_questions(self):
        fixed_ques = self.question_paper.get_ordered_questions()
        actual_ques = [self.questions[3], self.questions[5]]
        self.assertSequenceEqual(fixed_ques, actual_ques)


###############################################################################
class AnswerPaperTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.course = Course.objects.get(name="Python Course")
        self.ip = '101.0.0.1'
        self.user = User.objects.get(username='creator')
        self.user2 = User.objects.get(username='demo_user2')
        self.profile = self.user.profile
        self.quiz = Quiz.objects.get(description='demo quiz 1')
        self.question_paper = QuestionPaper(quiz=self.quiz, total_marks=3)
        self.question_paper.save()
        self.quiz2 = Quiz.objects.get(description='demo quiz 2')
        self.qtn_paper_with_single_question = QuestionPaper(
            quiz=self.quiz2, total_marks=3
        )
        self.qtn_paper_with_single_question.save()
        all_questions = Question.objects.filter(user=self.user).order_by("id")
        self.questions = all_questions[0:3]
        self.start_time = timezone.now()
        self.end_time = self.start_time + timedelta(minutes=20)
        self.question1 = all_questions[0]
        self.question2 = all_questions[1]
        self.question3 = all_questions[2]
        self.question4 = all_questions[3]

        # create answerpaper
        self.answerpaper = AnswerPaper(
            user=self.user,
            question_paper=self.question_paper,
            start_time=self.start_time,
            end_time=self.end_time,
            user_ip=self.ip,
            course=self.course
        )
        self.attempted_papers = AnswerPaper.objects.filter(
            question_paper=self.question_paper,
            user=self.user
        )
        self.question_paper.fixed_questions.add(*self.questions)
        already_attempted = self.attempted_papers.count()
        self.answerpaper.attempt_number = already_attempted + 1
        self.answerpaper.save()
        self.answerpaper.questions.add(*self.questions)
        self.answerpaper.questions_order = ",".join(
                            [str(q.id) for q in self.questions]
                            )
        self.answerpaper.questions_unanswered.add(*self.questions)
        self.answerpaper.save()

        # answers for the Answer Paper
        self.answer_right = Answer(
            question=self.question1,
            answer="Demo answer",
            correct=True, marks=1,
            error=json.dumps([])
        )
        self.answer_wrong = Answer(
            question=self.question2,
            answer="My answer",
            correct=False,
            marks=0,
            error=json.dumps(['error1', 'error2'])
        )
        self.answer_right.save()
        self.answer_wrong.save()
        self.answerpaper.answers.add(self.answer_right)
        self.answerpaper.answers.add(self.answer_wrong)

        self.answer1 = Answer.objects.create(
            question=self.question1,
            answer="answer1", correct=False, error=json.dumps([])
        )
        self.answerpaper.answers.add(self.answer1)

        # create an answerpaper with only one question
        self.answerpaper_single_question = AnswerPaper(
            user=self.user,
            question_paper=self.question_paper,
            start_time=self.start_time,
            end_time=self.end_time,
            user_ip=self.ip
        )
        self.attempted_papers = AnswerPaper.objects.filter(
            question_paper=self.question_paper,
            user=self.user
        )
        self.qtn_paper_with_single_question.fixed_questions.add(self.question4)
        already_attempted = self.attempted_papers.count()
        self.answerpaper_single_question.attempt_number = already_attempted + 1
        self.answerpaper_single_question.save()
        self.answerpaper_single_question.questions.add(self.question4)
        self.answerpaper_single_question.questions_unanswered.add(
            self.question4
            )
        self.answerpaper_single_question.save()
        # answers for the Answer Paper
        self.single_answer = Answer(
            question=self.question4,
            answer="Demo answer",
            correct=True, marks=1,
            error=json.dumps([])
        )
        self.single_answer.save()
        self.answerpaper_single_question.answers.add(self.single_answer)

        self.question1.language = 'python'
        self.question1.test_case_type = 'standardtestcase'
        self.question1.summary = "Q1"
        self.question1.save()
        self.question2.language = 'python'
        self.question2.type = 'mcq'
        self.question2.test_case_type = 'mcqtestcase'
        self.question2.summary = "Q2"
        self.question2.save()
        self.question3.language = 'python'
        self.question3.type = 'mcc'
        self.question3.test_case_type = 'mcqtestcase'
        self.question3.summary = "Q3"
        self.question3.save()
        self.assertion_testcase = StandardTestCase(
            question=self.question1,
            test_case='assert add(1, 3) == 4',
            type='standardtestcase'

        )
        self.assertion_testcase.save()
        self.mcq_based_testcase = McqTestCase(
            options='a',
            question=self.question2,
            correct=True,
            type='mcqtestcase'

        )
        self.mcq_based_testcase.save()
        self.mcc_based_testcase = McqTestCase(
            question=self.question3,
            options='a',
            correct=True,
            type='mcqtestcase'
        )
        self.mcc_based_testcase.save()

        # Setup quiz where questions are shuffled
        # Create Quiz and Question Paper
        self.quiz2 = Quiz.objects.get(description="demo quiz 2")
        self.question_paper2 = QuestionPaper(
            quiz=self.quiz2, total_marks=3, shuffle_questions=True)
        self.question_paper2.save()
        summary_list = ['Q%d' % (i) for i in range(1, 21)]
        self.que_list = Question.objects.filter(summary__in=summary_list)
        self.question_paper2.fixed_questions.add(*self.que_list)

        # Create AnswerPaper for user1 and user2
        self.user1_answerpaper = self.question_paper2.make_answerpaper(
            self.user, self.ip, 1, self.course.id
        )
        self.user2_answerpaper = self.question_paper2.make_answerpaper(
            self.user2, self.ip, 1, self.course.id
        )

        self.user2_answerpaper2 = self.question_paper.make_answerpaper(
            self.user2, self.ip, 1, self.course.id
        )
        self.questions_list = Question.objects.filter(
            summary__in=summary_list[0:5])
        # create question_paper3
        self.question_paper3 = QuestionPaper(
            quiz=self.quiz2, total_marks=3, shuffle_questions=True)
        self.question_paper3.save()
        question_list_with_only_one_category = [
            question for question in self.questions_list
            if question.type == 'code']
        self.question_paper3.fixed_questions.add(
            *question_list_with_only_one_category
        )
        # create anspaper for user1 with questions of only one category
        self.user1_answerpaper2 = self.question_paper3.make_answerpaper(
            self.user, self.ip, 1, self.course.id
        )
        # create question_paper4
        self.question_paper4 = QuestionPaper(
            quiz=self.quiz, total_marks=0, shuffle_questions=True
        )
        self.question_paper4.save()

        # create anspaper for user1 with no questions
        self.user1_answerpaper3 = self.question_paper4.make_answerpaper(
            self.user, self.ip, 1, self.course.id
        )

        settings.code_evaluators['python']['standardtestcase'] = \
            "yaksh.python_assertion_evaluator.PythonAssertionEvaluator"
        self.SERVER_POOL_PORT = 4000
        server_pool = ServerPool(n=1, pool_port=self.SERVER_POOL_PORT)
        self.server_pool = server_pool
        self.server_thread = t = Thread(target=server_pool.run)
        t.start()

    @classmethod
    def tearDownClass(self):
        self.quiz.questionpaper_set.all().delete()
        self.server_pool.stop()
        self.server_thread.join()
        settings.code_evaluators['python']['standardtestcase'] = \
            "python_assertion_evaluator.PythonAssertionEvaluator"

    def test_get_per_question_score(self):
        # Given
        question_id = self.question4.id
        question_name = self.question4.summary
        expected_score = {"Q4": 1.0}
        # When
        score = self.answerpaper_single_question.get_per_question_score(
            [(question_name, question_id, f"{question_id}-comments")]
            )
        # Then
        self.assertEqual(score['Q4'], expected_score['Q4'])

        # Given
        question_id = self.question2.id
        question_name = self.question2.summary
        expected_score = {"Q2": 0.0}
        # When
        score = self.answerpaper.get_per_question_score(
            [(question_name, question_id, f"{question_id}-comments")]
        )
        # Then
        self.assertEqual(score["Q2"], expected_score["Q2"])

        # Given
        question_id = 131
        question_name = "NA"
        expected_score = {'NA': 0}
        # When
        score = self.answerpaper.get_per_question_score(
            [(question_name, question_id, f"{question_id}-comments")]
        )
        # Then
        self.assertEqual(score["NA"], expected_score["NA"])

    def test_returned_question_is_not_none(self):
        # Test add_completed_question and next_question
        # When all questions are answered

        # Before questions are answered
        self.assertEqual(self.answerpaper_single_question.questions_left(), 1)

        current_question = \
            self.answerpaper_single_question.add_completed_question(
                self.question4.id
            )

        # Then
        self.assertEqual(
            self.answerpaper_single_question.questions_answered.all()[0],
            self.question4
        )
        self.assertEqual(self.answerpaper_single_question.questions_left(), 0)
        self.assertIsNotNone(current_question)
        self.assertEqual(current_question.summary, "Q4")

        # When
        next_question = self.answerpaper_single_question.next_question(
            self.question4.id
        )

        # Then
        self.assertEqual(self.answerpaper_single_question.questions_left(), 0)
        self.assertIsNotNone(next_question)
        self.assertEqual(next_question.summary, "Q4")

        # When
        current_question = \
            self.answerpaper_single_question.get_current_question(
                self.answerpaper_single_question.questions.all()
            )

        # Then
        self.assertEqual(self.answerpaper_single_question.questions_left(), 0)
        self.assertIsNotNone(current_question)
        self.assertEqual(current_question.summary, "Q4")

    def test_validate_and_regrade_mcc_correct_answer(self):
        # Given
        mcc_answer = [str(self.mcc_based_testcase.id)]
        self.answer = Answer(question=self.question3,
                             answer=mcc_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(mcc_answer,
                                                  self.question3, json_data
                                                  )

        # Then
        self.assertTrue(result['success'])
        self.assertEqual(result['error'], ['Correct answer'])
        self.answer.correct = True
        self.answer.marks = 1

        # Given
        self.answer.correct = True
        self.answer.marks = 1

        self.answer.answer = ['a', 'b']
        self.answer.save()

        # When
        details = self.answerpaper.regrade(self.question3.id)

        # Then
        self.answer = self.answerpaper.answers.filter(
                            question=self.question3).last()
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_validate_and_regrade_code_correct_answer(self):
        # Given
        # Start code server
        user_answer = dedent("""\
                                def add(a,b):
                                    return a+b
                             """)
        self.answer = Answer(question=self.question1,
                             answer=user_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)
        user = self.answerpaper.user

        # When
        json_data = self.question1.consolidate_answer_data(
            user_answer, user, regrade=True
            )
        get_result = self.answerpaper.validate_answer(user_answer,
                                                      self.question1,
                                                      json_data,
                                                      self.answer.id,
                                                      self.SERVER_POOL_PORT
                                                      )
        url = 'http://localhost:%s' % self.SERVER_POOL_PORT
        check_result = get_result_from_code_server(url, get_result['uid'],
                                                   block=True
                                                   )
        result = json.loads(check_result.get('result'))

        # Then
        self.assertTrue(result['success'])
        self.answer.correct = True
        self.answer.marks = 1

        # Regrade
        # Given
        self.answer.correct = True
        self.answer.marks = 1

        self.answer.answer = dedent("""
                                    def add(a,b):
                                        return a-b
                                    """)
        self.answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id,
                                           self.SERVER_POOL_PORT
                                           )

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question1
                                                      ).last()
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_validate_and_regrade_mcq_correct_answer(self):
        # Given
        mcq_answer = str(self.mcq_based_testcase.id)
        self.answer = Answer(
            question=self.question2,
            answer=mcq_answer,
        )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(mcq_answer,
                                                  self.question2, json_data
                                                  )

        # Then
        self.assertTrue(result['success'])
        self.answer.correct = True
        self.answer.marks = 1

        # Given
        self.answer.correct = True
        self.answer.marks = 1

        self.answer.answer = 'b'
        self.answer.save()

        # When
        details = self.answerpaper.regrade(self.question2.id)

        # Then
        self.answer = self.answerpaper.answers.filter(
            question=self.question2).last()
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_mcq_incorrect_answer(self):
        # Given
        mcq_answer = 'b'
        self.answer = Answer(
            question=self.question2,
            answer=mcq_answer,
        )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(mcq_answer,
                                                  self.question2, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])

    def test_mcc_incorrect_answer(self):
        # Given
        mcc_answer = ['b']
        self.answer = Answer(question=self.question3,
                             answer=mcc_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(mcc_answer,
                                                  self.question3, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])

    def test_answerpaper(self):
        """ Test Answer Paper"""
        self.assertEqual(self.answerpaper.user.username, 'creator')
        self.assertEqual(self.answerpaper.user_ip, self.ip)
        questions = [q.id for q in self.answerpaper.get_questions()]
        num_questions = len(questions)
        self.assertEqual(set(questions), set([q.id for q in self.questions]))
        self.assertEqual(num_questions, 3)
        self.assertEqual(self.answerpaper.question_paper, self.question_paper)
        self.assertEqual(self.answerpaper.start_time, self.start_time)
        self.assertEqual(self.answerpaper.status, 'inprogress')

    def test_questions(self):
        # Test questions_left() method of Answer Paper
        self.assertEqual(self.answerpaper.questions_left(), 3)
        # Test current_question() method of Answer Paper
        current_question = self.answerpaper.current_question()
        self.assertEqual(current_question.summary, "Q1")
        # Test completed_question() method of Answer Paper

        question = self.answerpaper.add_completed_question(self.question1.id)
        self.assertIsNotNone(question)
        self.assertEqual(self.answerpaper.questions_left(), 2)

        # Test next_question() method of Answer Paper
        current_question = self.answerpaper.current_question()
        self.assertEqual(current_question.summary, "Q2")

        # When
        next_question_id = self.answerpaper.next_question(current_question.id)

        # Then
        self.assertTrue(next_question_id is not None)
        self.assertEqual(next_question_id.summary, "Q3")

        # Given, here question is already answered
        current_question_id = self.question1.id

        # When
        next_question_id = self.answerpaper.next_question(current_question_id)

        # Then
        self.assertTrue(next_question_id is not None)
        self.assertEqual(next_question_id.summary, "Q2")

        # Given, wrong question id
        current_question_id = 12

        # When
        next_question_id = self.answerpaper.next_question(current_question_id)

        # Then
        self.assertTrue(next_question_id is not None)
        self.assertEqual(next_question_id.summary, "Q1")

        # Given, last question in the list
        current_question_id = self.question3.id

        # When
        next_question_id = self.answerpaper.next_question(current_question_id)

        # Then
        self.assertTrue(next_question_id is not None)

        self.assertEqual(next_question_id.summary, "Q1")

        # Test get_questions_answered() method
        # When
        questions_answered = self.answerpaper.get_questions_answered()

        # Then
        self.assertEqual(questions_answered.count(), 1)
        self.assertSequenceEqual(questions_answered, [self.questions[0]])

        # When
        questions_unanswered = self.answerpaper.get_questions_unanswered()

        # Then
        self.assertEqual(questions_unanswered.count(), 2)
        self.assertEqual(set([q.id for q in questions_unanswered]),
                         set([self.questions[1].id, self.questions[2].id])
                         )

        # Test completed_question and next_question
        # When all questions are answered

        current_question = self.answerpaper.add_completed_question(
            self.question2.id
        )

        # Then
        self.assertEqual(self.answerpaper.questions_left(), 1)
        self.assertIsNotNone(current_question)
        self.assertEqual(current_question.summary, "Q3")

        # When
        current_question = self.answerpaper.add_completed_question(
                                            self.question3.id
                                            )

        # Then
        self.assertEqual(self.answerpaper.questions_left(), 0)
        self.assertIsNotNone(current_question)
        self.assertTrue(
            current_question == self.answerpaper.get_all_ordered_questions()[0]
            )

        # When
        next_question_id = self.answerpaper.next_question(current_question_id)

        # Then
        all_questions = self.questions.all()
        self.assertTrue(next_question_id == all_questions[0])

    def test_update_marks(self):
        """ Test update_marks method of AnswerPaper"""
        self.answerpaper.update_marks('inprogress')
        self.assertEqual(self.answerpaper.status, 'inprogress')
        self.assertTrue(self.answerpaper.is_attempt_inprogress())
        self.answerpaper.update_marks()
        self.assertEqual(self.answerpaper.status, 'completed')
        self.assertEqual(self.answerpaper.marks_obtained, 1.0)
        self.assertEqual(self.answerpaper.percent, 33.33)
        self.assertTrue(self.answerpaper.passed)
        self.assertFalse(self.answerpaper.is_attempt_inprogress())

    def test_set_end_time(self):
        current_time = timezone.now()
        self.answerpaper.set_end_time(current_time)
        self.assertEqual(self.answerpaper.end_time, current_time)

    def test_get_question_answer(self):
        """ Test get_question_answer() method of Answer Paper"""
        questions = self.answerpaper.questions.all()
        answered = self.answerpaper.get_question_answers()
        self.assertEqual(list(questions), list(answered.keys()))

    def test_is_answer_correct(self):
        self.assertTrue(self.answerpaper.is_answer_correct(self.questions[0]))
        self.assertFalse(self.answerpaper.is_answer_correct(self.questions[1]))

    def test_get_previous_answers(self):
        answers = self.answerpaper.get_previous_answers(self.questions[0])
        self.assertEqual(answers.count(), 2)
        self.assertTrue(answers[0], self.answer_right)
        answers = self.answerpaper.get_previous_answers(self.questions[1])
        self.assertEqual(answers.count(), 1)
        self.assertTrue(answers[0], self.answer_wrong)

    def test_set_marks(self):
        self.answer_wrong.set_marks(0.5)
        self.assertEqual(self.answer_wrong.marks, 0.5)
        self.answer_wrong.set_marks(10.0)
        self.assertEqual(self.answer_wrong.marks, 1.0)

    def test_get_latest_answer(self):
        latest_answer = self.answerpaper.get_latest_answer(self.question1.id)
        self.assertEqual(latest_answer.id, self.answer1.id)
        self.assertEqual(latest_answer.answer, "answer1")

    def test_shuffle_questions(self):
        ques_set_1 = self.user1_answerpaper.get_all_ordered_questions()
        ques_set_2 = self.user2_answerpaper.get_all_ordered_questions()
        self.assertFalse(ques_set_1 == ques_set_2)

    def test_validate_current_question(self):
        self.user2_answerpaper2.questions_unanswered.remove(*self.questions)
        self.assertEqual(self.user2_answerpaper2.current_question(),
                         self.question1)

    def test_duplicate_attempt_answerpaper(self):
        with self.assertRaises(IntegrityError):
            AnswerPaper.objects.create(
                user=self.answerpaper.user,
                question_paper=self.answerpaper.question_paper,
                attempt_number=self.answerpaper.attempt_number,
                start_time=self.answerpaper.start_time,
                end_time=self.answerpaper.end_time,
                course=self.answerpaper.course
                )

    def test_get_categorized_question_indices_with_multiple_categories(self):
        question_indices = {'Programming': [1], 'Objective Type': [2, 3]}
        categorized_question_indices = \
            self.answerpaper.get_categorized_question_indices()
        self.assertDictEqual(question_indices, categorized_question_indices)

    def test_get_categorized_question_indices_for_only_one_category(self):
        question_indices = {'Programming': [1, 2, 3]}
        categorized_question_indices = \
            self.user1_answerpaper2.get_categorized_question_indices()
        self.assertDictEqual(question_indices, categorized_question_indices)

    def test_get_categorized_question_indices_for_no_questions(self):
        question_indices = {}
        categorized_question_indices = \
            self.user1_answerpaper3.get_categorized_question_indices()
        self.assertDictEqual(question_indices, categorized_question_indices)


###############################################################################
class CourseTestCases(unittest.TestCase):
    def setUp(self):
        self.course = Course.objects.get(name="Python Course")
        self.creator = User.objects.get(username="creator")
        self.template_course_user = User.objects.get(username="demo_user4")
        self.student = User.objects.get(username="course_user")
        self.student1 = User.objects.get(username="demo_user2")
        self.student2 = User.objects.get(username="demo_user3")
        self.quiz1 = Quiz.objects.get(description='demo quiz 1')
        self.quiz2 = Quiz.objects.get(description='demo quiz 2')
        self.questions = Question.objects.filter(active=True,
                                                 user=self.creator
                                                 )
        self.modules = LearningModule.objects.filter(creator=self.creator)

        # create courses with disabled enrollment
        self.enroll_request_course = Course.objects.create(
            name="Enrollment Request Course With Enrollment Disabled",
            enrollment="Enroll Request",
            creator=self.creator,
            start_enroll_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                       tzinfo=pytz.utc
                                       ),
            end_enroll_time=datetime(2015, 11, 9, 10, 8, 15, 0,
                                     tzinfo=pytz.utc
                                     ),
        )
        self.open_course = Course.objects.create(
            name="Open Course With Enrollment Disabled",
            enrollment="Open Course",
            creator=self.creator,
            start_enroll_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                       tzinfo=pytz.utc
                                       ),
            end_enroll_time=datetime(2015, 11, 9, 10, 8, 15, 0,
                                     tzinfo=pytz.utc
                                     ),
        )

        # create a course that will be cloned
        self.template_course = Course.objects.create(
            name="Template Course to clone",
            enrollment="Open Course",
            creator=self.creator,
            start_enroll_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                       tzinfo=pytz.utc
                                       ),
            end_enroll_time=datetime(2015, 11, 9, 10, 8, 15, 0,
                                     tzinfo=pytz.utc
                                     ),
        )

        self.template_quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0,
                                     tzinfo=pytz.utc
                                     ),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                   tzinfo=pytz.utc
                                   ),
            duration=30,
            active=False,
            attempts_allowed=-1,
            time_between_attempts=0,
            description='template quiz 1',
            pass_criteria=40,
            instructions="Demo Instructions"
        )

        self.template_question_paper = QuestionPaper.objects.create(
            quiz=self.template_quiz,
            total_marks=0.0,
            shuffle_questions=True
        )

        self.template_question_paper.fixed_questions.add(
            self.questions[1], self.questions[2], self.questions[3]
        )

        self.template_quiz2 = Quiz.objects.create(
            start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                     tzinfo=pytz.utc),
            end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            duration=30,
            active=True,
            attempts_allowed=1,
            time_between_attempts=0,
            pass_criteria=0,
            instructions="Demo Instructions"
        )

        self.template_question_paper2 = QuestionPaper.objects.create(
            quiz=self.template_quiz2,
            total_marks=0.0,
            shuffle_questions=True
        )

        self.template_question_paper2.fixed_questions.add(
            self.questions[1], self.questions[2], self.questions[3]
        )

    def test_get_learning_modules(self):
        # Given
        modules = list(self.modules)
        # When
        course_modules = self.course.get_learning_modules()
        # Then
        self.assertSequenceEqual(list(course_modules), modules)

        # Given
        modules = list(self.modules.filter(name='LM1'))
        module_to_remove = self.modules.get(name='LM2')
        # When
        self.course.learning_module.remove(module_to_remove)
        course_modules = self.course.get_learning_modules()
        # Then
        self.assertSequenceEqual(list(course_modules), modules)

    def test_get_quizzes(self):
        # Given
        quizzes = [self.quiz1]
        # When
        course_quizzes = self.course.get_quizzes()
        # Then
        self.assertSequenceEqual(course_quizzes, quizzes)

    def test_get_learning_units(self):
        # Given
        lesson = Lesson.objects.get(name='L1')
        self.learning_unit_one = LearningUnit.objects.get(order=1,
                                                          lesson=lesson)
        self.learning_unit_two = LearningUnit.objects.get(order=2,
                                                          quiz=self.quiz1)
        learning_units = [self.learning_unit_one, self.learning_unit_two]
        # When
        course_learning_units = self.course.get_learning_units()
        # Then
        self.assertSequenceEqual(course_learning_units, learning_units)

    def test_is_creator(self):
        """ Test is_creator method of Course"""
        self.assertTrue(self.course.is_creator(self.creator))

    def test_is_self_enroll(self):
        """ Test is_self_enroll method of Course"""
        self.assertFalse(self.course.is_self_enroll())

    def test_deactivate(self):
        """ Test deactivate method of Course"""
        self.course.deactivate()
        self.assertFalse(self.course.active)

    def test_activate(self):
        """ Test activate method of Course"""
        self.course.activate()
        self.assertTrue(self.course.active)

    def test_request(self):
        """ Test request and get_requests methods of Course"""
        self.course.request(self.student1, self.student2)
        self.assertSequenceEqual(self.course.get_requests(),
                                 [self.student1, self.student2])

    def test_enroll_reject(self):
        """ Test enroll, reject, get_enrolled and get_rejected methods"""
        self.assertSequenceEqual(self.course.get_enrolled(), [self.student])
        was_rejected = False
        self.course.enroll(was_rejected, self.student1)
        self.assertSequenceEqual(self.course.get_enrolled(),
                                 [self.student1, self.student])

        self.assertSequenceEqual(self.course.get_rejected(), [])
        was_enrolled = False
        self.course.reject(was_enrolled, self.student2)
        self.assertSequenceEqual(self.course.get_rejected(), [self.student2])

        was_rejected = True
        self.course.enroll(was_rejected, self.student2)
        self.assertSequenceEqual(self.course.get_enrolled(),
                                 [self.student1, self.student2, self.student])
        self.assertSequenceEqual(self.course.get_rejected(), [])

        was_enrolled = True
        self.course.reject(was_enrolled, self.student2)
        self.assertSequenceEqual(self.course.get_rejected(), [self.student2])
        self.assertSequenceEqual(self.course.get_enrolled(),
                                 [self.student1, self.student])

        self.assertTrue(self.course.is_enrolled(self.student1))

    def test_add_teachers(self):
        """ Test to add teachers to a course"""
        self.course.add_teachers(self.student1, self.student2)
        self.assertSequenceEqual(self.course.get_teachers(),
                                 [self.student1, self.student2])

    def test_remove_teachers(self):
        """ Test to remove teachers from a course"""
        self.course.add_teachers(self.student1, self.student2)
        self.course.remove_teachers(self.student1)
        self.assertSequenceEqual(self.course.get_teachers(), [self.student2])

    def test_is_teacher(self):
        """ Test to check if user is teacher"""
        self.course.add_teachers(self.student2)
        result = self.course.is_teacher(self.student2)
        self.assertTrue(result)

    def test_create_trial_course(self):
        """Test to check if trial course is created"""
        trial_course = Course.objects.create_trial_course(self.creator)
        self.assertEqual(trial_course.name, "trial_course")
        self.assertEqual(trial_course.enrollment, "open")
        self.assertTrue(trial_course.active)
        self.assertEqual(self.creator, trial_course.creator)
        self.assertIn(self.creator, trial_course.students.all())
        self.assertTrue(trial_course.is_trial)

    def test_enabled_enrollment_for_course(self):
        """Test to check enrollment is closed for open course"""
        self.assertTrue(self.course.is_active_enrollment())

    def test_disabled_enrollment_for_open_course(self):
        """Test to check enrollment is closed for open course"""
        self.assertFalse(self.open_course.is_active_enrollment())

    def test_disabled_enrollment_for_enroll_request_course(self):
        """Test to check enrollment is closed for open course"""
        self.assertFalse(self.enroll_request_course.is_active_enrollment())

    def test_course_complete_percent(self):
        # for course with no modules
        self.no_module_course = Course.objects.create(
            name="test_course", creator=self.creator, enrollment="open")
        modules = self.course.get_learning_modules()
        percent = self.course.percent_completed(self.student1, modules)
        self.assertEqual(percent, 0)
        self.quiz1.questionpaper_set.all().delete()
        # for course with module but zero percent completed
        percent = self.course.percent_completed(self.student1, modules)
        self.assertEqual(percent, 0)

        # Add completed unit to course status and check percent
        lesson = Lesson.objects.get(name='L1')
        self.completed_unit = LearningUnit.objects.get(lesson=lesson)

        course_status = CourseStatus.objects.create(
            course=self.course, user=self.student1)
        course_status.completed_units.add(self.completed_unit)
        updated_percent = self.course.percent_completed(self.student1, modules)
        self.assertEqual(updated_percent, 25)

    def test_course_time_remaining_to_start(self):
        # check if course has 0 days left to start
        self.assertEqual(self.course.days_before_start(), 0)

        # check if course has some days left to start
        course_time = self.course.start_enroll_time
        self.course.start_enroll_time = datetime(
            2199, 12, 31, 10, 8, 15, 0,
            tzinfo=pytz.utc
        )
        self.course.save()
        updated_course = Course.objects.get(id=self.course.id)
        time_diff = updated_course.start_enroll_time - timezone.now()
        actual_days = time_diff.days + 1
        self.assertEqual(updated_course.days_before_start(), actual_days)
        self.course.start_enroll_time = course_time
        self.course.save()


###############################################################################
class TestCaseTestCases(unittest.TestCase):
    def setUp(self):
        self.user = User.objects.get(username="creator")
        self.question1 = Question(
            summary='Demo question 1', language='Python',
            type='Code', active=True, description='Write a function',
            points=1.0, user=self.user, snippet='def myfunc()'
        )
        self.question2 = Question(
            summary='Demo question 2', language='Python',
            type='Code', active=True, description='Write to standard output',
            points=1.0, user=self.user, snippet='def myfunc()'
        )
        self.question1.save()
        self.question2.save()
        self.assertion_testcase = StandardTestCase(
            question=self.question1,
            test_case='assert myfunc(12, 13) == 15',
            type='standardtestcase'
        )
        self.stdout_based_testcase = StdIOBasedTestCase(
            question=self.question2,
            expected_output='Hello World',
            type='standardtestcase'

        )
        self.assertion_testcase.save()
        self.stdout_based_testcase.save()
        answer_data = {'metadata': {'user_answer': 'demo_answer',
                                    'language': 'python',
                                    'partial_grading': False
                                    },
                       'test_case_data': [
                       {'test_case': 'assert myfunc(12, 13) == 15',
                        'test_case_type': 'standardtestcase',
                        'test_case_args': "",
                        'weight': 1.0,
                        'hidden': False
                        }]
                       }
        self.answer_data_json = json.dumps(answer_data)

    def test_assertion_testcase(self):
        """ Test question """
        self.assertEqual(self.assertion_testcase.question, self.question1)
        self.assertEqual(self.assertion_testcase.test_case,
                         'assert myfunc(12, 13) == 15')

    def test_stdout_based_testcase(self):
        """ Test question """
        self.assertEqual(self.stdout_based_testcase.question, self.question2)
        self.assertEqual(self.stdout_based_testcase.expected_output,
                         'Hello World'
                         )

    def test_consolidate_answer_data(self):
        """ Test consolidate answer data model method """
        result = self.question1.consolidate_answer_data(
            user_answer="demo_answer"
        )
        actual_data = json.loads(result)
        exp_data = json.loads(self.answer_data_json)
        self.assertEqual(actual_data['metadata']['user_answer'],
                         exp_data['metadata']['user_answer'])
        self.assertEqual(actual_data['test_case_data'],
                         exp_data['test_case_data'])


class AssignmentUploadTestCases(unittest.TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='creator1',
            password='demo',
            email='demo@test1.com',
            first_name="dummy1", last_name="dummy1"
        )
        self.user2 = User.objects.create_user(
            username='creator2',
            password='demo',
            email='demo@test2.com',
            first_name="dummy1", last_name="dummy1"
        )
        self.quiz = Quiz.objects.create(
            start_date_time=datetime(
                2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc
            ),
            end_date_time=datetime(
                2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc
            ),
            duration=30, active=True,
            attempts_allowed=1, time_between_attempts=0,
            description='demo quiz 1', pass_criteria=0,
            instructions="Demo Instructions"
        )

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request",
            creator=self.user1
        )

        self.questionpaper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=0.0, shuffle_questions=True
        )
        self.question = Question.objects.create(
            summary='Assignment', language='Python', type='upload',
            active=True, description='Upload a file', points=1.0, snippet='',
            user=self.user1
        )
        self.questionpaper.fixed_question_order = "{0}".format(
            self.question.id)
        self.questionpaper.fixed_questions.add(self.question)

        attempt = 1
        ip = '127.0.0.1'
        self.answerpaper1 = self.questionpaper.make_answerpaper(
                self.user1, ip, attempt, self.course.id
            )

        file_path1 = os.path.join(dj_settings.MEDIA_ROOT, "upload1.txt")
        file_path2 = os.path.join(dj_settings.MEDIA_ROOT, "upload2.txt")
        self.assignment1 = AssignmentUpload.objects.create(
            assignmentQuestion=self.question,
            assignmentFile=file_path1, answer_paper=self.answerpaper1,
            )
        self.assignment2 = AssignmentUpload.objects.create(
            assignmentQuestion=self.question,
            assignmentFile=file_path2, answer_paper=self.answerpaper1,
            )

    def test_get_assignments_for_user_files(self):
        assignment_files, file_name = AssignmentUpload.objects.get_assignments(
                                    self.questionpaper, self.question.id,
                                    self.user1.id, self.course.id
                                    )
        self.assertIn("upload1.txt", assignment_files[0].assignmentFile.name)
        self.assertEqual(assignment_files[0].answer_paper.user, self.user1)
        actual_file_name = self.user1.get_full_name().replace(" ", "_")
        file_name = file_name.replace(" ", "_")
        self.assertEqual(file_name, actual_file_name)

    def test_get_assignments_for_quiz_files(self):
        assignment_files, file_name = AssignmentUpload.objects.get_assignments(
            self.questionpaper, course_id=self.course.id
            )
        files = [os.path.basename(file.assignmentFile.name)
                 for file in assignment_files]
        question_papers = [
            file.answer_paper.question_paper for file in assignment_files]
        self.assertIn("upload1.txt", files)
        self.assertIn("upload2.txt", files)
        self.assertEqual(question_papers[0].quiz, self.questionpaper.quiz)
        actual_file_name = self.course.name.replace(" ", "_")
        file_name = file_name.replace(" ", "_")
        self.assertIn(actual_file_name, file_name)

    def tearDown(self):
        self.questionpaper.delete()
        self.question.delete()
        self.course.delete()
        self.quiz.delete()
        self.user2.delete()
        self.user1.delete()


class CourseStatusTestCases(unittest.TestCase):
    def setUp(self):
        user = User.objects.get(username='creator')
        self.course = Course.objects.create(name="Demo Course", creator=user,
                                            enrollment="Enroll Request")
        self.module = LearningModule.objects.create(name='M1', creator=user,
                                                    description='module one')
        self.quiz1 = Quiz.objects.create(time_between_attempts=0, weightage=50,
                                         description='qz1')
        self.quiz2 = Quiz.objects.create(
            time_between_attempts=0, weightage=100, description='qz2'
            )
        question = Question.objects.first()
        self.qpaper1 = QuestionPaper.objects.create(quiz=self.quiz1)
        self.qpaper2 = QuestionPaper.objects.create(quiz=self.quiz2)
        self.qpaper1.fixed_questions.add(question)
        self.qpaper2.fixed_questions.add(question)
        self.qpaper1.update_total_marks()
        self.qpaper2.update_total_marks()
        self.qpaper1.save()
        self.qpaper2.save()
        self.unit_1_quiz = LearningUnit.objects.create(order=1, type='quiz',
                                                       quiz=self.quiz1)
        self.unit_2_quiz = LearningUnit.objects.create(order=2, type='quiz',
                                                       quiz=self.quiz2)
        self.module.learning_unit.add(self.unit_1_quiz)
        self.module.learning_unit.add(self.unit_2_quiz)
        self.module.save()
        self.course.learning_module.add(self.module)
        student = User.objects.get(username='course_user')
        self.course.students.add(student)
        self.course.save()

        attempt = 1
        ip = '127.0.0.1'
        self.answerpaper1 = self.qpaper1.make_answerpaper(student, ip, attempt,
                                                          self.course.id)
        self.answerpaper2 = self.qpaper2.make_answerpaper(student, ip, attempt,
                                                          self.course.id)

        self.course_status = CourseStatus.objects.create(course=self.course,
                                                         user=student)

    def tearDown(self):
        self.course_status.delete()
        self.answerpaper1.delete()
        self.answerpaper2.delete()
        self.qpaper1.delete()
        self.qpaper2.delete()
        self.quiz1.delete()
        self.quiz2.delete()
        self.unit_1_quiz.delete()
        self.unit_2_quiz.delete()
        self.module.delete()
        self.course.delete()

    def test_course_is_complete(self):
        # When
        self.course_status.completed_units.add(self.unit_1_quiz)
        # Then
        self.assertFalse(self.course_status.is_course_complete())

        # When
        self.course_status.completed_units.add(self.unit_2_quiz)
        # Then
        self.assertTrue(self.course_status.is_course_complete())

        # Given
        self.answerpaper1.marks_obtained = 1
        self.answerpaper1.save()
        self.answerpaper2.marks_obtained = 0
        self.answerpaper2.save()
        # When
        self.course_status.calculate_percentage()
        # Then
        self.assertEqual(round(self.course_status.percentage, 2), 33.33)
        # When
        self.course_status.set_grade()
        # Then
        self.assertEqual(self.course_status.get_grade(), 'F')

        # Given
        self.answerpaper1.marks_obtained = 0
        self.answerpaper1.save()
        self.answerpaper2.marks_obtained = 1
        self.answerpaper2.save()
        # When
        self.course_status.calculate_percentage()
        # Then
        self.assertEqual(round(self.course_status.percentage, 2), 66.67)
        # When
        self.course_status.set_grade()
        # Then
        self.assertEqual(self.course_status.get_grade(), 'B')

        # Test get course grade after completion
        self.assertEqual(self.course.get_grade(self.answerpaper1.user), 'B')


class FileUploadTestCases(unittest.TestCase):
    def setUp(self):
        self.question = Question.objects.get(summary='Q1')
        self.filename = "uploadtest.txt"
        self.uploaded_file = SimpleUploadedFile(self.filename, b'Test File')
        self.file_upload = FileUpload.objects.create(
            file=self.uploaded_file,
            question=self.question
        )

    def test_get_file_name(self):
        self.assertEqual(self.file_upload.get_filename(), self.filename)

    def tearDown(self):
        self.file_upload.delete()


class PostModelTestCases(unittest.TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            username='bart',
            password='bart',
            email='bart@test.com'
        )
        Profile.objects.create(
            user=self.user1,
            roll_number=1,
            institute='IIT',
            department='Chemical',
            position='Student'
        )

        self.user2 = User.objects.create(
            username='dart',
            password='dart',
            email='dart@test.com'
        )
        Profile.objects.create(
            user=self.user2,
            roll_number=2,
            institute='IIT',
            department='Chemical',
            position='Student'
        )

        self.user3 = User.objects.create(
            username='user3',
            password='user3',
            email='user3@test.com'
        )
        Profile.objects.create(
            user=self.user3,
            roll_number=3,
            is_moderator=True,
            department='Chemical',
            position='Teacher'
        )

        self.course = Course.objects.create(
            name='Python Course',
            enrollment='Enroll Request',
            creator=self.user3
        )
        course_ct = ContentType.objects.get_for_model(self.course)
        self.post1 = Post.objects.create(
            title='Post 1',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.user1,
            description='Post 1 description'
        )
        self.comment1 = Comment.objects.create(
            post_field=self.post1,
            creator=self.user2,
            description='Post 1 comment 1'
        )
        self.comment2 = Comment.objects.create(
            post_field=self.post1,
            creator=self.user3,
            description='Post 1 user3 comment 2'
        )

    def test_get_last_comment(self):
        last_comment = self.post1.get_last_comment()
        self.assertEquals(last_comment.description, 'Post 1 user3 comment 2')

    def test_get_comments_count(self):
        count = self.post1.get_comments_count()
        self.assertEquals(count, 2)

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.course.delete()
        self.post1.delete()


class QRcodeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        quiz = Quiz.objects.get(description='demo quiz 1')
        cls.questionpaper = QuestionPaper.objects.create(quiz=quiz)
        question = Question.objects.get(summary='Q1')
        question.type = 'upload'
        question.save()
        cls.questionpaper.fixed_questions.add(question)
        cls.questionpaper.update_total_marks()
        student = User.objects.get(username='course_user')
        course = Course.objects.get(name='Python Course')
        attempt = 1
        ip = '127.0.0.1'
        answerpaper = cls.questionpaper.make_answerpaper(
            student, ip, attempt, course.id)
        cls.qrcode_handler = QRcodeHandler.objects.create(
            user=student, answerpaper=answerpaper, question=question)
        cls.old_qrcode = cls.qrcode_handler._create_qrcode()
        cls.old_qrcode.set_used()
        cls.old_qrcode.save()
        cls.qrcode = cls.qrcode_handler.get_qrcode()
        cls.answerpaper = answerpaper

    @classmethod
    def tearDownClass(cls):
        cls.qrcode.image.delete()
        cls.qrcode.delete()
        cls.qrcode_handler.delete()
        cls.answerpaper.delete()
        cls.questionpaper.delete()
        QRcode.objects.all().delete()
        QRcodeHandler.objects.all().delete()

    def test_active(self):
        # Given
        qrcode = self.qrcode

        # Then
        self.assertFalse(qrcode.is_active())

        # When
        qrcode.activate()
        qrcode.save()

        # Then
        self.assertTrue(qrcode.is_active())

        # When
        qrcode.deactivate()
        qrcode.save()

        # Then
        self.assertFalse(qrcode.is_active())

    def test_used(self):
        # Given
        qrcode = self.qrcode

        # Then
        self.assertFalse(qrcode.is_used())

        # When
        qrcode.set_used()
        qrcode.save()

        # Then
        self.assertTrue(qrcode.is_used())

        # When
        qrcode.used = False
        qrcode.save()

        # Then
        self.assertFalse(qrcode.is_used())

    def test_random_key(self):
        # Given
        qrcode = self.qrcode

        # When
        expect_key = hashlib.sha1('{0}'.format(qrcode.id).encode()).hexdigest()

        # Then
        self.assertEqual(qrcode.random_key, expect_key)
        self.assertEqual(len(qrcode.random_key), 40)

    def test_short_key(self):
        # Given
        qrcode = self.qrcode

        # When
        expect_key = hashlib.sha1('{0}'.format(qrcode.id).encode()).hexdigest()

        # Then
        self.assertEqual(qrcode.short_key, expect_key[0:5])
        self.assertEqual(len(qrcode.short_key), 5)

        # Given
        old_qrcode = self.old_qrcode
        old_qrcode.random_key = qrcode.random_key
        old_qrcode.save()

        # When
        old_qrcode.set_short_key()

        # Then
        self.assertEqual(old_qrcode.short_key, expect_key[0:6])
        self.assertEqual(len(old_qrcode.short_key), 6)

    def test_generate_image(self):
        # Given
        qrcode = self.qrcode
        image_name = qrcode.short_key

        # When
        qrcode.generate_image('test')

        # Then
        self.assertTrue(qrcode.is_active())
        self.assertIn(image_name, qrcode.image.name)

    def test_get_qrcode(self):
        # Given
        handler = self.qrcode_handler
        self.qrcode.activate()
        self.qrcode.save()
        expected_qrcode = self.qrcode

        # When
        qrcode = handler.get_qrcode()

        # Then
        self.assertEqual(qrcode, expected_qrcode)
        self.qrcode.deactivate()
        self.qrcode.save()

    def test_can_use(self):
        # Given
        handler = self.qrcode_handler

        # When
        can_use = handler.can_use()

        # Then
        self.assertTrue(can_use)

        # Given
        answerpaper = self.answerpaper

        # When
        answerpaper.update_marks(state='complete')
        can_use = handler.can_use()

        # Then
        self.assertFalse(can_use)
