
'''
Status Codes :

302 - Redirect
404 - Page Not Found
200 - Success

'''

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from yaksh.models import (
    Profile, Course, Question, Quiz,
    QuestionPaper, AnswerPaper,
    Answer
)
import pytz
from datetime import datetime
import json


client = Client()


def create_student_profile(self):
    # studernt profile
    self.user_student_pass = 'demo_student'
    self.user_student = User.objects.create_user(
        username='demo_student',
        password=self.user_student_pass,
        first_name='demo',
        last_name='student'
    )

    Profile.objects.create(
        user=self.user_student,
        roll_number=1,
        institute='CSPIT',
        department='Computer',
        position='Graduate Student',
        timezone='UTC',
        state='Gujarat',
        gender='Male',
        age=20
    )


def create_teacher_profile(self):
    # teacher profile with moderator access
    self.user_teacher_pass = 'demo_teacher'
    self.user_teacher = User.objects.create_user(
        username='demo_teacher',
        password=self.user_teacher_pass,
        first_name='demo',
        last_name='teacher'
    )

    Profile.objects.create(
        user=self.user_teacher,
        institute='CSPIT',
        department='Computer',
        position='Teacher',
        timezone='UTC',
        state='Gujarat',
        gender='Male',
        age=35
    )

    moderator_group = Group.objects.create(name='moderator')
    moderator_group.user_set.add(self.user_teacher)


class ModeratorAnalysisTest(TestCase):
    """
    check if the moderator report is functional and none of
    the students are able to access it
    """

    def setUp(self):
        create_student_profile(self)
        create_teacher_profile(self)

    def test_cannot_view_moderator_analysis_without_login(self):
        """
        login required, hence redirects
        """

        response = client.get(reverse('analysis:final_summary'))
        self.assertEqual(response.status_code, 302)

    def test_student_cannot_view_moderator_analysis(self):
        """
        student cannot view moderator analysis, hence page not found
        """

        client.login(username=self.user_student.username,
                     password=self.user_student_pass)
        response = client.get(reverse('analysis:final_summary'))
        self.assertEqual(response.status_code, 404)

    def test_moderator_can_view_moderator_analysis(self):
        """
        moderator can view moderator analysis, hence accepts
        """

        client.login(username=self.user_teacher.username,
                     password=self.user_teacher_pass)
        response = client.get(reverse('analysis:final_summary'))
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()


class StudentAnalysisTest(TestCase):

    def setUp(self):
        create_student_profile(self)
        create_teacher_profile(self)

        self.course = Course.objects.create(
            name='demo_course',
            enrollment="open",
            start_enroll_time=datetime(
                2018, 6, 29, 13, 49, 0, 0, tzinfo=pytz.UTC),
            end_enroll_time=datetime(
                2019, 6, 29, 13, 49, 0, 0, tzinfo=pytz.UTC),
            creator=self.user_teacher
        )

        self.quiz = Quiz.objects.create(
            duration=30,
            instructions="demo quiz",
            description='demo quiz',
            creator=self.user_teacher
        )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz
        )

        self.answerpaper = AnswerPaper.objects.create(
            user=self.user_student,
            question_paper=self.question_paper,
            course=self.course,
            attempt_number=1,
            start_time=datetime(2018, 6, 29, 13, 49, 0, 0, tzinfo=pytz.UTC),
            end_time=datetime(2019, 6, 29, 13, 49, 0, 0, tzinfo=pytz.UTC),
        )

    def add_question(self, type):
        self.question = Question.objects.create(
            summary="demo_question",
            description="demo question",
            language="python",
            type=type,
            user=self.user_teacher
        )
        self.question_paper.fixed_questions.add(self.question)

    def add_answer(self):

        self.answer = Answer.objects.create(
            question=self.question,
            answer='demo answer',
            error=json.dumps([])
        )

        self.answerpaper.answers.add(self.answer)
        self.answerpaper.questions_answered.add(self.question)

    def test_cannot_view_without_course_enrollment(self):
        """
        Student cannot view stats without enrollment, hence redirects
        """

        client.login(username=self.user_student.username,
                     password=self.user_student_pass)
        response = client.get(reverse('analysis:view_quiz_stats',
                                      kwargs={'question_paper_id': (
                                          self.question_paper.id),
                                          'course_id': self.course.id}))

        self.assertEqual(response.status_code, 302)

    def test_no_view_for_no_code_quiz(self):
        """
        stats not required if no code questions,
        hence redirects
        """
        self.course.students.add(self.user_student)

        client.login(username=self.user_student.username,
                     password=self.user_student_pass)
        response = client.get(reverse('analysis:view_quiz_stats',
                                      kwargs={'question_paper_id': (
                                          self.question_paper.id),
                                          'course_id': self.course.id}))

        self.assertEqual(response.status_code, 302)

    def test_view_success(self):
        """
        successful as quiz has code question
        """
        self.course.students.add(self.user_student)
        self.add_question('code')
        self.add_answer()

        client.login(username=self.user_student.username,
                     password=self.user_student_pass)
        response = client.get(reverse('analysis:view_quiz_stats',
                                      kwargs={'question_paper_id': (
                                              self.question_paper.id),
                                              'course_id': self.course.id}))

        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        User.objects.all().delete()
        Course.objects.all().delete()
        Quiz.objects.all().delete()
        QuestionPaper.objects.all().delete()
        AnswerPaper.objects.all().delete()
        Question.objects.all().delete()
        Answer.objects.all().delete()


class RegistrationFormTest(TestCase):
    """
    check if the registration form is functional and
    no bad values are allowed to the newly introduced
    fields - age, gender, state, position
    """

    def test_registeration_success(self):
        """
        check whether user successfully registers
        """

        client.post(reverse('yaksh:register'),
                    data={'username': 'demo_user',
                          'email': 'demo@demo.com', 'password': 'demo_pass',
                          'confirm_password': 'demo_pass',
                          'first_name': 'demo_fname',
                          'last_name': 'demo_lname', 'roll_number': '777',
                          'institute': 'demo_institute',
                          'department': 'demo_dept',
                          'position': 'Graduate Student',
                          'timezone': pytz.utc.zone,
                          'age': 18, 'gender': 'Male', 'state': 'Gujarat'
                          }
                    )

        registered_user = User.objects.get(username='demo_user')

        self.assertEqual(registered_user.email, 'demo@demo.com')
        self.assertEqual(registered_user.first_name, 'demo_fname')
        self.assertEqual(registered_user.last_name, 'demo_lname')
        self.assertEqual(registered_user.profile.roll_number, '777')
        self.assertEqual(registered_user.profile.institute, 'demo_institute')
        self.assertEqual(registered_user.profile.department, 'demo_dept')
        self.assertEqual(registered_user.profile.position, 'Graduate Student')
        self.assertEqual(registered_user.profile.age, 18)
        self.assertEqual(registered_user.profile.gender, 'Male')
        self.assertEqual(registered_user.profile.state, 'Gujarat')
        self.assertEqual(registered_user.profile.timezone, 'UTC')

    def test_char_age_value(self):
        """
        as age is a numeric value, therefore post fails and no user is created
        """
        client.post(reverse('yaksh:register'),
                    data={'username': 'demo_user',
                          'email': 'demo@demo.com', 'password': 'demo_pass',
                          'confirm_password': 'demo_pass',
                          'first_name': 'demo_fname',
                          'last_name': 'demo_lname', 'roll_number': '777',
                          'institute': 'demo_institute',
                          'department': 'demo_dept',
                          'position': 'Graduate Student',
                          'timezone': pytz.utc.zone,
                          'age': 'eighteen', 'gender': 'Male',
                          'state': 'Gujarat'
                          }
                    )

        registered_user = User.objects.filter(username='demo_user').exists()
        self.assertFalse(registered_user)

    def test_undefined_gender_value(self):
        """
        as we have predefined values for gender,
        enter something else would not create user
        """
        client.post(reverse('yaksh:register'),
                    data={'username': 'demo_user',
                          'email': 'demo@demo.com', 'password': 'demo_pass',
                          'confirm_password': 'demo_pass',
                          'first_name': 'demo_fname',
                          'last_name': 'demo_lname', 'roll_number': '777',
                          'institute': 'demo_institute',
                          'department': 'demo_dept',
                          'position': 'Graduate Student',
                          'timezone': pytz.utc.zone,
                          'age': 18, 'gender': 'Something', 'state': 'Gujarat'
                          }
                    )

        registered_user = User.objects.filter(username='demo_user').exists()
        self.assertFalse(registered_user)

    def test_undefined_state_value(self):
        """
        as we have predefined values for state,
        enter something else would not create user
        """
        client.post(reverse('yaksh:register'),
                    data={'username': 'demo_user',
                          'email': 'demo@demo.com', 'password': 'demo_pass',
                          'confirm_password': 'demo_pass',
                          'first_name': 'demo_fname',
                          'last_name': 'demo_lname', 'roll_number': '777',
                          'institute': 'demo_institute',
                          'department': 'demo_dept',
                          'position': 'Graduate Student',
                          'timezone': pytz.utc.zone,
                          'age': 18, 'gender': 'Male', 'state': 'Something'
                          }
                    )

        registered_user = User.objects.filter(username='demo_user').exists()
        self.assertFalse(registered_user)

    def test_undefined_position_value(self):
        """
        as we have predefined values for state,
        enter something else would not create user
        """
        client.post(reverse('yaksh:register'),
                    data={'username': 'demo_user',
                          'email': 'demo@demo.com', 'password': 'demo_pass',
                          'confirm_password': 'demo_pass',
                          'first_name': 'demo_fname',
                          'last_name': 'demo_lname', 'roll_number': '777',
                          'institute': 'demo_institute',
                          'department': 'demo_dept',
                          'position': 'student', 'timezone': pytz.utc.zone,
                          'age': 18, 'gender': 'Male', 'state': 'Gujarat'
                          }
                    )

        registered_user = User.objects.filter(username='demo_user').exists()
        self.assertFalse(registered_user)

    def tearDown(self):
        User.objects.all().delete()


class CourseFormTest(TestCase):

    def setUp(self):
        create_teacher_profile(self)

    def test_course_creation_success(self):
        """
        test if course can be created after addition
        of new field - level
        """

        self.client.login(username=self.user_teacher.username,
                          password=self.user_teacher_pass)
        self.client.post(reverse('yaksh:add_course'),
                         data={'name': 'demo_course', 'group': 'Self',
                               'level': 'Basic', 'enrollment': 'open',
                               'active': True, 'code': 'demo_code',
                               'instructions': 'demo_instruct',
                               'start_enroll_time': '2018-06-29 13:49:00',
                               'end_enroll_time': '2019-06-29 13:49:00',
                               }
                         )

        created_course = Course.objects.get(name='demo_course')

        self.assertEqual(created_course.name, 'demo_course')
        self.assertEqual(created_course.level, 'Basic')
        self.assertEqual(created_course.group, 'Self')
        self.assertEqual(created_course.enrollment, 'open')
        self.assertEqual(created_course.active, True)
        self.assertEqual(created_course.code, 'demo_code')
        self.assertEqual(created_course.instructions, 'demo_instruct')

    def test_undefined_level_value(self):
        """
        as we have predefined values for level,
        enter something else would not create user
        """

        self.client.login(username=self.user_teacher.username,
                          password=self.user_teacher_pass)
        self.client.post(reverse('yaksh:add_course'),
                         data={'name': 'demo_course', 'group': 'Self',
                               'level': 'Something', 'enrollment': 'open',
                               'active': True, 'code': 'demo_code',
                               'instructions': 'demo_instruct',
                               'start_enroll_time': '2018-06-29 13:49:00',
                               'end_enroll_time': '2019-06-29 13:49:00',
                               }
                         )

        created_course = Course.objects.filter(name='demo_course').exists()
        self.assertFalse(created_course)

    def test_undefined_group_value(self):
        """
        as we have predefined values for level,
        enter something else would not create user
        """

        self.client.login(username=self.user_teacher.username,
                          password=self.user_teacher_pass)
        self.client.post(reverse('yaksh:add_course'),
                         data={'name': 'demo_course', 'group': 'Something',
                               'level': 'Basic', 'enrollment': 'open',
                               'active': True, 'code': 'demo_code',
                               'instructions': 'demo_instruct',
                               'start_enroll_time': '2018-06-29 13:49:00',
                               'end_enroll_time': '2019-06-29 13:49:00',
                               }
                         )

        created_course = Course.objects.filter(name='demo_course').exists()
        self.assertFalse(created_course)

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        Course.objects.all().delete()
