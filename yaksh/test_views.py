from datetime import datetime
import pytz
import os
import json
import time
try:
    from StringIO import StringIO as string_io
except ImportError:
    from io import BytesIO as string_io
import zipfile
import shutil
from markdown import Markdown
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from django.urls import reverse, resolve
from django.test import TestCase
from django.test import Client
from django.http import Http404
from django.utils import timezone
from django.core import mail
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files import File
from django.contrib.messages import get_messages
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase


from yaksh.models import (
    User, Profile, Question, Quiz, QuestionPaper, AnswerPaper, Answer, Course,
    AssignmentUpload, McqTestCase, IntegerTestCase, StringTestCase,
    FloatTestCase, FIXTURES_DIR_PATH, LearningModule, LearningUnit, Lesson,
    LessonFile, CourseStatus, dict_to_yaml, Post, Comment, Topic,
    TableOfContents, LessonQuizAnswer
)
from yaksh.views import add_as_moderator, course_forum, post_comments
from yaksh.forms import PostForm, CommentForm
from yaksh.decorators import user_has_profile
from online_test.celery_settings import app

from notifications_plugin.models import Notification

app.conf.update(CELERY_ALWAYS_EAGER=True)


class TestUserRegistration(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

    def tearDown(self):
        self.registered_user.delete()
        self.mod_group.delete()

    def test_register_user_post(self):
        self.client.post(
            reverse('yaksh:register'),
            data={'username': 'register_user',
                  'email': 'register_user@mail.com', 'password': 'reg_user',
                  'confirm_password': 'reg_user', 'first_name': 'user1_f_name',
                  'last_name': 'user1_l_name', 'roll_number': '1',
                  'institute': 'demo_institute', 'department': 'demo_dept',
                  'position': 'student', 'timezone': pytz.utc.zone
                  }
            )
        self.registered_user = User.objects.get(username='register_user')
        self.assertEqual(self.registered_user.email, 'register_user@mail.com')
        self.assertEqual(self.registered_user.first_name, 'user1_f_name')
        self.assertEqual(self.registered_user.last_name, 'user1_l_name')
        self.assertEqual(self.registered_user.profile.roll_number, '1')
        self.assertEqual(self.registered_user.profile.institute,
                         'demo_institute')
        self.assertEqual(self.registered_user.profile.department, 'demo_dept')
        self.assertEqual(self.registered_user.profile.position, 'student')
        self.assertEqual(self.registered_user.profile.timezone, 'UTC')


class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

        # Create User without profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            email='demo1@test.com'
        )

        # Create User with profile
        self.user2_plaintext_pass = 'demo2'
        self.user2 = User.objects.create_user(
            username='demo_user2',
            password=self.user2_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.user2,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Student',
            timezone='UTC'
        )

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.user2.delete()
        self.mod_group.delete()

    def test_user_has_profile_for_user_without_profile(self):
        """
        If no profile exists for user passed as argument return False
        """
        has_profile_status = user_has_profile(self.user1)
        self.assertFalse(has_profile_status)

    def test_user_has_profile_for_user_with_profile(self):
        """
        If profile exists for user passed as argument return True
        """
        has_profile_status = user_has_profile(self.user2)
        self.assertTrue(has_profile_status)

    def test_view_profile_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(reverse('yaksh:view_profile'), follow=True)
        redirect_destination = '/exam/login/?next=/exam/viewprofile/'
        self.assertRedirects(response, redirect_destination)

    def test_view_profile_get_for_user_without_profile(self):
        """
        If no profile exists a blank profile form will be displayed
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:view_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/editprofile.html')

    def test_view_profile_get_for_user_with_profile(self):
        """
        If profile exists a viewprofile.html template will be rendered
        """
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:view_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/view_profile.html')

    def test_email_verification_for_user_post(self):
        """
        POST request to verify email
        """
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        post_response = self.client.post(
                reverse('yaksh:new_activation'),
                data={'email': self.user2.email}
            )
        subject = mail.outbox[0].subject.replace(" ", "_")
        activation_key = mail.outbox[0].body.split("\n")[2].split("/")[-1]
        get_response = self.client.get(
            reverse('yaksh:activate', kwargs={'key': activation_key}),
            follow=True
            )
        updated_profile_user = User.objects.get(id=self.user2.id)
        updated_profile = Profile.objects.get(user=updated_profile_user)
        self.assertEqual(post_response.status_code, 200)
        self.assertEqual(subject, "Yaksh_Email_Verification")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(updated_profile.is_email_verified, True)
        self.assertTemplateUsed(get_response, 'yaksh/activation_status.html')

        post_response = self.client.post(
                reverse('yaksh:new_activation'),
                data={'email': 'user@mail.com'}
            )
        self.assertEqual(post_response.status_code, 200)
        self.assertFalse(post_response.context['success'])
        self.assertTemplateUsed(get_response, 'yaksh/activation_status.html')

    def test_edit_profile_post(self):
        """
        POST request to edit_profile view should update the user's profile
        """
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:edit_profile'),
            data={
                'user': self.user2,
                'first_name': 'new_first_name',
                'last_name': 'new_last_name',
                'roll_number': 20,
                'institute': 'new_institute',
                'department': 'Aerospace',
                'position': 'new_position',
                'timezone': 'UTC'
            }
        )
        updated_profile_user = User.objects.get(id=self.user2.id)
        updated_profile = Profile.objects.get(user=updated_profile_user)
        self.assertEqual(updated_profile_user.first_name, 'new_first_name')
        self.assertEqual(updated_profile_user.last_name, 'new_last_name')
        self.assertEqual(updated_profile.roll_number, '20')
        self.assertEqual(updated_profile.institute, 'new_institute')
        self.assertEqual(updated_profile.department, 'Aerospace')
        self.assertEqual(updated_profile.position, 'new_position')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/profile_updated.html')

    def test_edit_profile_post_for_user_without_profile(self):
        """
        POST request to edit_profile view should update the user's profile
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:edit_profile'),
            data={
                'user': self.user1,
                'first_name': 'new_first_name',
                'last_name': 'new_last_name',
                'roll_number': 21,
                'institute': 'new_institute',
                'department': 'Aerospace',
                'position': 'new_position',
                'timezone': 'UTC'
            }
        )
        updated_profile_user = User.objects.get(id=self.user1.id)
        updated_profile = Profile.objects.get(user=updated_profile_user)
        self.assertEqual(updated_profile_user.first_name, 'new_first_name')
        self.assertEqual(updated_profile_user.last_name, 'new_last_name')
        self.assertEqual(updated_profile.roll_number, '21')
        self.assertEqual(updated_profile.institute, 'new_institute')
        self.assertEqual(updated_profile.department, 'Aerospace')
        self.assertEqual(updated_profile.position, 'new_position')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/profile_updated.html')

    def test_edit_profile_get(self):
        """
        GET request to edit profile should display profile form
        """
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/editprofile.html')

    def test_edit_profile_get_for_user_without_profile(self):
        """
        If no profile exists a blank profile form will be displayed
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/editprofile.html')

    def test_edit_profile_get_for_user_with_profile(self):
        """
        If profile exists a editprofile.html template will be rendered
        """
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/editprofile.html')

    def test_update_email_for_user_post(self):
        """ POST request to update email if multiple users with same email are
            found
        """
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:update_email'),
            data={
                'username': self.user2.username,
                'email': "demo_user2@mail.com"
            }
        )
        updated_user = User.objects.get(id=self.user2.id)
        self.assertEqual(updated_user.email, "demo_user2@mail.com")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/activation_status.html')


class TestStudentDashboard(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

        # student
        self.student_plaintext_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # student without profile
        self.student_no_profile_plaintext_pass = 'student2'
        self.student_no_profile = User.objects.create_user(
            username='student_no_profile',
            password=self.student_no_profile_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student_no_profile@test.com'
        )

        # moderator
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
            )

        self.hidden_course = Course.objects.create(
            name="Hidden Course", enrollment="Enroll Request",
            creator=self.user, code="hide", hidden=True
            )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_student_dashboard_denies_anonymous_user(self):
        """
            Check student dashboard denies anonymous user
        """
        response = self.client.get(reverse('yaksh:quizlist_user'),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 200)
        redirection_url = '/exam/login/?next=/exam/quizzes/'
        self.assertRedirects(response, redirection_url)

    def test_student_dashboard_get_for_user_without_profile(self):
        """
        If no profile exists a blank profile form will be displayed
        """
        self.client.login(
            username=self.student_no_profile.username,
            password=self.student_no_profile_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:quizlist_user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/editprofile.html')

    def test_student_dashboard_get_for_user_with_profile(self):
        """
        If profile exists a editprofile.html template will be rendered
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:quizlist_user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/quizzes_user.html')

    def test_student_dashboard_all_courses_get(self):
        """
            Check student dashboard for all non hidden courses
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:quizlist_user'),
                                   follow=True
                                   )
        courses_in_context = {
            'data': self.course,
            'completion_percentage': None,
        }
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/quizzes_user.html")
        self.assertEqual(response.context['title'], 'All Courses')
        self.assertEqual(response.context['courses'][0], courses_in_context)

    def test_student_dashboard_hidden_courses_post(self):
        """
            Get courses for student based on the course code
        """

        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.post(reverse('yaksh:quizlist_user'),
                                    data={'course_code': 'hide'}
                                    )
        courses_in_context = {
            'data': self.hidden_course,
            'completion_percentage': None,
        }
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/quizzes_user.html")
        self.assertEqual(response.context['title'], 'Search Results')
        self.assertEqual(response.context['courses'][0], courses_in_context)


class TestMonitor(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com',
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Open Enrollment", creator=self.user
            )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )
        self.learning_unit = LearningUnit.objects.create(
            order=1, type="quiz", quiz=self.quiz)
        self.learning_module = LearningModule.objects.create(
            order=1, name="test module", description="test",
            creator=self.user, check_prerequisite=False)
        self.learning_module.learning_unit.add(self.learning_unit.id)
        self.course.learning_module.add(self.learning_module)

        self.question = Question.objects.create(
            summary="Test_question", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user
            )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz,
            total_marks=1.0, fixed_question_order=str(self.question)
            )
        self.question_paper.fixed_questions.add(self.question)
        user_answer = "def add(a, b)\n\treturn a+b"
        self.new_answer = Answer(
            question=self.question, answer=user_answer,
            correct=True, error=json.dumps([])
            )
        self.new_answer.save()
        self.answerpaper = AnswerPaper.objects.create(
            user=self.student, question_paper=self.question_paper,
            attempt_number=1,
            start_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_time=datetime(2014, 10, 9, 10, 15, 15, 0, tzone),
            user_ip="127.0.0.1", status="completed", passed=True,
            percent=1, marks_obtained=1, course=self.course
            )
        self.answerpaper.answers.add(self.new_answer)
        self.answerpaper.questions_answered.add(self.question)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.course.delete()
        self.answerpaper.delete()
        self.question.delete()
        self.question_paper.delete()
        self.new_answer.delete()
        self.learning_module.delete()
        self.learning_unit.delete()
        self.mod_group.delete()

    def test_monitor_denies_student(self):
        """
            Check Monitor denies student
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:monitor'),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 404)

    def test_monitor_quiz_not_found(self):
        """
            Check if quiz is not found
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:monitor'),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 404)

    def test_monitor_display_quiz_results(self):
        """
            Check all the quiz results in monitor
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:monitor',
                    kwargs={'quiz_id': self.quiz.id,
                            'course_id': self.course.id}),
            follow=True
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/monitor.html")
        self.assertEqual(response.context['papers'][0], self.answerpaper)

    def test_get_quiz_user_data(self):
        """
            Check for getting user data for a quiz
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:user_data',
                    kwargs={'user_id': self.student.id,
                            'questionpaper_id': self.question_paper.id,
                            'course_id': self.course.id}),
            follow=True
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/user_data.html')
        self.assertEqual(response.context['data']['papers'][0],
                         self.answerpaper)
        self.assertEqual(response.context['data']['profile'],
                         self.student.profile)
        self.assertEqual(response.context['data']['user'], self.student)
        self.assertEqual(response.context['data']['questionpaperid'],
                         str(self.question_paper.id))


class TestGradeUser(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Open Enrollment", creator=self.user)

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )
        self.learning_unit = LearningUnit.objects.create(
            order=1, type="quiz", quiz=self.quiz)
        self.learning_module = LearningModule.objects.create(
            order=1, name="test module", description="test",
            creator=self.user, check_prerequisite=False)
        self.learning_module.learning_unit.add(self.learning_unit.id)
        self.course.learning_module.add(self.learning_module)

        self.question = Question.objects.create(
            summary="Test_question", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user
            )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz,
            total_marks=1.0, fixed_question_order=str(self.question.id)
            )
        self.question_paper.fixed_questions.add(self.question)
        user_answer = "def add(a, b)\n\treturn a+b"
        self.new_answer = Answer(
            question=self.question, answer=user_answer,
            correct=True, error=json.dumps([]), marks=0.5
            )
        self.new_answer.save()
        self.answerpaper = AnswerPaper.objects.create(
            user=self.student, question_paper=self.question_paper,
            attempt_number=1,
            start_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_time=datetime(2014, 10, 9, 10, 15, 15, 0, tzone),
            user_ip="127.0.0.1", status="completed", passed=True,
            marks_obtained=0.5, course=self.course
            )
        self.answerpaper.answers.add(self.new_answer)
        self.answerpaper.questions_answered.add(self.question)
        self.answerpaper.questions.add(self.question)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.course.delete()
        self.answerpaper.delete()
        self.question.delete()
        self.question_paper.delete()
        self.new_answer.delete()
        self.learning_module.delete()
        self.learning_unit.delete()

    def test_grade_user_denies_student(self):
        """
            Check Grade User denies student
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:grade_user'),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 404)

    def test_grade_user_display_quizzes(self):
        """
            Check all the available quizzes in grade user
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:grade_user'),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/grade_user.html")
        self.assertEqual(response.context['objects'][0], self.course)

    def test_grade_user_get_quiz_users(self):
        """
            Check all the available users in quiz in grade user
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:grade_user',
                    kwargs={"quiz_id": self.quiz.id,
                            'course_id': self.course.id}),
            follow=True
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/grade_user.html")
        self.assertEqual(response.context['users'][0]['user__first_name'],
                         self.student.first_name)
        self.assertEqual(response.context['quiz'], self.quiz)
        self.assertFalse(response.context['has_quiz_assignments'])

    def test_grade_user_get_quiz_user_data(self):
        """
            Check student attempts and answers
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:grade_user',
                    kwargs={"quiz_id": self.quiz.id,
                            "course_id": self.course.id,
                            "user_id": self.student.id}),
            follow=True
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/grade_user.html")
        self.assertFalse(response.context['has_user_assignments'])
        self.assertEqual(response.context['quiz_id'], str(self.quiz.id))
        self.assertEqual(response.context['user_id'], str(self.student.id))
        self.assertEqual(response.context['attempts'][0], self.answerpaper)

    def test_grade_user_update_user_marks(self):
        """
            Check update marks of student
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        self.client.get(reverse('yaksh:grade_user',
                                kwargs={"quiz_id": self.quiz.id,
                                        "course_id": self.course.id,
                                        "user_id": self.student.id}),
                        follow=True
                        )
        question_marks = "q{0}_marks".format(self.question.id)
        response = self.client.post(
            reverse(
                'yaksh:grade_user',
                kwargs={"quiz_id": self.quiz.id,
                        "user_id": self.student.id,
                        "course_id": self.course.id,
                        "attempt_number": self.answerpaper.attempt_number}
                ),
            data={question_marks: 1.0}
            )

        updated_ans_paper = AnswerPaper.objects.get(
            user=self.student, question_paper=self.question_paper,
            attempt_number=self.answerpaper.attempt_number
            )
        updated_ans = Answer.objects.get(question=self.question)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/grade_user.html")
        self.assertEqual(updated_ans.marks, 1.0)
        self.assertEqual(updated_ans_paper.marks_obtained, 1.0)


class TestDownloadAssignment(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)
        # Create Student 1
        self.student1_plaintext_pass = 'demo_student1'
        self.student1 = User.objects.create_user(
            username='demo_student1',
            password=self.student1_plaintext_pass,
            first_name='student1_first_name',
            last_name='student1_last_name',
            email='demo_student1@test.com'
        )

        # Create Student 2
        self.student2_plaintext_pass = 'demo_student2'
        self.student2 = User.objects.create_user(
            username='demo_student2',
            password=self.student2_plaintext_pass,
            first_name='student2_first_name',
            last_name='student2_last_name',
            email='demo_student2@test.com'
        )

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
            )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo_quiz', pass_criteria=40
        )
        self.learning_unit = LearningUnit.objects.create(
            order=1, type="quiz", quiz=self.quiz)
        self.learning_module = LearningModule.objects.create(
            order=1, name="test module", description="test",
            creator=self.user, check_prerequisite=False)
        self.learning_module.learning_unit.add(self.learning_unit.id)
        self.course.learning_module.add(self.learning_module)

        self.question = Question.objects.create(
            summary="Test_question", description="Assignment Upload",
            points=1.0, language="python", type="upload", user=self.user
            )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz,
            total_marks=1.0, fixed_question_order=str(self.question.id)
            )
        self.question_paper.fixed_questions.add(self.question)

        attempt = 1
        ip = '127.0.0.1'
        self.answerpaper1 = self.question_paper.make_answerpaper(
                self.student1, ip, attempt, self.course.id
            )

        self.answerpaper2 = self.question_paper.make_answerpaper(
                self.student2, ip, attempt, self.course.id
            )

        # create assignment file
        assignment_file1 = SimpleUploadedFile("file1.txt", b"Test")
        assignment_file2 = SimpleUploadedFile("file2.txt", b"Test")

        self.assignment1 = AssignmentUpload.objects.create(
            assignmentQuestion=self.question,
            assignmentFile=assignment_file1, answer_paper=self.answerpaper1
            )
        self.assignment2 = AssignmentUpload.objects.create(
            assignmentQuestion=self.question,
            assignmentFile=assignment_file2, answer_paper=self.answerpaper1
            )

        self.assignment1 = AssignmentUpload.objects.create(
            assignmentQuestion=self.question,
            assignmentFile=assignment_file1, answer_paper=self.answerpaper2
            )
        self.assignment2 = AssignmentUpload.objects.create(
            assignmentQuestion=self.question,
            assignmentFile=assignment_file2, answer_paper=self.answerpaper2
            )


    def test_download_assignment_denies_student(self):
        """
            Check download assignment denies student not enrolled in a course
        """
        self.client.login(
            username=self.student1.username,
            password=self.student1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_quiz_assignment',
                    kwargs={'quiz_id': self.quiz.id,
                            "course_id": self.course.id}),
            follow=True
            )
        self.assertEqual(response.status_code, 404)

    def test_download_assignment_per_quiz(self):
        """
            Check for download assignments per quiz
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_quiz_assignment',
                    kwargs={'quiz_id': self.quiz.id,
                            'course_id': self.course.id}),
            follow=True
            )
        file_name = "{0}_Assignment_files.zip".format(self.course.name)
        file_name = file_name.replace(" ", "_")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         "attachment; filename={0}".format(file_name))
        zip_file = string_io(response.content)
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        self.assertIsNone(zipped_file.testzip())
        self.assertIn('file1.txt', zipped_file.namelist()[0])
        self.assertIn('file2.txt', zipped_file.namelist()[1])
        zip_file.close()
        zipped_file.close()

    def test_download_assignment_per_user(self):
        """
            Check for download assignments per quiz
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_user_assignment',
                    kwargs={'quiz_id': self.quiz.id,
                            'question_id': self.question.id,
                            'user_id': self.student2.id,
                            'course_id': self.course.id
                            }),
            follow=True
            )
        file_name = "{0}.zip".format(self.student2.get_full_name())
        file_name = file_name.replace(" ", "_")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         "attachment; filename={0}".format(file_name))
        zip_file = string_io(response.content)
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        self.assertIsNone(zipped_file.testzip())
        self.assertIn('file1.txt', zipped_file.namelist()[0])
        zip_file.close()
        zipped_file.close()

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student1.delete()
        self.student2.delete()
        self.assignment1.delete()
        self.assignment2.delete()
        self.quiz.delete()
        self.learning_module.delete()
        self.learning_unit.delete()
        self.mod_group.delete()
        dir_name = f'Course_{self.course.id}'
        file_path = os.sep.join((settings.MEDIA_ROOT, dir_name))
        if os.path.exists(file_path):
            shutil.rmtree(file_path)
        self.course.delete()


class TestAddQuiz(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
            )

        self.module = LearningModule.objects.create(
            name="My test module", creator=self.user, description="Test"
            )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

        self.exercise = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            attempts_allowed=-1, time_between_attempts=0,
            is_exercise=True, description='demo exercise', creator=self.user
        )

        unit1 = LearningUnit.objects.create(
            type="quiz", quiz=self.quiz, order=1)
        unit2 = LearningUnit.objects.create(
            type="quiz", quiz=self.exercise, order=2)
        self.module.learning_unit.add(*[unit1.id, unit2.id])

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.exercise.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_add_quiz_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:add_quiz', kwargs={
                'course_id': self.course.id,
                'module_id': self.module.id
            }), follow=True)
        redirect_destination = (
            '/exam/login/?next=/exam/manage/addquiz/{0}/{1}/'.format(
                self.course.id, self.module.id
                )
            )
        self.assertRedirects(response, redirect_destination)

    def test_add_quiz_denies_non_moderator(self):
        """
        If not moderator in redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:add_quiz', kwargs={
                'course_id': self.course.id,
                'module_id': self.module.id
            }), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_add_quiz_get(self):
        """
        GET request to add question should display add quiz form
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:add_quiz', kwargs={
                'course_id': self.course.id,
                'module_id': self.module.id
            }))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/add_quiz.html')
        self.assertIsNotNone(response.context['form'])

    def test_add_quiz_post_existing_quiz(self):
        """
        POST request to add quiz should edit quiz if quiz exists
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        tzone = pytz.timezone('UTC')
        response = self.client.post(
            reverse('yaksh:edit_quiz', kwargs={
                'course_id': self.course.id,
                'module_id': self.module.id,
                'quiz_id': self.quiz.id
            }),
            data={
                'start_date_time': '2016-01-10 09:00:15',
                'end_date_time': '2016-01-15 09:00:15',
                'duration': 30,
                'active': False,
                'attempts_allowed': 5,
                'time_between_attempts': 1,
                'description': 'updated demo quiz',
                'pass_criteria': 40,
                'instructions': "Demo Instructions",
                'weightage': 1.0
            }
        )

        updated_quiz = Quiz.objects.get(id=self.quiz.id)
        self.assertEqual(
            updated_quiz.start_date_time,
            datetime(2016, 1, 10, 9, 0, 15, 0, tzone)
        )
        self.assertEqual(
            updated_quiz.end_date_time,
            datetime(2016, 1, 15, 9, 0, 15, 0, tzone)
        )
        self.assertEqual(updated_quiz.duration, 30)
        self.assertEqual(updated_quiz.active, False)
        self.assertEqual(updated_quiz.attempts_allowed, 5)
        self.assertEqual(updated_quiz.time_between_attempts, 1)
        self.assertEqual(updated_quiz.description, 'updated demo quiz')
        self.assertEqual(updated_quiz.pass_criteria, 40)

    def test_add_quiz_post_new_quiz(self):
        """
        POST request to add quiz should add new quiz if no quiz exists
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        tzone = pytz.timezone('UTC')
        response = self.client.post(
            reverse('yaksh:add_quiz',
                    kwargs={'course_id': self.course.id,
                            'module_id': self.module.id}),
            data={
                'start_date_time': '2016-01-10 09:00:15',
                'end_date_time': '2016-01-15 09:00:15',
                'duration': 50,
                'active': True,
                'attempts_allowed': -1,
                'time_between_attempts': 2,
                'description': 'new demo quiz',
                'pass_criteria': 50,
                'instructions': "Demo Instructions",
                'weightage': 1.0
            }
        )
        quiz_list = Quiz.objects.all().order_by('-id')
        new_quiz = quiz_list[0]
        self.assertEqual(
            new_quiz.start_date_time,
            datetime(2016, 1, 10, 9, 0, 15, 0, tzone)
        )
        self.assertEqual(
            new_quiz.end_date_time,
            datetime(2016, 1, 15, 9, 0, 15, 0, tzone)
        )
        self.assertEqual(new_quiz.duration, 50)
        self.assertEqual(new_quiz.active, True)
        self.assertEqual(new_quiz.attempts_allowed, -1)
        self.assertEqual(new_quiz.time_between_attempts, 2)
        self.assertEqual(new_quiz.description, 'new demo quiz')
        self.assertEqual(new_quiz.pass_criteria, 50)

    def test_add_exercise_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:add_exercise',
                    kwargs={'course_id': self.course.id,
                            'module_id': self.module.id}),
            follow=True
        )
        redirect = (
            '/exam/login/?next=/exam/manage/add_exercise/{0}/{1}/'.format(
                self.course.id, self.module.id
                )
            )
        self.assertRedirects(response, redirect)

    def test_add_exercise_denies_non_moderator(self):
        """
        If not moderator in redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:add_exercise',
                    kwargs={'course_id': self.course.id,
                            'module_id': self.module.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_add_exercise_get(self):
        """
        GET request to add exercise should display add exercise form
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:add_exercise',
                    kwargs={'course_id': self.course.id,
                            'module_id': self.module.id})
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/add_exercise.html')
        self.assertIsNotNone(response.context['form'])

    def test_add_exercise_post_existing_exercise(self):
        """
        POST request to edit exercise
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:edit_exercise', kwargs={
                'course_id': self.course.id,
                'module_id': self.module.id,
                'quiz_id': self.exercise.id
            }),
            data={
                'description': 'updated demo exercise',
                'active': True
            }
        )

        updated_exercise = Quiz.objects.get(id=self.exercise.id)
        self.assertEqual(updated_exercise.active, True)
        self.assertEqual(updated_exercise.duration, 1000)
        self.assertEqual(updated_exercise.attempts_allowed, -1)
        self.assertEqual(updated_exercise.time_between_attempts, 0)
        self.assertEqual(updated_exercise.description, 'updated demo exercise')
        self.assertEqual(updated_exercise.pass_criteria, 0)
        self.assertTrue(updated_exercise.is_exercise)

    def test_add_exercise_post_new_exercise(self):
        """
        POST request to add new exercise
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:add_exercise', kwargs={
                'course_id': self.course.id,
                'module_id': self.module.id
            }),
            data={
                'description': "Demo Exercise",
                'active': True
            }
        )
        quiz_list = Quiz.objects.all().order_by('-id')
        new_exercise = quiz_list[0]
        self.assertEqual(new_exercise.active, True)
        self.assertEqual(new_exercise.duration, 1000)
        self.assertEqual(new_exercise.attempts_allowed, -1)
        self.assertEqual(new_exercise.time_between_attempts, 0)
        self.assertEqual(new_exercise.description, 'Demo Exercise')
        self.assertEqual(new_exercise.pass_criteria, 0)
        self.assertTrue(new_exercise.is_exercise)


class TestAddAsModerator(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
        )

        self.mod_group.delete()

    def tearDown(self):
        self.client.logout()
        self.user.delete()

    def test_add_as_moderator_group_does_not_exist(self):
        """
        If group does not exist return 404
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:add_teacher',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        with self.assertRaises(Http404):
            add_as_moderator(self.user, 'moderator')


class TestToggleModerator(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')

        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Student',
            timezone='UTC',
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
            )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_toggle_for_moderator(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:toggle_moderator')
        )
        self.assertEqual(response.status_code, 302)
        self.assertEquals(self.user.groups.all().count(), 0)

    def test_toggle_for_student(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:toggle_moderator')
        )

        self.assertEqual(response.status_code, 404)


class TestAddTeacher(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')

        # Create User with no profile
        self.user_no_profile_plaintext_pass = 'demo_no_profile'
        self.user_no_profile = User.objects.create_user(
            username='demo_user_no_profile',
            password=self.user_no_profile_plaintext_pass,
            first_name='first_name_no_profile',
            last_name='last_name_no_profile',
            email='demo_no_profile@test.com'
        )

        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
            )

        self.pre_req_quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 2, 1, 5, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='pre requisite quiz', pass_criteria=40,
            creator=self.user
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.pre_req_quiz.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_add_teacher_denies_no_profile(self):
        """
        If not moderator redirect to login page
        """
        self.client.login(
            username=self.user_no_profile.username,
            password=self.user_no_profile_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:add_teacher',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_add_teacher_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:add_teacher',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/addteacher/{0}/'.format(
                self.course.id)
            )
        self.assertRedirects(response, redirect_destination)

    def test_add_teacher_denies_non_moderator(self):
        """
        If not moderator redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:add_teacher',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_add_teacher_get(self):
        """
        GET request to add teacher should display list of teachers
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:add_teacher',
                    kwargs={'course_id': self.course.id}
                    )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/addteacher.html')
        self.assertEqual(response.context['course'], self.course)

    def test_add_teacher_post(self):
        """
        POST request to add teacher should add teachers to a course
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        teacher_id_list = []

        for i in range(5):
            teacher = User.objects.create_user(
                username='demo_teacher{}'.format(i),
                password='demo_teacher_pass{}'.format(i),
                first_name='teacher_first_name{}'.format(i),
                last_name='teacher_last_name{}'.format(i),
                email='demo{}@test.com'.format(i)
            )

            Profile.objects.create(
                user=teacher,
                roll_number='T{}'.format(i),
                institute='IIT',
                department='Chemical',
                position='Teacher',
                timezone='UTC'
            )
            teacher_id_list.append(teacher.id)

        response = self.client.post(
            reverse('yaksh:add_teacher',
                    kwargs={'course_id': self.course.id}
                    ),
            data={'check': teacher_id_list}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/addteacher.html')
        self.assertEqual(response.context['status'], True)
        for t_id in teacher_id_list:
            teacher_object = User.objects.get(id=t_id)
            self.assertIn(teacher_object, response.context['teachers_added'])
            self.assertIn(teacher_object, self.course.teachers.all())


class TestRemoveTeacher(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')

        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user)

        self.pre_req_quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 2, 1, 5, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='pre requisite quiz', pass_criteria=40,
            creator=self.user
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.pre_req_quiz.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_remove_teacher_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:remove_teacher',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/remove_teachers/{0}/'.format(
                self.course.id)
            )
        self.assertRedirects(response, redirect_destination)

    def test_remove_teacher_denies_non_moderator(self):
        """
        If not moderator redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:remove_teacher',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_remove_teacher_post(self):
        """
        POST request should remove moderator from course
        """
        teacher_id_list = []
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        for i in range(5):
            teacher = User.objects.create_user(
                username='remove_teacher{}'.format(i),
                password='remove_teacher_pass{}'.format(i),
                first_name='remove_teacher_first_name{}'.format(i),
                last_name='remove_teacher_last_name{}'.format(i),
                email='remove_teacher{}@test.com'.format(i)
            )

            Profile.objects.create(
                user=teacher,
                roll_number='RT{}'.format(i),
                institute='IIT',
                department='Aeronautical',
                position='Teacher',
                timezone='UTC'
            )
            teacher_id_list.append(teacher.id)
            self.course.teachers.add(teacher)

        response = self.client.post(
            reverse('yaksh:remove_teacher',
                    kwargs={'course_id': self.course.id}
                    ),
            data={'remove': teacher_id_list}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.course.teachers.filter(id__in=teacher_id_list).exists()
        )


class TestCourses(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='user1_first_name',
            last_name='user1_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.user2_plaintext_pass = 'demo2'
        self.user2 = User.objects.create_user(
            username='demo_user2',
            password=self.user2_plaintext_pass,
            first_name='user2_first_name',
            last_name='user2_last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.user2,
            roll_number=10,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )
        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC'
        )

        self.teacher_plaintext_pass = 'teacher'
        self.teacher = User.objects.create_user(
            username='teacher',
            password=self.teacher_plaintext_pass,
            first_name='teacher_first_name',
            last_name='teacher_last_name',
            email='demo_teacher@test.com'
        )

        Profile.objects.create(
            user=self.teacher,
            roll_number=10,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)
        self.mod_group.user_set.add(self.user2)
        self.mod_group.user_set.add(self.teacher)

        # Create a learning module to add to course
        self.learning_module = LearningModule.objects.create(
            order=0, name="test module", description="module",
            check_prerequisite=True, creator=self.teacher)

        self.user1_course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user1)

        # Create Learning Module for Python Course
        self.learning_module1 = LearningModule.objects.create(
            order=0, name="demo module", description="module",
            check_prerequisite=False, creator=self.user1)

        self.quiz = Quiz.objects.create(
            time_between_attempts=0, description='demo quiz',
            creator=self.user1)
        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=1.0)
        self.lesson = Lesson.objects.create(
            name="demo lesson", description="test description",
            creator=self.user1)
        lesson_file = SimpleUploadedFile("file1.mp4", b"Test")
        django_file = File(lesson_file)
        self.lesson.video_file.save(lesson_file.name, django_file,
                                    save=True)

        self.lesson_unit = LearningUnit.objects.create(
            order=1, type="lesson", lesson=self.lesson)
        self.quiz_unit = LearningUnit.objects.create(
            order=2, type="quiz", quiz=self.quiz)

        # Add units to module
        self.learning_module1.learning_unit.add(self.lesson_unit)
        self.learning_module1.learning_unit.add(self.quiz_unit)

        # Add teacher to user1 course
        self.user1_course.teachers.add(self.teacher)

        self.user2_course = Course.objects.create(
            name="Java Course",
            enrollment="Enroll Request", creator=self.user2)
        self.user2_course.learning_module.add(self.learning_module)

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.user2.delete()
        self.student.delete()
        self.teacher.delete()
        self.mod_group.delete()

    def test_courses_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(reverse('yaksh:courses'), follow=True)
        redirect_destination = ('/exam/login/?next=/exam/manage/courses/')
        self.assertRedirects(response, redirect_destination)

    def test_courses_denies_non_moderator(self):
        """
        If not moderator redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(reverse('yaksh:courses'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_courses_get(self):
        """
        GET request should return courses page
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:courses'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/courses.html')
        self.assertIn(self.user1_course, response.context['courses'])
        self.assertNotIn(self.user2_course, response.context['courses'])

    def test_teacher_can_design_course(self):
        """ Check if teacher can design the course i.e add learning modules """
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:design_course',
                    kwargs={"course_id": self.user1_course.id}),
            data={"Add": "Add",
                  "module_list": [str(self.learning_module.id)]
                  })

        # Test add learning module
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/design_course_session.html')
        added_learning_module = self.user1_course.learning_module.all().first()
        self.assertEqual(self.learning_module, added_learning_module)
        self.assertEqual(added_learning_module.order, 1)

        # Test change order of learning module
        response = self.client.post(
            reverse('yaksh:design_course',
                    kwargs={"course_id": self.user1_course.id}),
            data={"Change": "Change", "ordered_list": ",".join(
                [str(self.learning_module.id)+":"+"0"]
                )}
        )
        updated_learning_module = LearningModule.objects.get(
            id=self.learning_module.id)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/design_course_session.html')
        self.assertEqual(updated_learning_module.order, 0)

        # Test change check prerequisite
        response = self.client.post(
            reverse('yaksh:design_course',
                    kwargs={"course_id": self.user1_course.id}),
            data={"Change_prerequisite": "Change_prerequisite",
                  "check_prereq": [str(self.learning_module.id)]
                  })
        updated_learning_module = LearningModule.objects.get(
            id=self.learning_module.id)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/design_course_session.html')
        self.assertTrue(updated_learning_module.check_prerequisite)

        # Test to remove learning module from course
        response = self.client.post(
            reverse('yaksh:design_course',
                    kwargs={"course_id": self.user1_course.id}),
            data={"Remove": "Remove",
                  "delete_list": [str(self.learning_module.id)]
                  })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/design_course_session.html')
        self.assertFalse(self.user1_course.learning_module.all().exists())

    def test_get_course_modules(self):
        """ Test to check if student gets course modules """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:course_modules',
                    kwargs={"course_id": self.user1_course.id}),
            follow=True
        )
        # Student is not allowed if not enrolled in the course
        err_msg = "You are not enrolled for this course!"
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0], err_msg)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/quizzes_user.html")

        # enroll student in the course
        self.user1_course.students.add(self.student)
        # deactivate the course and check if student is able to view course
        self.user1_course.active = False
        self.user1_course.save()
        response = self.client.get(
            reverse('yaksh:course_modules',
                    kwargs={"course_id": self.user1_course.id}),
            follow=True
        )
        err_msg = "{0} is either expired or not active".format(
            self.user1_course.name)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0], err_msg)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/quizzes_user.html")

        # activate the course and check if students gets course modules
        self.user1_course.active = True
        self.user1_course.save()
        self.user1_course.learning_module.add(self.learning_module)
        response = self.client.get(
            reverse('yaksh:course_modules',
                    kwargs={"course_id": self.user1_course.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/course_modules.html")
        self.assertEqual(response.context['course'], self.user1_course)
        module, percent = response.context['modules'][0]
        self.assertEqual(module, self.learning_module)
        self.assertEqual(percent, 0.0)

    def test_duplicate_course(self):
        """ Test To clone/duplicate course and link modules"""

        # Student Login
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:duplicate_course',
                    kwargs={"course_id": self.user2_course.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

        # Teacher Login
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )

        # Denies teacher not added in the course
        response = self.client.get(
            reverse('yaksh:duplicate_course',
                    kwargs={"course_id": self.user2_course.id}),
            follow=True
        )
        err_msg = "You do not have permissions"
        self.assertEqual(response.status_code, 200)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(err_msg, messages[0])

        # Test clone/duplicate courses and create copies of modules and units

        # Teacher Login
        # Given
        # Add files to a lesson
        file_content = b"Test"
        lesson_file = SimpleUploadedFile("file1.txt", file_content)
        django_file = File(lesson_file)
        lesson_file_obj = LessonFile()
        lesson_file_obj.lesson = self.lesson
        lesson_file_obj.file.save(lesson_file.name, django_file, save=True)

        # Add module to Python Course
        self.user1_course.learning_module.add(self.learning_module1)
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:duplicate_course',
                    kwargs={"course_id": self.user1_course.id}),
            follow=True
        )

        # When
        courses = Course.objects.filter(
            creator=self.teacher).order_by("id")
        module = courses.last().get_learning_modules()[0]
        units = module.get_learning_units()
        cloned_lesson = units[0].lesson
        cloned_quiz = units[1].quiz
        expected_lesson_files = cloned_lesson.get_files()
        actual_lesson_files = self.lesson.get_files()
        cloned_qp = cloned_quiz.questionpaper_set.get()
        self.all_files = LessonFile.objects.filter(
            lesson_id__in=[self.lesson.id, cloned_lesson.id])

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertEqual(courses.last().creator, self.teacher)
        self.assertEqual(courses.last().name, "Copy Of Python Course")
        self.assertEqual(module.name, "demo module")
        self.assertEqual(module.creator, self.teacher)
        self.assertEqual(module.order, 0)
        self.assertEqual(len(units), 2)
        self.assertEqual(cloned_lesson.name, "demo lesson")
        self.assertEqual(cloned_lesson.creator, self.teacher)
        self.assertEqual(cloned_quiz.description, "demo quiz")
        self.assertEqual(cloned_quiz.creator, self.teacher)
        self.assertEqual(cloned_qp.__str__(),
                         "Question Paper for demo quiz")
        self.assertTrue(expected_lesson_files.exists())
        self.assertEquals(expected_lesson_files[0].file.read(), file_content)

        self.all_files.delete()

    def test_download_course_offline(self):
        """ Test to download course with lessons offline"""

        # Student fails to download course if not enrolled in that course
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_course',
                    kwargs={"course_id": self.user1_course.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

        # Teacher/Moderator should be able to download course
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )

        # Should not allow to download if the course doesn't have lessons
        self.user1_course.learning_module.add(self.learning_module)
        response = self.client.get(
            reverse('yaksh:download_course',
                    kwargs={"course_id": self.user1_course.id}),
            follow=True
        )
        self.user1_course.learning_module.remove(self.learning_module)
        self.assertEqual(response.status_code, 404)
        lesson_file = SimpleUploadedFile("file1.txt", b"Test")
        django_file = File(lesson_file)
        lesson_file_obj = LessonFile()
        lesson_file_obj.lesson = self.lesson
        lesson_file_obj.file.save(lesson_file.name, django_file, save=True)
        self.user1_course.learning_module.add(self.learning_module1)
        response = self.client.get(
            reverse('yaksh:download_course',
                    kwargs={"course_id": self.user1_course.id}),
            follow=True
        )
        course_name = self.user1_course.name.replace(" ", "_")
        self.assertEqual(response.status_code, 200)
        zip_file = string_io(response.content)
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        self.assertIsNone(zipped_file.testzip())
        files_in_zip = zipped_file.namelist()
        module_path = os.path.join(course_name, "demo_module",
                                   "demo_module.html")
        lesson_path = os.path.join(course_name, "demo_module", "demo_lesson",
                                   "demo_lesson.html")
        self.assertIn(module_path, files_in_zip)
        self.assertIn(lesson_path, files_in_zip)
        zip_file.close()
        zipped_file.close()
        self.user1_course.learning_module.remove(self.learning_module1)


class TestSearchFilters(TestCase):
    def setUp(self):
        self.client = Client()

        # Create moderator group
        self.mod_group = Group.objects.create(name="moderator")

        # Create user1 with profile
        self.user1_plaintext_pass = "demo1"
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='user1_first_name',
            last_name='user1_last_name',
            email='demo1@test.com'
        )
        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute="IIT",
            department="Chemical",
            position="moderator",
            timezone="UTC",
            is_moderator=True
            )

        # Add user1 to moderator group
        self.mod_group.user_set.add(self.user1)

        # Create courses for user1
        self.user1_course1 = Course.objects.create(
            name="Demo Course",
            enrollment="Enroll Request", creator=self.user1)
        self.user1_course2 = Course.objects.create(
            name="Test Course",
            enrollment="Enroll Request", creator=self.user1)

        # Create learning modules for user1
        self.learning_module1 = LearningModule.objects.create(
            order=0, name="Demo Module", description="Demo Module",
            check_prerequisite=False, creator=self.user1)
        self.learning_module2 = LearningModule.objects.create(
            order=0, name="Test Module", description="Test Module",
            check_prerequisite=False, creator=self.user1)

        # Create quizzes for user1
        self.quiz1 = Quiz.objects.create(
            time_between_attempts=0, description='Demo Quiz',
            creator=self.user1)
        self.question_paper1 = QuestionPaper.objects.create(
            quiz=self.quiz1, total_marks=1.0)

        self.quiz2 = Quiz.objects.create(
            time_between_attempts=0, description='Test Quiz',
            creator=self.user1)
        self.question_paper2 = QuestionPaper.objects.create(
            quiz=self.quiz2, total_marks=1.0)

        # Create lessons for user1
        self.lesson1 = Lesson.objects.create(
            name="Demo Lesson", description="Demo Lession",
            creator=self.user1)
        self.lesson2 = Lesson.objects.create(
            name="Test Lesson", description="Test Lesson",
            creator=self.user1)

        # Create units for lesson and quiz
        self.lesson_unit1 = LearningUnit.objects.create(
            order=1, type="lesson", lesson=self.lesson1)
        self.lesson_unit2 = LearningUnit.objects.create(
            order=1, type="lesson", lesson=self.lesson2)
        self.quiz_unit1 = LearningUnit.objects.create(
            order=2, type="quiz", quiz=self.quiz1)
        self.quiz_unit2 = LearningUnit.objects.create(
            order=2, type="quiz", quiz=self.quiz2)

        # Add units to module
        self.learning_module1.learning_unit.add(self.lesson_unit1)
        self.learning_module1.learning_unit.add(self.quiz_unit1)
        self.learning_module2.learning_unit.add(self.lesson_unit2)
        self.learning_module2.learning_unit.add(self.quiz_unit2)

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.mod_group.delete()

    def test_courses_search_filter(self):
        """ Test to check if courses are obtained with tags and status """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:courses'),
            data={'search_tags': 'demo', 'search_status': 'active'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/courses.html')
        self.assertIsNotNone(response.context['form'])
        self.assertIn(self.user1_course1, response.context['courses'])


class TestAddCourse(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')

        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create a teacher
        self.teacher_plaintext_pass = 'demo_teacher'
        self.teacher = User.objects.create_user(
            username='demo_teacher',
            password=self.teacher_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.teacher,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)
        self.mod_group.user_set.add(self.teacher)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user)

        self.course.teachers.add(self.teacher)

        self.pre_req_quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 2, 1, 5, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='pre requisite quiz', pass_criteria=40,
            creator=self.user
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.pre_req_quiz.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_add_course_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(reverse('yaksh:add_course'),
                                   follow=True
                                   )
        redirect_destination = ('/exam/login/?next=/exam/manage/add_course/')
        self.assertRedirects(response, redirect_destination)

    def test_add_course_denies_non_moderator(self):
        """
        If not moderator in redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:add_course'), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_add_course_get(self):
        """
        GET request to add course should display add course form
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:add_course'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/add_course.html')
        self.assertIsNotNone(response.context['form'])

    def test_add_course_post_new_course(self):
        """
        POST request to add course should add new courses if no course exists
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        response = self.client.post(
            reverse('yaksh:add_course'),
            data={'name': 'new_demo_course_1',
                  'active': True,
                  'enrollment': 'open',
                  'start_enroll_time': '2016-01-10 09:00:15',
                  'end_enroll_time': '2016-01-15 09:00:15',
                  }
        )
        new_course = Course.objects.latest('created_on')
        self.assertEqual(new_course.name, 'new_demo_course_1')
        self.assertEqual(new_course.enrollment, 'open')
        self.assertEqual(new_course.active, True)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exam/manage/courses',
                             target_status_code=301)

    def test_add_course_teacher_cannot_be_creator(self):
        """
        Teacher editing the course should not become creator
        """
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )

        response = self.client.post(
            reverse('yaksh:edit_course',
                    kwargs={"course_id": self.course.id}),
            data={'name': 'Teacher_course',
                  'active': True,
                  'enrollment': 'open',
                  'start_enroll_time': '2016-01-10 09:00:15',
                  'end_enroll_time': '2016-01-15 09:00:15',
                  }
        )
        updated_course = Course.objects.get(id=self.course.id)
        self.assertEqual(updated_course.name, 'Teacher_course')
        self.assertEqual(updated_course.enrollment, 'open')
        self.assertEqual(updated_course.active, True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(updated_course.creator, self.user)
        self.assertRedirects(response, '/exam/manage/courses',
                             target_status_code=301)


class TestUploadMarks(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')

        # Create Moderator with profile
        self.teacher = User.objects.create_user(
            username='teacher',
            password='teacher',
            first_name='teacher',
            last_name='teaacher',
            email='teacher@test.com'
        )

        Profile.objects.create(
            user=self.teacher,
            roll_number=101,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.TA = User.objects.create_user(
            username='TA',
            password='TA',
            first_name='TA',
            last_name='TA',
            email='TA@test.com'
        )

        Profile.objects.create(
            user=self.TA,
            roll_number=102,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student1 = User.objects.create_user(
            username='student1',
            password='student1',
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student1@test.com'
        )
        self.student2 = User.objects.create_user(
            username='student2',
            password='student2',
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student2@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.teacher)
        self.mod_group.user_set.add(self.TA)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.teacher
        )

        self.question1 = Question.objects.create(
            id=1212, summary='Dummy1', points=1,
            type='code', user=self.teacher
        )
        self.question2 = Question.objects.create(
            id=1213, summary='Dummy2', points=1,
            type='code', user=self.teacher
        )

        self.quiz = Quiz.objects.create(time_between_attempts=0,
                                        description='demo quiz')
        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=2.0
        )
        self.question_paper.fixed_questions.add(self.question1)
        self.question_paper.fixed_questions.add(self.question2)
        self.question_paper.save()

        self.ans_paper1 = AnswerPaper.objects.create(
            user=self.student1, attempt_number=1,
            question_paper=self.question_paper, start_time=timezone.now(),
            user_ip='101.0.0.1', course=self.course,
            end_time=timezone.now()+timezone.timedelta(minutes=20)
        )
        self.ans_paper2 = AnswerPaper.objects.create(
            user=self.student2, attempt_number=1,
            question_paper=self.question_paper, start_time=timezone.now(),
            user_ip='101.0.0.1', course=self.course,
            end_time=timezone.now()+timezone.timedelta(minutes=20)
        )
        self.answer1 = Answer(
            question=self.question1, answer="answer1",
            correct=False, error=json.dumps([]), marks=0
        )
        self.answer2 = Answer(
            question=self.question2, answer="answer2",
            correct=False, error=json.dumps([]), marks=0
        )
        self.answer12 = Answer(
            question=self.question1, answer="answer12",
            correct=False, error=json.dumps([]), marks=0
        )
        self.answer1.save()
        self.answer12.save()
        self.answer2.save()
        self.ans_paper1.answers.add(self.answer1)
        self.ans_paper1.answers.add(self.answer2)
        self.ans_paper2.answers.add(self.answer12)
        self.ans_paper1.questions_answered.add(self.question1)
        self.ans_paper1.questions_answered.add(self.question2)
        self.ans_paper2.questions_answered.add(self.question1)
        self.ans_paper1.questions.add(self.question1)
        self.ans_paper1.questions.add(self.question2)
        self.ans_paper2.questions.add(self.question1)
        self.ans_paper2.questions.add(self.question2)

    def tearDown(self):
        self.client.logout()
        self.student1.delete()
        self.student2.delete()
        self.TA.delete()
        self.teacher.delete()
        self.course.delete()
        self.ans_paper1.delete()
        self.ans_paper2.delete()
        self.question_paper.delete()
        self.quiz.delete()
        self.question1.delete()
        self.question2.delete()
        self.mod_group.delete()

    def test_upload_users_marks_not_attempted_question(self):
        # Given
        self.client.login(
            username=self.teacher.username,
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "marks_not_attempted_question.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        ans_paper = AnswerPaper.objects.get(user=self.student2,
                                            question_paper=self.question_paper,
                                            course=self.course)
        self.assertEqual(ans_paper.marks_obtained, 1.3)
        answer = Answer.objects.get(answer='answer12')
        self.assertEqual(answer.comment.strip(), 'very good')

    def test_upload_users_marks_invalid_question_id(self):
        # Given
        self.client.login(
            username=self.teacher.username,
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "marks_invalid_question_id.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)

    def test_upload_users_marks_invalid_user(self):
        # Given
        self.client.login(
            username=self.teacher.username,
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "marks_invalid_user.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)

    def test_upload_users_marks_invalid_data(self):
        # Given
        self.client.login(
            username=self.teacher.username,
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "marks_invalid_data.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)

    def test_upload_users_marks_headers_missing(self):
        # Given
        self.client.login(
            username=self.teacher.username,
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "marks_header_missing.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        ans_paper = AnswerPaper.objects.get(user=self.student1,
                                            question_paper=self.question_paper,
                                            course=self.course)
        self.assertEqual(ans_paper.marks_obtained, 0.9)

    def test_upload_users_marks_headers_modified(self):
        # Given
        self.client.login(
            username=self.teacher.username,
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "marks_header_modified.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        answer = Answer.objects.get(answer='answer1')
        self.assertEqual(answer.comment.strip(), 'fine work')
        self.assertNotEqual(answer.marks, 0.75)
        answer = Answer.objects.get(answer='answer2')
        self.assertEqual(answer.comment.strip(), 'not nice')

    def test_upload_users_marks_csv_single_question(self):
        # Given
        self.client.login(
            username=self.teacher.username,
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "marks_single_question.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        ans_paper = AnswerPaper.objects.get(user=self.student1,
                                            question_paper=self.question_paper,
                                            course=self.course)
        self.assertEqual(ans_paper.marks_obtained, 0.5)
        answer = Answer.objects.get(answer='answer1')
        self.assertEqual(answer.comment.strip(), 'okay work')

    def test_upload_users_with_correct_csv(self):
        # Given
        self.client.login(
            username=self.teacher.username,
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH, "marks_correct.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        ans_paper = AnswerPaper.objects.get(user=self.student1,
                                            question_paper=self.question_paper,
                                            course=self.course)
        self.assertEqual(ans_paper.marks_obtained, 2)
        answer = Answer.objects.get(answer='answer1')
        self.assertEqual(answer.comment.strip(), 'good work')

    def test_upload_users_with_wrong_csv(self):
        # Given
        self.client.login(
            username='teacher',
            password='teacher'
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH, "demo_questions.zip")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())
        message = "The file uploaded is not a CSV file."

        # When
        response = self.client.post(
            reverse('yaksh:upload_marks',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual('The file uploaded is not a CSV file.', messages[0])


class TestCourseDetail(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')

        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='user1_first_name',
            last_name='user1_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.user2_plaintext_pass = 'demo2'
        self.user2 = User.objects.create_user(
            username='demo_user2',
            password=self.user2_plaintext_pass,
            first_name='user2_first_name',
            last_name='user2_last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.user2,
            roll_number=10,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )
        self.student1_plaintext_pass = 'demo_student1'
        self.student1 = User.objects.create_user(
            username='demo_student1',
            password=self.student1_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student1@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)
        self.mod_group.user_set.add(self.user2)

        self.user1_course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user1
            )

        self.user1_othercourse = Course.objects.create(
            name="Python Course II",
            enrollment="Enroll Request", creator=self.user1
            )

        self.user1_deactive_course = Course.objects.create(
            name="Python Course II",
            enrollment="Enroll Request",
            creator=self.user1,
            end_enroll_time=timezone.now()
        )

        self.learning_module = LearningModule.objects.create(
            name="test module", description="test description module",
            html_data="test html description module", creator=self.user1,
            order=1)
        self.user1_course.learning_module.add(self.learning_module)
        self.lesson = Lesson.objects.create(
            name="test lesson", description="test description",
            creator=self.user1)
        self.learning_unit1 = LearningUnit.objects.create(
            order=1, type="lesson", lesson=self.lesson)
        self.learning_module.learning_unit.add(self.learning_unit1)

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.user2.delete()
        self.student.delete()
        self.user1_course.delete()
        self.user1_othercourse.delete()
        self.mod_group.delete()

    def test_upload_users_with_correct_csv(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH, "users_correct.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        uploaded_user = User.objects.filter(email="abc@xyz.com")
        self.assertEqual(uploaded_user.count(), 1)
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("abc@xyz.com", messages[0])
        self.assertIn(uploaded_user.first(), self.user1_course.students.all())

    def test_upload_existing_user(self):
        # Given
        self.client.login(
            username=self.user1.username, password=self.user1_plaintext_pass)
        csv_file_path = os.path.join(FIXTURES_DIR_PATH, 'existing_user.csv')
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())
        csv_file.close()

        # When
        response = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file})

        # Then
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("demo_user2", messages[0])
        self.assertIn(self.user2, self.user1_course.students.all())

    def test_upload_same_user_multiple_course(self):
        # Given
        self.client.login(
            username=self.user1.username, password=self.user1_plaintext_pass)
        csv_file_path = os.path.join(FIXTURES_DIR_PATH, 'users_correct.csv')
        csv_file = open(csv_file_path, 'rb')
        upload_file1 = SimpleUploadedFile(csv_file_path, csv_file.read())
        csv_file.seek(0)
        upload_file2 = SimpleUploadedFile(csv_file_path, csv_file.read())
        csv_file.close()

        # When
        response1 = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file1})

        response2 = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_othercourse.id}),
            data={'csv_file': upload_file2})

        # Then
        uploaded_users = User.objects.filter(email='abc@xyz.com')
        self.assertEqual(response1.status_code, 302)
        messages1 = [m.message for m in get_messages(response1.wsgi_request)]
        self.assertIn('abc@xyz.com', messages1[0])
        self.assertEqual(response2.status_code, 302)
        messages2 = [m.message for m in get_messages(response2.wsgi_request)]
        self.assertIn('abc@xyz.com', messages2[0])
        self.assertIn('abc@xyz.com', messages2[1])
        self.assertTrue(
            self.user1_course.students.filter(
                id=uploaded_users.first().id).exists()
        )
        self.assertTrue(
            self.user1_othercourse.students.filter(
                id=uploaded_users.first().id).exists()
        )

    def test_upload_existing_user_email(self):
        # Given
        self.client.login(
            username=self.user1.username, password=self.user1_plaintext_pass)
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     'user_existing_email.csv')
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())
        csv_file.close()

        # When
        response = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file})

        # Then
        uploaded_users = User.objects.filter(email='demo_student@test.com')
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('demo_student', messages[0])
        self.assertTrue(
            self.user1_course.students.filter(
                id=uploaded_users.first().id).exists()
        )
        self.assertEqual(uploaded_users.count(), 1)

    def test_upload_users_add_update_reject(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "users_add_update_reject.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        uploaded_user = User.objects.filter(username="test2")
        user = uploaded_user[0]
        self.assertEqual(uploaded_user.count(), 1)
        self.assertEqual(user.first_name, "test2")
        self.assertIn(user, self.user1_course.get_rejected())
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('test2', messages[2])
        self.assertIn('User rejected', messages[2])

    def test_upload_users_with_wrong_csv(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH, "demo_questions.zip")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())
        message = "The file uploaded is not a CSV file."

        # When
        response = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual('The file uploaded is not a CSV file.', messages[0])

    def test_upload_users_csv_with_missing_headers(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "users_some_headers_missing.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())
        message = "The CSV file does not contain the required headers"

        # When
        response = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            'The CSV file does not contain the required headers', messages[0]
        )

    def test_upload_users_csv_with_no_values(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "users_with_no_values.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file})
        csv_file.close()

        # Then
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("No rows in the CSV file", messages[0])

    def test_upload_users_csv_with_missing_values(self):
        '''
            This test takes csv with 3 row values.
            1st row has a missing row.
            2nd has a proper row.
            3rd has a same row has 2nd

            Only 2nd user will be added.

            This test proves that:
            - Row with missing values is ignored and continued with next row.
            - Duplicate user is not created.
        '''
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                     "users_some_values_missing.csv")
        csv_file = open(csv_file_path, 'rb')
        upload_file = SimpleUploadedFile(csv_file_path, csv_file.read())

        # When
        response = self.client.post(
            reverse('yaksh:upload_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'csv_file': upload_file}
            )
        csv_file.close()

        # Then
        uploaded_user = User.objects.filter(email="dummy@xyz.com")
        self.assertEqual(uploaded_user.count(), 1)
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Missing Values", messages[0])

    def test_course_detail_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:course_detail',
                    kwargs={'course_id': self.user1_course.id}
                    ),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/course_detail/{0}/'.format(
                self.user1_course.id)
            )
        self.assertRedirects(response, redirect_destination)

    def test_course_detail_denies_non_moderator(self):
        """
        If not moderator redirect to 404
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:course_detail',
                    kwargs={'course_id': self.user1_course.id}
                    ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_course_detail_denies_unrelated_moderators(self):
        """
        If not creator of course or related teacher redirect to 404
        """
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:course_detail',
                    kwargs={'course_id': self.user1_course.id}
                    ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_course_detail_get(self):
        """
        If not creator of course or related teacher redirect to 404
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:course_detail',
                    kwargs={'course_id': self.user1_course.id}
                    ),
            follow=True
        )
        self.assertEqual(self.user1_course, response.context['course'])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/course_detail.html')

    def test_student_course_enroll_get(self):
        """
            Enroll student in a course using get request
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:enroll_user',
                    kwargs={'course_id': self.user1_course.id,
                            'user_id': self.student.id})
                    )
        enrolled_student = self.user1_course.students.all()
        self.assertEqual(response.status_code, 302)
        self.assertSequenceEqual([self.student], enrolled_student)

    def test_student_course_enroll_post(self):
        """
            Enroll student in a course using post request
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id
        })
        data = {
            'check': self.student1.id,
            'enroll': 'enroll'
        }
        response = self.client.post(url, data)
        enrolled_student = self.user1_course.students.all()
        self.assertEqual(response.status_code, 302)
        self.assertSequenceEqual([self.student1], enrolled_student)

    def test_student_course_enroll_post_without_enroll_in_request(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id
        })
        data = {
            'check': self.student1.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_student_course_enroll_post_without_enroll_ids(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id
        })
        data = {
            'enroll': 'enroll'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_student_course_reject_post_without_reject_in_request(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id
        })
        data = {
            'check': self.student1.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_student_course_reject_post_without_reject_ids(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id
        })
        data = {
            'reject': 'reject'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_student_course_reject_get(self):
        """
            Reject student in a course using get request
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:reject_user',
                    kwargs={'course_id': self.user1_course.id,
                            'user_id': self.student.id})
                    )
        enrolled_student = self.user1_course.rejected.all()
        self.assertEqual(response.status_code, 302)
        self.assertSequenceEqual([self.student], enrolled_student)

    def test_student_course_reject_post(self):
        """
            Reject student in a course using post request
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id
        })
        data = {
            'check': self.student1.id,
            'reject': 'reject'
        }
        response = self.client.post(url, data)
        enrolled_student = self.user1_course.rejected.all()
        self.assertEqual(response.status_code, 302)
        self.assertSequenceEqual([self.student1], enrolled_student)

    def test_enroll_user_not_moderator(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        url = reverse('yaksh:enroll_user', kwargs={
            'course_id': self.user1_course.id,
            'user_id': self.user1.id
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_enroll_user_in_expired_course(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_user', kwargs={
            'course_id': self.user1_deactive_course.id,
            'user_id': self.student.id
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_enroll_user_where_moderator_is_neither_creator_nor_teacher(self):
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        url = reverse('yaksh:enroll_user', kwargs={
            'course_id': self.user1_course.id,
            'user_id': self.user1.id
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_reject_user_not_moderator(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        url = reverse('yaksh:reject_user', kwargs={
            'course_id': self.user1_course.id,
            'user_id': self.user1.id
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_reject_user_where_moderator_is_neither_creator_nor_teacher(self):
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        url = reverse('yaksh:reject_user', kwargs={
            'course_id': self.user1_course.id,
            'user_id': self.user1.id
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_enroll_reject_user_not_moderator(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_enroll_reject_user_in_deactivated_course(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_deactive_course.id,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_enroll_reject_user_where_moderator_is_neither_creator_nor_teacher(
            self):
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_enroll_reject_user_view(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:enroll_reject_user', kwargs={
            'course_id': self.user1_course.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_toggle_course_status_get(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:toggle_course_status',
                    kwargs={'course_id': self.user1_course.id})
            )
        self.assertEqual(response.status_code, 302)
        course = Course.objects.get(name="Python Course")
        self.assertFalse(course.active)
        self.assertRedirects(response, '/exam/manage/courses',
                             target_status_code=301)

    def test_send_mail_to_course_students(self):
        """ Check if bulk mail is sent to multiple students enrolled
            in a course
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        self.student2 = User.objects.create_user(
            username='demo_student2',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student2@test.com'
        )
        self.student3 = User.objects.create_user(
            username='demo_student3',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student3@test.com'
        )
        self.student4 = User.objects.create_user(
            username='demo_student4',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student4@test.com'
        )
        user_ids = [self.student.id, self.student2.id, self.student3.id,
                    self.student4.id]
        user_emails = [self.student.email, self.student2.email,
                       self.student3.email, self.student4.email]

        self.user1_course.students.add(*user_ids)
        attachment = SimpleUploadedFile("file.txt", b"Test")
        email_data = {
            'send_mail': 'send_mail', 'email_attach': [attachment],
            'subject': 'test_bulk_mail', 'body': 'Test_Mail',
            'check': user_ids
        }
        self.client.post(reverse(
            'yaksh:send_mail', kwargs={'course_id': self.user1_course.id}),
            data=email_data
        )
        attachment_file = mail.outbox[0].attachments[0][0]
        subject = mail.outbox[0].subject
        body = mail.outbox[0].alternatives[0][0]
        recipients = mail.outbox[0].bcc
        self.assertEqual(attachment_file, "file.txt")
        self.assertEqual(subject, "test_bulk_mail")
        self.assertEqual(body, "Test_Mail")
        self.assertSequenceEqual(recipients, user_emails)

        # Test for get request in send mail
        get_response = self.client.get(reverse(
            'yaksh:send_mail', kwargs={'course_id': self.user1_course.id})
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.context['course'], self.user1_course)
        self.assertTrue(get_response.context['is_mail'])

    def test_download_users_template(self):
        """ Test to check download users template """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # Denies student to download users upload template
        response = self.client.get(reverse('yaksh:download_sample_csv'))
        self.assertEqual(response.status_code, 404)

        # Moderator Login
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:download_sample_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="sample_user_upload.csv"')

    def test_view_course_status(self):
        """ Test to view course status """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # Denies student to view course status
        response = self.client.get(reverse('yaksh:course_status',
                                   kwargs={'course_id': self.user1_course.id}))
        self.assertEqual(response.status_code, 404)

        # Moderator Login
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        self.user1_course.students.add(self.student)

        # Check student details when course is not started
        response = self.client.get(reverse('yaksh:course_status',
                                   kwargs={'course_id': self.user1_course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_progress'])
        self.assertEqual(response.context['course'], self.user1_course)
        student_details = response.context['student_details'][0]
        student, grade, percent, current_unit = student_details
        self.assertEqual(student.username, "demo_student")
        self.assertEqual(grade, "NA")
        self.assertEqual(percent, 0.0)
        self.assertIsNone(current_unit)

        # Check student details when student starts the course
        self.course_status = CourseStatus.objects.create(
            course=self.user1_course, user=self.student)
        response = self.client.get(reverse('yaksh:course_status',
                                   kwargs={'course_id': self.user1_course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_progress'])
        self.assertEqual(response.context['course'], self.user1_course)
        student_details = response.context['student_details'][0]
        student, grade, percent, current_unit = student_details
        self.assertEqual(student.username, "demo_student")
        self.assertIsNone(grade)
        self.assertEqual(percent, 0)
        self.assertIsNone(current_unit)

        self.user1_course.students.remove(self.student)

    def test_course_status_per_user(self):
        """ Test course status for a particular student"""
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # Denies student to view course status
        response = self.client.get(reverse('yaksh:get_user_data',
                                   kwargs={'course_id': self.user1_course.id,
                                           'student_id': self.student.id}))
        err_msg = response.json()['user_data'].replace("\n", "").strip()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(err_msg, "You are not a moderator")

        # Other Moderator Login
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:get_user_data',
                                   kwargs={'course_id': self.user1_course.id,
                                           'student_id': self.student.id}))
        err_msg = response.json()['user_data'].strip()
        actual_err = ('You are neither course creator '
                      'nor course teacher for {0}'.format(
                        self.user1_course.name)
                      )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(err_msg, actual_err)

        # Actual course creator login
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:get_user_data',
                                   kwargs={'course_id': self.user1_course.id,
                                           'student_id': self.student.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()['user_data']
        self.assertIn("Student_First_Name Student_Last_Name", data)
        self.assertIn("Course completed", data)
        self.assertIn("Per Module Progress", data)


class TestCourseStudents(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='user1_first_name',
            last_name='user1_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.user2_plaintext_pass = 'demo2'
        self.user2 = User.objects.create_user(
            username='demo_user2',
            password=self.user2_plaintext_pass,
            first_name='user2_first_name',
            last_name='user2_last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.user2,
            roll_number=10,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )
        self.student1_plaintext_pass = 'demo_student'
        self.student1 = User.objects.create_user(
            username='demo_student1',
            password=self.student1_plaintext_pass,
            first_name='student1_first_name',
            last_name='student1_last_name',
            email='demo_student1@test.com'
        )

        self.student2_plaintext_pass = 'demo_student'
        self.student2 = User.objects.create_user(
            username='demo_student2',
            password=self.student2_plaintext_pass,
            first_name='student2_first_name',
            last_name='student2_last_name',
            email='demo_student2@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)
        self.mod_group.user_set.add(self.user2)

        self.user1_course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user1
            )

        self.user1_course.enroll(False, self.student)
        self.user1_course.reject(False, self.student1)
        self.user1_course.request(self.student2)

    def test_enrolled_users(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:course_students', kwargs={
            'course_id': self.user1_course.id
        })
        response = self.client.get(url)
        enrolled_users = self.user1_course.get_enrolled()
        self.assertTrue(enrolled_users.exists())

    def test_requested_users(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:course_students', kwargs={
            'course_id': self.user1_course.id
        })
        response = self.client.get(url)
        requested_users = self.user1_course.get_requests()
        self.assertTrue(requested_users.exists())

    def test_rejected_users(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:course_students', kwargs={
            'course_id': self.user1_course.id
        })
        response = self.client.get(url)
        rejected_users = self.user1_course.get_rejected()
        self.assertTrue(rejected_users.exists())

    def test_course_students_context(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:course_students', kwargs={
            'course_id': self.user1_course.id
        })
        response = self.client.get(url)
        self.assertTrue('enrolled_users' in response.context)
        self.assertTrue('requested_users' in response.context)
        self.assertTrue('rejected_users' in response.context)

    def test_course_students_where_moderator_is_neither_creator_nor_teacher(
            self):
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        url = reverse('yaksh:course_students', kwargs={
            'course_id': self.user1_course.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_course_students_where_user_is_not_moderator(self):
        self.client.login(
            username=self.student1,
            password=self.student1_plaintext_pass
        )
        url = reverse('yaksh:course_students', kwargs={
            'course_id': self.user1_course.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        self.student.delete()
        self.student1.delete()
        self.student2.delete()
        self.user1_course.delete()


class TestEnrollRequest(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')

        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='user1_first_name',
            last_name='user1_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.user2_plaintext_pass = 'demo2'
        self.user2 = User.objects.create_user(
            username='demo_user2',
            password=self.user2_plaintext_pass,
            first_name='user2_first_name',
            last_name='user2_last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.user2,
            roll_number=10,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)
        self.mod_group.user_set.add(self.user2)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user1
            )

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.user2.delete()
        self.student.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_enroll_request_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:enroll_request',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/enroll_request/{}/'.format(
                self.course.id)
            )
        self.assertRedirects(response, redirect_destination)

    def test_enroll_request_get_for_student(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:enroll_request',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        self.assertRedirects(response, '/exam/quizzes/')

    def test_enroll_request_get_for_moderator(self):
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:enroll_request',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        self.assertRedirects(response, '/exam/manage/courses/')


class TestViewAnswerPaper(TestCase):
    def setUp(self):
        self.client = Client()
        self.plaintext_pass = 'demo'

        for i in range(1, 4):
            User.objects.create_user(
                username='demo_user{0}'.format(i),
                password=self.plaintext_pass,
                first_name='first_name',
                last_name='last_name',
                email='demo@test.com'
            )

        self.user1 = User.objects.get(username="demo_user1")

        self.course = Course.objects.create(
            name="Python Course", enrollment="Enroll Request",
            creator=self.user1
            )

        self.question = Question.objects.create(
            summary='Dummy', points=1,
            type='code', user=self.user1
            )

        self.quiz = Quiz.objects.create(time_between_attempts=0,
                                        description='demo quiz')
        self.user3 = User.objects.get(username="demo_user3")
        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=1.0
            )
        self.question_paper.fixed_questions.add(self.question)
        self.question_paper.save()

        self.ans_paper = AnswerPaper.objects.create(
            user=self.user3, attempt_number=1,
            question_paper=self.question_paper, start_time=timezone.now(),
            user_ip='101.0.0.1', course=self.course,
            end_time=timezone.now()+timezone.timedelta(minutes=20)
            )

    def tearDown(self):
        User.objects.all().delete()
        Course.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        QuestionPaper.objects.all().delete()
        AnswerPaper.objects.all().delete()

    def test_anonymous_user(self):
        # Given, user not logged in
        redirect_destination = (
            '/exam/login/?next=/exam/view_answerpaper/{0}/{1}'.format(
                self.question_paper.id, self.course.id)
            )

        # When
        response = self.client.get(
            reverse('yaksh:view_answerpaper',
                    kwargs={'questionpaper_id': self.question_paper.id,
                            'course_id': self.course.id}
                    ),
            follow=True
        )

        # Then
        self.assertRedirects(response, redirect_destination)

    def test_cannot_view(self):
        # Given, enrolled user tries to view when not permitted by moderator
        user2 = User.objects.get(username="demo_user2")
        self.course.students.add(user2)
        self.course.save()
        self.quiz.view_answerpaper = False
        self.quiz.save()
        self.client.login(
            username=user2.username,
            password=self.plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:view_answerpaper',
                    kwargs={'questionpaper_id': self.question_paper.id,
                            'course_id': self.course.id}
                    ),
            follow=True
        )

        # Then
        self.assertRedirects(response, '/exam/quizzes/')

    def test_can_view_answerpaper(self):
        # Given, user enrolled and can view
        user3 = User.objects.get(username="demo_user3")
        self.course.students.add(user3)
        self.course.save()
        self.quiz.view_answerpaper = True
        self.quiz.save()
        self.client.login(
            username=user3.username,
            password=self.plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:view_answerpaper',
                    kwargs={'questionpaper_id': self.question_paper.id,
                            'course_id': self.course.id}
                    ),
            follow=True
        )

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertTrue('data' in response.context)
        self.assertTrue('quiz' in response.context)
        self.assertTemplateUsed(response, 'yaksh/view_answerpaper.html')

        # When, wrong question paper id
        response = self.client.get(
            reverse('yaksh:view_answerpaper',
                    kwargs={'questionpaper_id': 190,
                            'course_id': self.course.id}
                    ),
            follow=True
        )

        # Then
        self.assertEqual(response.status_code, 404)

    def test_view_when_not_enrolled(self):
        # Given, user tries to view when not enrolled in the course
        user2 = User.objects.get(username="demo_user2")
        self.client.login(
            username=user2.username,
            password=self.plaintext_pass
        )
        self.course.students.remove(user2)
        self.course.save()
        self.quiz.view_answerpaper = True
        self.quiz.save()

        # When
        response = self.client.get(
            reverse('yaksh:view_answerpaper',
                    kwargs={'questionpaper_id': self.question_paper.id,
                            'course_id': self.course.id}
                    ),
            follow=True
        )

        # Then
        self.assertRedirects(response, '/exam/quizzes/')


class TestSelfEnroll(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')
        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='user1_first_name',
            last_name='user1_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.user2_plaintext_pass = 'demo2'
        self.user2 = User.objects.create_user(
            username='demo_user2',
            password=self.user2_plaintext_pass,
            first_name='user2_first_name',
            last_name='user2_last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.user2,
            roll_number=10,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)
        self.mod_group.user_set.add(self.user2)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user1
            )

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.user2.delete()
        self.student.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_self_enroll_denies_anonymous(self):
        response = self.client.get(
            reverse('yaksh:self_enroll',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/self_enroll/{}/'.format(self.course.id)
            )
        self.assertRedirects(response, redirect_destination)

    def test_enroll_request_get_for_student(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:self_enroll',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        self.assertRedirects(response, '/exam/quizzes/')

    def test_enroll_request_get_for_moderator(self):
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:self_enroll',
                    kwargs={'course_id': self.course.id}
                    ),
            follow=True
        )
        self.assertRedirects(response, '/exam/manage/')



class TestGrader(TestCase):
    allow_database_queries = True

    def setUp(self):
        self.client = Client()

        self.mod_group, created = Group.objects.get_or_create(name='moderator')

        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='user1_first_name',
            last_name='user1_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.user2_plaintext_pass = 'demo2'
        self.user2 = User.objects.create_user(
            username='demo_user2',
            password=self.user2_plaintext_pass,
            first_name='user2_first_name',
            last_name='user2_last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.user2,
            roll_number=10,
            institute='IIT',
            department='Aeronautical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)
        self.mod_group.user_set.add(self.user2)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user1
            )

        self.question = Question.objects.create(
            summary='Dummy', points=1, type='code', user=self.user1
            )

        self.quiz = Quiz.objects.create(time_between_attempts=0,
                                        description='demo quiz')

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=1.0
            )
        self.question_paper.fixed_questions.add(self.question)
        self.question_paper.save()

        self.answerpaper = AnswerPaper.objects.create(
            user=self.user2, attempt_number=1,
            question_paper=self.question_paper, start_time=timezone.now(),
            user_ip='101.0.0.1', course=self.course,
            end_time=timezone.now()+timezone.timedelta(minutes=20),
            )

    def tearDown(self):
        User.objects.all().delete()
        Course.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        QuestionPaper.objects.all().delete()
        AnswerPaper.objects.all().delete()
        self.mod_group.delete()

    def test_regrade_denies_anonymous(self):
        # Given
        url = "/exam/login/?next=/exam/manage/regrade/user/question"
        redirect_destination = (
            url + "/{}/{}/{}/{}/".format(
                self.course.id, self.question_paper.id,
                self.answerpaper.id, self.question.id)
            )

        # When
        response = self.client.get(
            reverse('yaksh:regrade_by_question',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id,
                            'question_id': self.question.id,
                            'answerpaper_id': self.answerpaper.id}),
            follow=True
            )

        # Then
        self.assertRedirects(response, redirect_destination)

    def test_regrade_denies_students(self):
        # Given
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:regrade_by_question',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id,
                            'question_id': self.question.id,
                            'answerpaper_id': self.answerpaper.id}),
            follow=True
            )

        # Then
        self.assertEqual(response.status_code, 404)

    def test_regrade_by_moderator(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:regrade_by_question',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id,
                            'question_id': self.question.id,
                            'answerpaper_id': self.answerpaper.id}),
            follow=True)

        # Then
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertIn("demo quiz is submitted for re-evaluation", messages[0])

        # When
        response = self.client.get(
            reverse('yaksh:regrade_by_user',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id,
                            'answerpaper_id': self.answerpaper.id}),
            follow=True)

        # Then
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertIn("demo quiz is submitted for re-evaluation", messages[0])

        # When
        response = self.client.get(
            reverse('yaksh:regrade_by_quiz',
                    kwargs={'course_id': self.course.id,
                            'question_id': self.question.id,
                            'questionpaper_id': self.question_paper.id}),
            follow=True)

        # Then
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertIn("demo quiz is submitted for re-evaluation", messages[0])
        self.assertEqual(Notification.objects.get_receiver_notifications(
            self.user1.id
            ).count(), 3)

    def test_regrade_denies_moderator_not_in_course(self):
        # Given
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )

        self.mod_group.user_set.remove(self.user2)
        # When
        response = self.client.get(
            reverse('yaksh:regrade_by_question',
                    kwargs={'course_id': self.course.id,
                            'questionpaper_id': self.question_paper.id,
                            'question_id': self.question.id,
                            'answerpaper_id': self.answerpaper.id}),
            follow=True)

        # Then
        self.assertEqual(response.status_code, 404)
        self.mod_group.user_set.add(self.user2)


class TestPasswordReset(TestCase):
    def setUp(self):
        self.mod_group = Group.objects.create(name='moderator')

        # Create User with profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo1@test.com'
        )

        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Student',
            timezone='UTC'
        )

    def tearDown(self):
        self.user1.delete()
        self.mod_group.delete()

    def test_password_reset_post(self):
        """
        POST request to password_reset view should return a valid response
        """
        # When
        response = self.client.post(
            reverse('password_reset'),
            data={
                'email': self.user1.email,
            }
        )

        # Then
        self.assertEqual(response.context['email'], self.user1.email)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exam/reset/password_reset/done/')

    def test_password_change_post(self):
        """
        POST request to password_change view should change the user password
        """
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # When
        response = self.client.post(
            reverse('password_change'),
            data={
                'old_password': self.user1_plaintext_pass,
                'new_password1': 'new_demo1_pass',
                'new_password2': 'new_demo1_pass'
            }
        )

        # Then
        self.assertIsNotNone(authenticate(username='demo_user1',
                                          password='new_demo1_pass'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exam/reset/password_change/done/')

        # Finally
        self.client.logout()


class TestModeratorDashboard(TestCase):
    def setUp(self):
        self.client = Client()
        tzone = pytz.timezone("utc")
        self.mod_group = Group.objects.create(name='moderator')
        # student
        self.student_plaintext_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # moderator
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='user_first_name',
            last_name='user_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.mod_no_profile_plaintext_pass = 'demo2'
        self.mod_no_profile = User.objects.create_user(
            username='demo_user2',
            password=self.mod_no_profile_plaintext_pass,
            first_name='user_first_name22',
            last_name='user_last_name',
            email='demo2@test.com'
        )

        self.mod_group.user_set.add(self.user)
        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
            )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

        self.question = Question.objects.create(
            summary="Test_question", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user
            )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz,
            total_marks=1.0, fixed_question_order=str(self.question.id)
            )
        self.question_paper.fixed_questions.add(self.question)

        # student answerpaper
        user_answer = "def add(a, b)\n\treturn a+b"
        self.new_answer = Answer(
            question=self.question, answer=user_answer,
            correct=True, error=json.dumps([]), marks=0.5
            )
        self.new_answer.save()
        self.answerpaper = AnswerPaper.objects.create(
            user=self.student, question_paper=self.question_paper,
            attempt_number=1,
            start_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_time=datetime(2014, 10, 9, 10, 15, 15, 0, tzone),
            user_ip="127.0.0.1", status="completed", passed=True,
            marks_obtained=0.5, course=self.course
            )
        self.answerpaper.answers.add(self.new_answer)
        self.answerpaper.questions_answered.add(self.question)
        self.answerpaper.questions.add(self.question)

        # moderator trial answerpaper
        self.trial_course = Course.objects.create(
            name="Trial Course",
            enrollment="Enroll Request", creator=self.user, is_trial=True
            )
        self.trial_quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='trial quiz', pass_criteria=40,
            is_trial=True
        )

        self.trial_question_paper = QuestionPaper.objects.create(
            quiz=self.trial_quiz,
            total_marks=1.0, fixed_question_order=str(self.question.id)
            )
        self.trial_question_paper.fixed_questions.add(self.question)

        self.new_answer1 = Answer(
            question=self.question, answer=user_answer,
            correct=True, error=json.dumps([]), marks=0.5
            )
        self.new_answer1.save()
        self.trial_answerpaper = AnswerPaper.objects.create(
            user=self.user, question_paper=self.trial_question_paper,
            attempt_number=1,
            start_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_time=datetime(2014, 10, 9, 10, 15, 15, 0, tzone),
            user_ip="127.0.0.1", status="completed", passed=True,
            marks_obtained=0.5, course=self.trial_course
            )
        self.trial_answerpaper.answers.add(self.new_answer1)
        self.trial_answerpaper.questions_answered.add(self.question)
        self.trial_answerpaper.questions.add(self.question)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.quiz.delete()
        self.question_paper.delete()
        self.answerpaper.delete()
        self.new_answer.delete()
        self.mod_group.delete()

    def test_moderator_dashboard_denies_student(self):
        """
            Check moderator dashboard denies student
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:manage'),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 200)

    def test_moderator_dashboard_get_for_user_without_profile(self):
        """
        If no profile exists a blank profile form will be displayed
        """
        self.client.login(
            username=self.mod_no_profile.username,
            password=self.mod_no_profile_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:quizlist_user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/editprofile.html')

    def test_moderator_dashboard_get_for_user_with_profile(self):
        """
        If profile exists a editprofile.html template will be rendered
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:quizlist_user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/quizzes_user.html')

    def test_moderator_dashboard_get_all_quizzes(self):
        """
            Check moderator dashboard to get all the moderator created quizzes
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        response = self.client.get(reverse('yaksh:manage'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/moderator_dashboard.html")
        self.assertEqual(response.context['courses'][0], self.course)


class TestUserLogin(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')

        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo1'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='user1_first_name',
            last_name='user1_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

    def tearDown(self):
        self.client.logout()
        settings.IS_DEVELOPMENT = True
        self.user1.delete()
        self.mod_group.delete()

    def test_successful_user_login(self):
        """
            Check if user is successfully logged in
        """
        response = self.client.post(
            reverse('yaksh:login'),
            data={'username': self.user1.username,
                  'password': self.user1_plaintext_pass}
            )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exam/quizzes/')

    def test_unsuccessful_user_login(self):
        """
            Check for failed login attempt for incorrect username/password
        """
        response = self.client.post(reverse('yaksh:login'),
                                    data={'username': self.user1.username,
                                          'password': "demo"}
                                    )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/login.html')

    def test_email_verified_decorator_for_user_login(self):
        """
            Check email verified decorator to check for user login
        """
        settings.IS_DEVELOPMENT = False
        response = self.client.post(
            reverse('yaksh:login'),
            data={'username': self.user1.username,
                  'password': self.user1_plaintext_pass}
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/activation_status.html")


class TestDownloadCsv(TestCase):
    def setUp(self):
        self.client = Client()
        tzone = pytz.timezone("utc")
        self.mod_group = Group.objects.create(name='moderator')
        # student
        self.student_plaintext_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # moderator
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='user_first_name',
            last_name='user_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )
        self.mod_group.user_set.add(self.user)
        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
            )
        self.course.students.add(self.student)

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

        self.question = Question.objects.create(
            summary="Test_question", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user
            )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz,
            total_marks=1.0, fixed_question_order=str(self.question.id)
            )
        self.question_paper.fixed_questions.add(self.question)
        self.learning_unit = LearningUnit.objects.create(
            order=1, type="quiz", quiz=self.quiz)
        self.learning_module = LearningModule.objects.create(
            order=1, name="download module", description="download module",
            check_prerequisite=False, creator=self.user)
        self.learning_module.learning_unit.add(self.learning_unit.id)
        self.course.learning_module.add(self.learning_module)


        # student answerpaper
        user_answer = "def add(a, b)\n\treturn a+b"
        self.new_answer = Answer(
            question=self.question, answer=user_answer,
            correct=True, error=json.dumps([]), marks=0.5
            )
        self.new_answer.save()
        self.answerpaper = AnswerPaper.objects.create(
            user=self.student, question_paper=self.question_paper,
            attempt_number=1,
            start_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_time=datetime(2014, 10, 9, 10, 15, 15, 0, tzone),
            user_ip="127.0.0.1", status="completed", passed=True,
            marks_obtained=0.5, course=self.course
            )
        self.answerpaper.answers.add(self.new_answer)
        self.answerpaper.questions_answered.add(self.question)
        self.answerpaper.questions.add(self.question)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_download_csv_denies_student(self):
        """
            Check download csv denies student
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:download_quiz_csv',
                                   kwargs={"course_id": self.course.id,
                                           "quiz_id": self.quiz.id}),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 404)

    def test_download_course_csv_denies_student(self):
        """
            Check download course csv denies student
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:download_course_csv',
                                   kwargs={"course_id": self.course.id}),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 404)

    def test_download_csv_denies_non_course_creator(self):
        """
            Check download csv denies non course creator
        """
        self.mod_group.user_set.add(self.student)
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:download_quiz_csv',
                                   kwargs={"course_id": self.course.id,
                                           "quiz_id": self.quiz.id}),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 404)

    def test_download_course_csv_denies_non_course_creator(self):
        """
            Check download course csv denies non course creator
        """
        self.mod_group.user_set.add(self.student)
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:download_course_csv',
                                   kwargs={"course_id": self.course.id}),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 404)

    def test_download_course_csv(self):
        """
            Check for csv result of a course
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_course_csv',
                    kwargs={'course_id': self.course.id}),
            follow=True
            )
        file_name = "{0}.csv".format(
            self.course.name.replace(" ", "_").lower()
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="{0}"'.format(file_name))

    def test_download_course_progress_csv(self):
        """
            Check for csv result of a course progress
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_course_progress',
                    kwargs={'course_id': self.course.id}),
            follow=True
            )
        file_name = "{0}.csv".format(
            self.course.name.lower().replace(" ", "_")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="{0}"'.format(file_name))

    def test_download_quiz_csv(self):
        """
            Check for csv result of a quiz
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:download_quiz_csv',
                    kwargs={"course_id": self.course.id,
                            "quiz_id": self.quiz.id}),
            data={"attempt_number": 1},
            follow=True
            )
        file_name = "{0}-{1}-attempt-{2}.csv".format(
            self.course.name.replace(' ', '_'),
            self.quiz.description.replace(' ', '_'), 1
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="{0}"'.format(file_name))


class TestShowQuestions(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')
        # student
        self.student_plaintext_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # moderator
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='user_first_name',
            last_name='user_last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )
        self.mod_group.user_set.add(self.user)
        self.question = Question.objects.create(
            summary="Test_question1", description="Add two numbers",
            points=2.0, language="python", type="code", user=self.user,
            active=True
            )
        self.question.tags.add("question1")
        self.question1 = Question.objects.create(
            summary="Test_question2", description="Add two numbers",
            points=1.0, language="python", type="mcq", user=self.user,
            active=True
            )
        test_case_upload_data = [{"test_case": "assert fact(3)==6",
                                  "test_case_type": "standardtestcase",
                                  "test_case_args": "",
                                  "weight": 1.0
                                  }]
        question_data_1 = {"snippet": "def fact()", "active": True,
                           "points": 1.0,
                           "description": "factorial of a no",
                           "language": "Python", "type": "Code",
                           "testcase": test_case_upload_data,
                           "summary": "Yaml Demo 2",
                           "tags": ['yaml_demo']
                           }

        question_data_2 = {"snippet": "def fact()", "active": True,
                           "points": 1.0,
                           "description": "factorial of a no",
                           "language": "Python", "type": "Code",
                           "testcase": test_case_upload_data,
                           "summary": "Yaml Demo 3",
                           "tags": ['yaml_demo']
                           }
        yaml_question_1 = dict_to_yaml(question_data_1)
        yaml_question_2 = dict_to_yaml(question_data_2)
        self.yaml_file_1 = SimpleUploadedFile("test1.yaml",
                                              yaml_question_1.encode("utf-8")
                                              )
        self.yaml_file_2 = SimpleUploadedFile("test2.yaml",
                                              yaml_question_2.encode("utf-8")
                                              )

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Profile.objects.all().delete()
        Question.objects.all().delete()
        Group.objects.all().delete()

    def test_show_questions_denies_student(self):
        """
            Check show questions denies student
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:show_questions'),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 404)

    def test_show_all_questions(self):
        """
            Check if all the user created questions are shown
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:show_questions'), follow=True
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertEqual(response.context['objects'][0], self.question1)

    def test_download_questions(self):
        """
            Check for downloading questions zip file
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'question': [self.question.id],
                  'download': 'download'}
            )
        file_name = "{0}_questions.zip".format(self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         "attachment; filename={0}".format(file_name))
        zip_file = string_io(response.content)
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        self.assertIsNone(zipped_file.testzip())
        self.assertIn('questions_dump.yaml', zipped_file.namelist())
        zip_file.close()
        zipped_file.close()

        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'question': [],
                  'download': 'download'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        messages = [m.message for m in get_messages(response.wsgi_request)]
        err_msg = "Please select atleast one question to download"
        self.assertIn(err_msg, messages[0])

    def test_upload_zip_questions(self):
        """
            Check for uploading questions zip file
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ques_file = os.path.join(FIXTURES_DIR_PATH, "demo_questions.zip")
        f = open(ques_file, 'rb')
        questions_file = SimpleUploadedFile(ques_file, f.read(),
                                            content_type="application/zip")
        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'file': questions_file,
                  'upload': 'upload'}
            )
        summaries = ['Find the value of n', 'Print Output in Python2.x',
                     'Adding decimals', 'For Loop over String',
                     'Hello World in File',
                     'Arrange code to convert km to miles',
                     'Print Hello, World!', "Square of two numbers",
                     'Check Palindrome', 'Add 3 numbers', 'Reverse a string'
                     ]

        uploaded_ques = Question.objects.filter(
            active=True, summary__in=summaries,
            user=self.user).count()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertEqual(uploaded_ques, 11)
        f.close()
        dummy_file = SimpleUploadedFile("test.txt", b"test")
        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'file': dummy_file,
                  'upload': 'upload'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Please Upload a ZIP file", messages[0])

    def test_upload_yaml_questions(self):
        """
            Check for uploading questions yaml file
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'file': self.yaml_file_1,
                  'upload': 'upload'}
            )
        uploaded_ques = Question.objects.filter(
            active=True, summary="Yaml Demo 2",
            user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertEqual(uploaded_ques.count(), 1)
        uploaded_ques.delete()

    def test_upload_multiple_yaml_zip_questions(self):
        """
            Check for uploading questions zip file with
            multiple yaml files
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        zipfile_name = string_io()
        zip_file = zipfile.ZipFile(zipfile_name, "w")
        zip_file.writestr("test1.yaml", self.yaml_file_1.read())
        zip_file.writestr("test2.yaml", self.yaml_file_2.read())
        zip_file.close()
        zipfile_name.seek(0)
        questions_file = SimpleUploadedFile("questions.zip",
                                            zipfile_name.read(),
                                            content_type="application/zip"
                                            )
        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'file': questions_file,
                  'upload': 'upload'}
            )
        uploaded_ques = Question.objects.filter(
            active=True, summary="Yaml Demo 2",
            user=self.user).count()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertEqual(uploaded_ques, 1)

    def test_attempt_questions(self):
        """
            Check for testing questions
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'question': [self.question.id],
                  'test': 'test'}
            )
        trial_que_paper = QuestionPaper.objects.get(
                                            quiz__description="trial_questions"
                                            )
        trial_course = Course.objects.get(name="trial_course")
        trial_module = trial_course.learning_module.all()[0]
        redirection_url = "/exam/start/1/{0}/{1}/{2}/".format(
            trial_module.id, trial_que_paper.id, trial_course.id
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirection_url, target_status_code=200)

    def test_questions_filter(self):
        """
            Check for filter questions based type, marks and
            language of a question
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:questions_filter'),
            data={'question_type': 'mcq',
                  'marks': '1.0', 'language': 'python'
                  }
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertEqual(response.context['objects'][0], self.question1)

    def test_download_question_yaml_template(self):
        """ Test to check download question yaml template """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # Denies student to download question yaml template
        response = self.client.get(reverse('yaksh:download_yaml_template'))
        self.assertEqual(response.status_code, 404)

        # Moderator Login
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:download_yaml_template'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="questions_dump.yaml"')

    def test_delete_questions(self):
        """ Test to check if questions are set to not active when deleted """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'question': [self.question.id],
                  'delete': 'delete'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        updated_que = Question.objects.get(id=self.question.id)
        self.assertFalse(updated_que.active)

    def test_search_tags(self):
        """ Test to check if questions are obtained with tags """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        self.question.tags.add('code')
        response = self.client.get(
                reverse('yaksh:search_questions_by_tags'),
                data={'question_tags': ['question1']}
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertEqual(response.context['objects'][0], self.question)

    def test_single_question_attempt(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:test_question', args=[self.question.id])
            )
        trial_que_paper = QuestionPaper.objects.get(
                                            quiz__description="trial_questions"
                                            )
        trial_course = Course.objects.get(name="trial_course")
        trial_module = trial_course.learning_module.all()[0]
        redirection_url = "/exam/start/1/{0}/{1}/{2}/".format(
            trial_module.id, trial_que_paper.id, trial_course.id
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirection_url, target_status_code=200)

    def test_single_question_download(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_question', args=[self.question.id])
            )
        file_name = "{0}_question.zip".format(self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         "attachment; filename={0}".format(file_name))
        zip_file = string_io(response.content)
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        self.assertIsNone(zipped_file.testzip())
        self.assertIn('questions_dump.yaml', zipped_file.namelist())
        zip_file.close()
        zipped_file.close()

    def test_single_question_delete(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:delete_question', args=[self.question.id])
            )
        self.assertEqual(response.status_code, 302)
        updated_que = Question.objects.get(id=self.question.id)
        self.assertFalse(updated_que.active)


class TestShowStatistics(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Open Enrollment", creator=self.user
            )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

        self.question = Question.objects.create(
            summary="Test_question", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user
            )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz,
            total_marks=1.0, fixed_question_order=str(self.question)
            )
        self.question_paper.fixed_questions.add(self.question)
        user_answer = "def add(a, b)\n\treturn a+b"
        self.new_answer = Answer(
            question=self.question, answer=user_answer,
            correct=True, error=json.dumps([])
            )
        self.new_answer.save()
        self.answerpaper = AnswerPaper.objects.create(
            user=self.student, question_paper=self.question_paper,
            attempt_number=1,
            start_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_time=datetime(2014, 10, 9, 10, 15, 15, 0, tzone),
            user_ip="127.0.0.1", status="completed", passed=True,
            percent=1, marks_obtained=1, course=self.course
            )
        self.answerpaper.answers.add(self.new_answer)
        self.answerpaper.questions_answered.add(self.question)
        self.answerpaper.questions.add(self.question)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.course.delete()
        self.answerpaper.delete()
        self.question.delete()
        self.question_paper.delete()
        self.new_answer.delete()
        self.mod_group.delete()

    def test_show_statistics_denies_student(self):
        """
            Check show statistics denies student
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:show_statistics',
                    kwargs={"questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id}),
            follow=True
            )
        self.assertEqual(response.status_code, 404)

    def test_show_statistics_for_student(self):
        """
            Check for student statistics
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:show_statistics',
                    kwargs={'questionpaper_id': self.question_paper.id,
                            "course_id": self.course.id}),
            follow=True
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/statistics_question.html')
        self.assertEqual(response.context['quiz'], self.quiz)
        self.assertEqual(response.context['attempts'][0],
                         self.answerpaper.attempt_number)
        self.assertEqual(response.context['questionpaper_id'],
                         str(self.question_paper.id))

    def test_show_statistics_for_student_per_attempt(self):
        """
            Check for student statistics per attempt
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:show_statistics',
                    kwargs={'questionpaper_id': self.question_paper.id,
                            'attempt_number': self.answerpaper.attempt_number,
                            "course_id": self.course.id}),
            follow=True
            )
        question_stats = response.context['question_stats']
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/statistics_question.html')
        self.assertIn(self.question, list(question_stats.keys()))
        q_data = list(question_stats.values())[0]
        self.assertSequenceEqual(q_data[0:2], [1, 1])
        self.assertEqual(100, q_data[2])


class TestQuestionPaper(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        self.student_plaintext_pass = 'demo'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Student',
            timezone='UTC'
        )

        self.user2_plaintext_pass = 'demo2'
        self.user2 = User.objects.create_user(
            username='demo_user2',
            password=self.user_plaintext_pass,
            first_name='first_name2',
            last_name='last_name2',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.user2,
            roll_number=11,
            institute='IIT',
            department='Chemical',
            position='Student',
            timezone='UTC'
        )

        self.teacher_plaintext_pass = 'demo_teacher'
        self.teacher = User.objects.create_user(
            username='demo_teacher',
            password=self.teacher_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.teacher,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)
        self.mod_group.user_set.add(self.teacher)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Open Enrollment", creator=self.user)

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

        self.demo_quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz 2', pass_criteria=40,
            creator=self.user
        )

        self.quiz_without_qp = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='quiz without question paper', pass_criteria=40,
            creator=self.user
        )

        self.learning_unit = LearningUnit.objects.create(
            order=1, type="quiz", quiz=self.quiz)
        self.learning_module = LearningModule.objects.create(
            order=1, name="test module", description="module",
            check_prerequisite=False, creator=self.user)
        self.learning_module.learning_unit.add(self.learning_unit.id)
        self.course.learning_module.add(self.learning_module)

        # Questions for random set
        self.random_que1 = Question.objects.create(
            summary="Random 1", description="Test Random 1",
            points=1.0, language="python", type="code", user=self.user
        )
        self.random_que2 = Question.objects.create(
            summary="Random 2", description="Test Random 2",
            points=1.0, language="python", type="code", user=self.user
        )

        # Mcq Question
        self.question_mcq = Question.objects.create(
            summary="Test_mcq_question", description="Test MCQ",
            points=1.0, language="python", type="mcq", user=self.user
        )
        self.mcq_based_testcase = McqTestCase(
            options="a",
            question=self.question_mcq,
            correct=True,
            type='mcqtestcase'
        )
        self.mcq_based_testcase.save()

        # Mcc Question
        self.question_mcc = Question.objects.create(
            summary="Test_mcc_question", description="Test MCC",
            points=1.0, language="python", type="mcq", user=self.user
        )
        self.mcc_based_testcase = McqTestCase(
            options="a",
            question=self.question_mcc,
            correct=True,
            type='mcqtestcase'
        )
        self.mcc_based_testcase.save()

        # Integer Question
        self.question_int = Question.objects.create(
            summary="Test_mcc_question", description="Test MCC",
            points=1.0, language="python", type="integer", user=self.user
        )
        self.int_based_testcase = IntegerTestCase(
            correct=1,
            question=self.question_int,
            type='integertestcase'
        )
        self.int_based_testcase.save()

        # String Question
        self.question_str = Question.objects.create(
            summary="Test_mcc_question", description="Test MCC",
            points=1.0, language="python", type="string", user=self.user
        )
        self.str_based_testcase = StringTestCase(
            correct="abc",
            string_check="lower",
            question=self.question_str,
            type='stringtestcase'
        )
        self.str_based_testcase.save()

        # Float Question
        self.question_float = Question.objects.create(
            summary="Test_mcc_question", description="Test MCC",
            points=1.0, language="python", type="float", user=self.user
        )
        self.float_based_testcase = FloatTestCase(
            correct=2.0,
            error_margin=0,
            question=self.question_float,
            type='floattestcase'
        )
        self.float_based_testcase.save()

        # Question with tag
        self.tagged_que = Question.objects.create(
            summary="Test_tag_question", description="Test Tag",
            points=1.0, language="python", type="float", user=self.teacher
            )
        self.tagged_que.tags.add("test_tag")

        self.questions_list = [self.question_mcq, self.question_mcc,
                               self.question_int, self.question_str,
                               self.question_float]
        questions_order = ",".join([
            str(self.question_mcq.id), str(self.question_mcc.id),
            str(self.question_int.id), str(self.question_str.id),
            str(self.question_float.id)
        ])
        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz,
            total_marks=5.0, fixed_question_order=questions_order
        )
        self.fixed_que = Question.objects.create(
            summary="Test_fixed_question", description="Test Tag",
            points=1.0, language="python", type="float", user=self.teacher
            )
        self.fixed_question_paper = QuestionPaper.objects.create(
            quiz=self.demo_quiz, total_marks=5.0
        )
        self.question_paper.fixed_questions.add(*self.questions_list)
        self.answerpaper = AnswerPaper.objects.create(
            user=self.user, question_paper=self.question_paper,
            attempt_number=1,
            start_time=timezone.now() - timezone.timedelta(minutes = 10),
            end_time=timezone.now() - timezone.timedelta(minutes = 1),
            user_ip="127.0.0.1", status="inprogress", passed=False,
            percent=0, marks_obtained=0, course=self.course
        )
        self.answerpaper.questions.add(*self.questions_list)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.teacher.delete()
        self.quiz.delete()
        self.demo_quiz.delete()
        self.course.delete()
        self.answerpaper.delete()
        self.question_mcq.delete()
        self.question_mcc.delete()
        self.question_int.delete()
        self.question_paper.delete()
        self.learning_module.delete()
        self.learning_unit.delete()
        self.mod_group.delete()

    def test_preview_questionpaper_correct(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Should successfully preview question paper
        response = self.client.get(
            reverse('yaksh:preview_questionpaper',
                    kwargs={"questionpaper_id": self.question_paper.id}
                    )
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/preview_questionpaper.html')
        self.assertEqual(
           response.context['questions'],
           self.questions_list
        )
        self.assertEqual(response.context['paper'], self.question_paper)

    def test_preview_questionpaper_without_moderator(self):
        self.client.login(
            username=self.user2.username,
            password=self.user_plaintext_pass
        )

        # Should raise an HTTP 404 response
        response = self.client.get(
            reverse('yaksh:preview_questionpaper',
                    kwargs={"questionpaper_id": self.question_paper.id}
                    )
            )
        self.assertEqual(response.status_code, 404)

    def test_preview_questionpaper_without_quiz_owner(self):
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )

        # Should pass successfully
        response = self.client.get(
            reverse('yaksh:preview_questionpaper',
                    kwargs={"questionpaper_id": self.question_paper.id}
                    )
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/preview_questionpaper.html')
        self.assertEqual(
           response.context['questions'],
           self.questions_list
        )
        self.assertEqual(response.context['paper'], self.question_paper)

    def test_mcq_attempt_right_after_wrong(self):
        """ Case:- Check if answerpaper and answer marks are updated after
            attempting same mcq question with wrong answer and then right
            answer
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Given Wrong Answer
        wrong_user_answer = "25"

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_mcq.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": wrong_user_answer}
        )

        # Then
        wrong_answer_paper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(wrong_answer_paper.marks_obtained, 0)

        # Given Right Answer
        right_user_answer = str(self.mcq_based_testcase.id)

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_mcq.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": right_user_answer}
        )

        # Then
        updated_answerpaper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(updated_answerpaper.marks_obtained, 1)

    def test_mcq_question_attempt_wrong_after_right(self):
        """ Case:- Check if answerpaper and answer marks are updated after
            attempting same mcq question with right answer and then wrong
            answer
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Given Right Answer
        right_user_answer = str(self.mcq_based_testcase.id)

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_mcq.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": right_user_answer}
        )

        # Then
        updated_answerpaper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(updated_answerpaper.marks_obtained, 1)

        # Given Wrong Answer
        wrong_user_answer = "25"

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_mcq.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": wrong_user_answer}
        )

        # Then
        wrong_answer_paper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(wrong_answer_paper.marks_obtained, 0)

    def test_mcc_question_attempt_wrong_after_right(self):
        """ Case:- Check if answerpaper and answer marks are updated after
            attempting same mcc question with right answer and then wrong
            answer
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Given Right Answer
        right_user_answer = str(self.mcc_based_testcase.id)

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_mcc.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": right_user_answer}
        )

        # Then
        updated_answerpaper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(updated_answerpaper.marks_obtained, 1)

        # Given Wrong Answer
        wrong_user_answer = "b"

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_mcc.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": wrong_user_answer}
        )

        # Then
        wrong_answer_paper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(wrong_answer_paper.marks_obtained, 0)

    def test_integer_question_attempt_wrong_after_right(self):
        """ Case:- Check if answerpaper and answer marks are updated after
            attempting same integer question with right answer and then wrong
            answer
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Given Right Answer
        right_user_answer = 1

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_int.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": right_user_answer}
        )

        # Then
        updated_answerpaper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(updated_answerpaper.marks_obtained, 1)

        # Given Wrong Answer
        wrong_user_answer = -1

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_int.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": wrong_user_answer}
        )

        # Then
        wrong_answer_paper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(wrong_answer_paper.marks_obtained, 0)

    def test_string_question_attempt_wrong_after_right(self):
        """ Case:- Check if answerpaper and answer marks are updated after
            attempting same string question with right answer and then wrong
            answer
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Given Right Answer
        right_user_answer = "abc"

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_str.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": right_user_answer}
        )

        # Then
        updated_answerpaper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(updated_answerpaper.marks_obtained, 1)

        # Given Wrong Answer
        wrong_user_answer = "c"

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_str.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": wrong_user_answer}
        )

        # Then
        wrong_answer_paper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(wrong_answer_paper.marks_obtained, 0)

    def test_float_question_attempt_wrong_after_right(self):
        """ Case:- Check if answerpaper and answer marks are updated after
            attempting same float question with right answer and then wrong
            answer
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Given Right Answer
        right_user_answer = 2.0

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_float.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": right_user_answer}
        )

        # Then
        updated_answerpaper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(updated_answerpaper.marks_obtained, 1)

        # Given Wrong Answer
        wrong_user_answer = -1

        # When
        self.client.post(
            reverse('yaksh:check',
                    kwargs={"q_id": self.question_float.id, "attempt_num": 1,
                            "questionpaper_id": self.question_paper.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"answer": wrong_user_answer}
        )

        # Then
        wrong_answer_paper = AnswerPaper.objects.get(id=self.answerpaper.id)
        self.assertEqual(wrong_answer_paper.marks_obtained, 0)

    def test_design_questionpaper(self):
        """ Test design Question Paper """

        # Should fail if Question paper is not the one which is associated
        # with a quiz
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:designquestionpaper',
                    kwargs={
                        "course_id": self.course.id,
                        "quiz_id": self.demo_quiz.id,
                        "questionpaper_id": self.question_paper.id}))
        self.assertEqual(response.status_code, 404)

        # Design question paper for a quiz
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"course_id": self.course.id,
                            "quiz_id": self.quiz_without_qp.id}),
            data={"marks": "1.0", "question_type": "code"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['questions'])

        # Student should not be able to design question paper
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:designquestionpaper',
                    kwargs={"course_id": self.course.id,
                            "quiz_id": self.demo_quiz.id,
                            "questionpaper_id": self.question_paper.id}))
        self.assertEqual(response.status_code, 404)

        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )

        # Should not allow teacher to view question paper
        response = self.client.get(
            reverse('yaksh:designquestionpaper',
                    kwargs={"course_id": self.course.id,
                            "quiz_id": self.quiz.id,
                            "questionpaper_id": self.question_paper.id}))

        self.assertEqual(response.status_code, 404)

        # Should not allow teacher to view question paper
        response = self.client.get(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.question_paper.id}))

        self.assertEqual(response.status_code, 404)

        # Should allow course teacher to view question paper
        # Add teacher to the course
        self.course.teachers.add(self.teacher)
        response = self.client.get(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.question_paper.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/design_questionpaper.html')
        self.assertEqual(response.context['fixed_questions'],
                         self.questions_list)
        self.assertEqual(response.context['qpaper'], self.question_paper)

        # Get questions using tags for question paper
        search_tag = [tag for tag in self.tagged_que.tags.all()]
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.question_paper.id}),
            data={"question_tags": search_tag})

        self.assertEqual(response.context["questions"][0], self.tagged_que)

        # Add random questions in question paper
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.question_paper.id}),
            data={'random_questions': [self.random_que1.id,
                                       self.random_que2.id],
                  'marks': ['1.0'], 'question_type': ['code'],
                  'add-random': ['']}
            )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            self.question_paper.random_questions.filter(
                id__in=[self.random_que1.id, self.random_que2.id]).exists()
        )

        # Check if questions already exists
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.question_paper.id}),
            data={'marks': ['1.0'], 'question_type': ['code'],
                  'add-fixed': ['']}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["questions"].count(), 0)

        # Add fixed question in question paper
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.demo_quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.fixed_question_paper.id}),
            data={'checked_ques': [self.fixed_que.id],
                  'add-fixed': ''}
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            self.fixed_question_paper.fixed_questions.filter(
                id=self.fixed_que.id).exists()
        )

        # Add one more fixed question in question paper
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.demo_quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.fixed_question_paper.id}),
            data={'checked_ques': [self.question_float.id],
                  'add-fixed': ''}
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            self.fixed_question_paper.fixed_questions.filter(
                id=self.question_float.id).exists()
        )

        # Remove fixed question from question paper
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.demo_quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.fixed_question_paper.id}),
            data={'added-questions': [self.fixed_que.id],
                  'remove-fixed': ''}
            )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            self.fixed_question_paper.fixed_questions.filter(
                id=self.fixed_que.id).exists()
        )

        # Remove one more fixed question from question paper
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.demo_quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.fixed_question_paper.id}),
            data={'added-questions': [self.question_float.id],
                  'remove-fixed': ''}
            )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            self.fixed_question_paper.fixed_questions.filter(
                id=self.question_float.id).exists()
        )

        # Remove random questions from question paper
        random_que_set = self.question_paper.random_questions.all().first()
        response = self.client.post(
            reverse('yaksh:designquestionpaper',
                    kwargs={"quiz_id": self.quiz.id,
                            "course_id": self.course.id,
                            "questionpaper_id": self.question_paper.id}),
            data={'random_sets': random_que_set.id,
                  'remove-random': ''}
            )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            self.question_paper.random_questions.filter(
                id=random_que_set.id).exists()
        )


class TestLearningModule(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create a student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@student.com'
        )

        # Create a teacher to add to the course
        self.teacher_plaintext_pass = 'demo_teacher'
        self.teacher = User.objects.create_user(
            username='demo_teacher',
            password=self.teacher_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@teacher.com',
        )

        Profile.objects.create(
            user=self.teacher,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)
        self.mod_group.user_set.add(self.teacher)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Open Enrollment", creator=self.user)

        self.question = Question.objects.create(
            summary="Test_question", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user
            )
        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            creator=self.user
        )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz,
            total_marks=5.0, fixed_question_order=str(self.question.id)
        )

        self.question_paper.fixed_questions.add(self.question)

        self.lesson = Lesson.objects.create(
            name="test lesson", description="test description",
            creator=self.user)
        # create quiz learning unit
        self.learning_unit = LearningUnit.objects.create(
            order=0, type="quiz", quiz=self.quiz)
        # create lesson learning unit
        self.learning_unit1 = LearningUnit.objects.create(
            order=1, type="lesson", lesson=self.lesson)
        # create learning module
        self.learning_module = LearningModule.objects.create(
            order=0, name="test module", description="module",
            check_prerequisite=False, creator=self.user)
        self.learning_module.learning_unit.add(self.learning_unit)
        self.learning_module.learning_unit.add(self.learning_unit1)
        self.learning_module1 = LearningModule.objects.create(
            order=0, name="my module", description="my description",
            check_prerequisite=False, creator=self.user)
        self.course.teachers.add(self.teacher)
        self.course.learning_module.add(self.learning_module)
        self.course.learning_module.add(self.learning_module1)

        self.expected_url = "/exam/manage/courses/all_learning_module/"

    def tearDown(self):
        self.user.delete()
        self.student.delete()
        self.teacher.delete()
        self.quiz.delete()
        self.course.delete()
        self.learning_unit.delete()
        self.learning_module.delete()
        self.mod_group.delete()

    def test_add_new_module_denies_non_moderator(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # Student tries to add learning module
        response = self.client.post(
            reverse('yaksh:add_module', kwargs={"course_id": self.course.id}),
            data={"name": "test module1",
                  "description": "my test1",
                  "Save": "Save"})
        self.assertEqual(response.status_code, 404)

        # Student tries to view learning modules
        self.assertEqual(response.status_code, 404)

    def test_add_new_module(self):
        """ Check if new module is created """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Test add new module
        response = self.client.post(
            reverse('yaksh:add_module', kwargs={"course_id": self.course.id}),
            data={"name": "test module1",
                  "description": "my test1",
                  "Save": "Save"})

        self.assertEqual(response.status_code, 200)
        learning_module = LearningModule.objects.get(name="test module1")
        self.assertEqual(learning_module.description, "my test1")
        self.assertEqual(learning_module.creator, self.user)
        self.assertFalse(learning_module.check_prerequisite)
        self.assertEqual(learning_module.html_data,
                         Markdown().convert("my test1"))

    def test_edit_module(self):
        """ Check if existing module is editable """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        # Test add new module
        response = self.client.post(
            reverse('yaksh:edit_module',
                    kwargs={"course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"name": "test module2",
                  "description": "my test2",
                  "Save": "Save"})

        self.assertEqual(response.status_code, 200)
        learning_module = LearningModule.objects.get(name="test module2")
        self.assertEqual(learning_module.description, "my test2")
        self.assertEqual(learning_module.creator, self.user)
        self.assertFalse(learning_module.check_prerequisite)
        self.assertEqual(learning_module.html_data,
                         Markdown().convert("my test2"))

    def test_teacher_can_edit_module(self):
        """ Check if teacher can edit the module """
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:edit_module',
                    kwargs={"module_id": self.learning_module.id,
                            "course_id": self.course.id}),
            data={"name": "teacher module 2",
                  "description": "teacher module 2",
                  "Save": "Save"})

        self.assertEqual(response.status_code, 200)
        learning_module = LearningModule.objects.get(name="teacher module 2")
        self.assertEqual(learning_module.description, "teacher module 2")
        self.assertEqual(learning_module.creator, self.user)

    def test_teacher_can_design_module(self):
        """ Check if teacher can design the module i.e add learning units """
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:design_module',
                    kwargs={"module_id": self.learning_module1.id,
                            "course_id": self.course.id}),
            data={"Add": "Add",
                  "chosen_list": ",".join([str(self.quiz.id)+":"+"quiz"])
                  })

        # Test add learning unit
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/add_module.html')
        learning_unit = self.learning_module1.learning_unit.all().first()
        self.assertEqual(self.quiz, learning_unit.quiz)
        self.assertEqual(learning_unit.type, "quiz")
        self.assertEqual(learning_unit.order, 1)

        # Test change order of learning unit
        response = self.client.post(
            reverse('yaksh:design_module',
                    kwargs={"module_id": self.learning_module1.id,
                            "course_id": self.course.id}),
            data={"Change": "Change",
                  "ordered_list": ",".join([str(learning_unit.id)+":"+"0"])
                  })
        updated_learning_unit = LearningUnit.objects.get(id=learning_unit.id)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/add_module.html')
        self.assertEqual(updated_learning_unit.order, 0)

        # Test change check prerequisite
        response = self.client.post(
            reverse('yaksh:design_module',
                    kwargs={"module_id": self.learning_module1.id,
                            "course_id": self.course.id}),
            data={"Change_prerequisite": "Change_prerequisite",
                  "check_prereq": [str(learning_unit.id)]
                  })
        updated_learning_unit = LearningUnit.objects.get(id=learning_unit.id)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/add_module.html')
        self.assertTrue(updated_learning_unit.check_prerequisite)

        # Test to remove learning unit from learning module
        response = self.client.post(
            reverse('yaksh:design_module',
                    kwargs={"module_id": self.learning_module1.id,
                            "course_id": self.course.id}),
            data={"Remove": "Remove",
                  "delete_list": [str(learning_unit.id)]
                  })
        updated_learning_unit = LearningUnit.objects.filter(
            id=learning_unit.id).exists()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/add_module.html')
        self.assertFalse(updated_learning_unit)
        self.assertFalse(self.learning_module1.learning_unit.all().exists())

    def test_get_learning_units_for_design(self):
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:design_module',
                    kwargs={"module_id": self.learning_module1.id,
                            "course_id": self.course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/add_module.html')
        self.assertEqual(response.context['quiz_les_list'], set())
        self.assertEqual(len(response.context['learning_units']), 0)
        self.assertEqual(response.context['status'], "design")
        self.assertEqual(response.context['module_id'],
                         str(self.learning_module1.id))
        self.assertEqual(response.context['course_id'], str(self.course.id))

    def test_view_module(self):
        """ Student tries to view a module containing learning units """

        # Student is not enrolled in the course is thrown out
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:view_module',
                    kwargs={"module_id": self.learning_module.id,
                            "course_id": self.course.id}))
        self.assertEqual(response.status_code, 404)

        # add student to the course
        self.course.students.add(self.student.id)

        # check if enrolled student can view module
        response = self.client.get(
            reverse('yaksh:view_module',
                    kwargs={"module_id": self.learning_module.id,
                            "course_id": self.course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/show_video.html")
        self.assertEqual(response.context['learning_units'][0],
                         self.learning_unit)
        self.assertEqual(response.context["state"], "module")
        self.assertEqual(response.context["first_unit"], self.learning_unit)
        self.assertEqual(response.context["user"], self.student)

    def test_get_next_unit(self):
        """ Check if we get correct next unit """

        # Student who is not enrolled is thrown out
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:view_module',
                    kwargs={"module_id": self.learning_module.id,
                            "course_id": self.course.id}))
        self.assertEqual(response.status_code, 404)

        # Enroll student in the course
        self.course.students.add(self.student.id)

        # Get First unit as next unit
        response = self.client.get(
            reverse('yaksh:next_unit',
                    kwargs={"module_id": self.learning_module.id,
                            "course_id": self.course.id,
                            "current_unit_id": self.learning_unit.id,
                            "first_unit": "1"}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['attempt_num'], 1)
        self.assertEqual(response.context["questionpaper"],
                         self.question_paper)
        self.assertEqual(response.context["course"], self.course)
        self.assertEqual(response.context["module"], self.learning_module)
        self.assertEqual(response.context["user"], self.student)

        # Get next unit after first unit
        response = self.client.get(
            reverse('yaksh:next_unit',
                    kwargs={"module_id": self.learning_module.id,
                            "course_id": self.course.id,
                            "current_unit_id": self.learning_unit.id}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["state"], "lesson")
        self.assertEqual(response.context["current_unit"].id,
                         self.learning_unit1.id)

        # Go to next module with empty module
        response = self.client.get(
            reverse('yaksh:next_unit',
                    kwargs={"module_id": self.learning_module1.id,
                            "course_id": self.course.id}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["state"], "module")
        self.assertEqual(response.context["learning_module"].id,
                         self.learning_module.id)

        # Go to next module from last unit of previous unit
        response = self.client.get(
            reverse('yaksh:next_unit',
                    kwargs={"module_id": self.learning_module.id,
                            "course_id": self.course.id,
                            "current_unit_id": self.learning_unit1.id}),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["state"], "module")
        self.assertEqual(response.context["learning_module"].id,
                         self.learning_module1.id)


class TestLessons(TestCase):
    def setUp(self):
        self.client = Client()

        self.mod_group = Group.objects.create(name='moderator')
        # Create Moderator with profile
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Create a student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@student.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # Create a teacher to add to the course
        self.teacher_plaintext_pass = 'demo_teacher'
        self.teacher = User.objects.create_user(
            username='demo_teacher',
            password=self.teacher_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@student.com'
        )

        Profile.objects.create(
            user=self.teacher,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)
        self.mod_group.user_set.add(self.teacher)

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Open Enrollment", creator=self.user)

        self.lesson = Lesson.objects.create(
            name="test lesson", description="test description",
            creator=self.user)
        self.lesson2 = Lesson.objects.create(
            name="test lesson2", description="test description2",
            creator=self.user)
        self.learning_unit = LearningUnit.objects.create(
            order=0, type="lesson", lesson=self.lesson
            )
        self.learning_unit2 = LearningUnit.objects.create(
            order=0, type="lesson", lesson=self.lesson2
            )
        self.learning_module = LearningModule.objects.create(
            order=0, name="test module", description="module",
            check_prerequisite=False, creator=self.user
            )
        self.learning_module2 = LearningModule.objects.create(
            order=1, name="test module 2", description="module 2",
            check_prerequisite=True, creator=self.user
            )
        self.learning_module.learning_unit.add(self.learning_unit.id)
        self.learning_module2.learning_unit.add(self.learning_unit2.id)
        self.course.learning_module.add(*[
            self.learning_module.id, self.learning_module2.id])
        self.course.teachers.add(self.teacher.id)

    def tearDown(self):
        self.user.delete()
        self.student.delete()
        self.teacher.delete()
        self.course.delete()
        self.learning_unit.delete()
        self.learning_unit2.delete()
        self.learning_module.delete()
        self.learning_module2.delete()
        self.lesson.delete()
        self.lesson2.delete()
        self.mod_group.delete()

    def test_edit_lesson_denies_non_moderator(self):
        """ Student should not be allowed to edit lesson """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # Student tries to edit lesson
        response = self.client.get(
            reverse('yaksh:edit_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}))
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_edit_lesson(self):
        """ Teacher should be allowed to edit lesson """
        self.client.login(
            username=self.teacher.username,
            password=self.teacher_plaintext_pass
        )
        dummy_file = SimpleUploadedFile("test.txt", b"test")
        video_file = SimpleUploadedFile("test.mp4", b"test")
        response = self.client.post(
            reverse('yaksh:edit_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"name": "updated lesson",
                  "description": "updated description",
                  "Lesson_files": dummy_file,
                  "video_file": video_file,
                  "Save": "Save"}
            )

        # Teacher edits existing lesson and adds file
        self.assertEqual(response.status_code, 302)
        updated_lesson = Lesson.objects.get(name="updated lesson")
        self.assertEqual(updated_lesson.description, "updated description")
        self.assertEqual(updated_lesson.creator, self.user)
        self.assertEqual(updated_lesson.html_data,
                         Markdown().convert("updated description"))
        self.assertIn("test", os.path.basename(updated_lesson.video_file.name))
        lesson_files = LessonFile.objects.filter(
            lesson=self.lesson).first()
        self.assertIn("test", lesson_files.file.name)
        lesson_file_path = lesson_files.file.path

        # Teacher adds multiple videos in video path
        response = self.client.post(
            reverse('yaksh:edit_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"name": "updated lesson",
                  "description": "updated description",
                  "video_path": "{'youtube': 'test', 'others': 'test'}",
                  "Save": "Save"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Video path : Only one type of video path is allowed",
            str(response.content)
        )

        # Teacher adds wrong pattern in video path
        response = self.client.post(
            reverse('yaksh:edit_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"name": "updated lesson",
                  "description": "updated description",
                  "video_path": "test",
                  "Save": "Save"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Video path : Value must be dictionary",
            str(response.content)
        )

        # Teacher adds correct path in video path
        response = self.client.post(
            reverse('yaksh:edit_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"name": "updated lesson",
                  "description": "updated description",
                  "video_path": "{'others': 'test'}",
                  "Save": "Save"}
            )
        self.assertEqual(response.status_code, 302)

        # Teacher removes the lesson file
        response = self.client.post(
            reverse('yaksh:edit_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "course_id": self.course.id,
                            "module_id": self.learning_module.id}),
            data={"delete_files": [str(lesson_files.id)],
                  "Delete": "Delete"}
            )
        self.assertEqual(response.status_code, 200)
        lesson_file_exists = LessonFile.objects.filter(
            lesson=self.lesson).exists()
        self.assertFalse(lesson_file_exists)
        self.assertFalse(os.path.exists(lesson_file_path))
        updated_lesson.remove_file()

    def test_show_lesson(self):
        """ Student should be able to view lessons """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:show_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "module_id": self.learning_module.id,
                            "course_id": self.course.id}))
        # Student is unable to view lesson
        self.assertEqual(response.status_code, 404)

        # Add student to course
        self.course.students.add(self.student.id)
        response = self.client.get(
            reverse('yaksh:show_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "module_id": self.learning_module.id,
                            "course_id": self.course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["state"], "lesson")
        self.assertEqual(response.context["current_unit"], self.learning_unit)

        # Check unit module prerequisite completion status
        response = self.client.get(
            reverse('yaksh:show_lesson',
                    kwargs={"lesson_id": self.lesson2.id,
                            "module_id": self.learning_module2.id,
                            "course_id": self.course.id}))
        err_msg = "You have not completed the module previous to {0}".format(
            self.learning_module2.name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["msg"], err_msg)

        # Check if lesson is active
        self.lesson.active = False
        self.lesson.save()
        response = self.client.get(
            reverse('yaksh:show_lesson',
                    kwargs={"lesson_id": self.lesson.id,
                            "module_id": self.learning_module.id,
                            "course_id": self.course.id}))
        err_msg = "{0} is not active".format(self.lesson.name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["msg"], err_msg)

        # Check if module is active
        self.learning_module2.active = False
        self.learning_module2.save()
        response = self.client.get(
            reverse('yaksh:show_lesson',
                    kwargs={"lesson_id": self.lesson2.id,
                            "module_id": self.learning_module2.id,
                            "course_id": self.course.id}))
        err_msg = "{0} is not active".format(self.learning_module2.name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["msg"], err_msg)


class TestPost(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

        self.student_plaintext_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # moderator
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
        )

    def test_csrf(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(url)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_view_course_forum_denies_anonymous_user(self):
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        redirection_url = '/exam/login/?next=/exam/forum/course_forum/{0}/'.format(
            str(self.course.id)
            )
        self.assertRedirects(response, redirection_url)

    def test_view_course_forum(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(url, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/course_forum.html')

    def test_view_course_forum_not_found_status_code(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': 99
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_course_forum_url_resolves_course_forum_view(self):
        view = resolve('/exam/forum/course_forum/1/')
        self.assertEqual(view.func, course_forum)

    def test_course_forum_contains_link_to_post_comments_page(self):
        # create a post in setup
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        course_ct = ContentType.objects.get_for_model(self.course)
        post = Post.objects.create(
            title='post 1',
            description='post 1 description',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )
        response = self.client.get(url)
        post_comments_url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': post.uid
        })
        self.assertContains(response, 'href="{0}'.format(post_comments_url))

    def test_new_post_valid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        data = {
            "title": 'Post 1',
            "description": 'Post 1 description',
        }
        response = self.client.post(url, data)
        # This shouldn't be 302. Check where does it redirects.
        course_ct = ContentType.objects.get_for_model(self.course)
        result = Post.objects.filter(title='Post 1',
                                     creator=self.student,
                                     target_ct=course_ct,
                                     target_id=self.course.id)
        self.assertTrue(result.exists())

    def test_new_post_invalid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        data = {}
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)

    def test_new_post_invalid_post_data_empty_fields(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        data = {
            "title": '',
            "description": '',
        }
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)
        self.assertFalse(Post.objects.exists())

    def test_open_created_post_denies_anonymous_user(self):
        course_ct = ContentType.objects.get_for_model(self.course)
        post = Post.objects.create(
            title='post 1',
            description='post 1 description',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': post.uid
        })
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        redirection_url = '/exam/login/?next=/exam/forum/{0}/post/{1}/'.format(
                str(self.course.id), str(post.uid)
            )
        self.assertRedirects(response, redirection_url)

    def test_new_post_invalid_post_data(self):
        """
        Invalid post data should not redirect
        The expected behavior is to show form again with validation errors
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        data = {}
        response = self.client.post(url, data)
        form = response.context.get('form')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(form.errors)

    def test_hide_post(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        self.course.students.add(self.user)
        course_ct = ContentType.objects.get_for_model(self.course)
        post = Post.objects.create(
            title='post 1',
            description='post 1 description',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )
        url = reverse('yaksh:hide_post', kwargs={
            'course_id': self.course.id,
            'uuid': post.uid
        })
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.course.delete()
        self.mod_group.delete()


class TestPostComment(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

        self.student_plaintext_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # moderator
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
        )

        course_ct = ContentType.objects.get_for_model(self.course)
        self.post = Post.objects.create(
            title='post 1',
            description='post 1 description',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )

    def test_csrf(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        response = self.client.get(url)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_post_comments_view_success_status_code(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_post_comments_view_not_found_status_code(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': 99,
            'uuid': '90da38ad-06fa-451b-9e82-5035e839da90'
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_post_comments_url_resolves_post_comments_view(self):
        view = resolve(
            '/exam/forum/1/post/90da38ad-06fa-451b-9e82-5035e839da89/'
        )
        self.assertEquals(view.func, post_comments)

    def test_post_comments_view_contains_link_back_to_course_forum_view(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        comment_url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        course_forum_url = reverse('yaksh:course_forum', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(comment_url)
        self.assertContains(response, 'href="{0}"'.format(course_forum_url))

    def test_post_comments_valid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        data = {
            'post_field': self.post,
            'description': 'post 1 comment',
            'creator': self.user,
        }
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 302)
        result = Comment.objects.filter(post_field__uid=self.post.uid)
        self.assertTrue(result.exists())

    def test_post_comments_invalid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        data = {}
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)

    def test_post_comments_post_data_empty_fields(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        data = {
            'post_field': '',
            'description': '',
            'creator': '',
        }
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)
        self.assertFalse(Comment.objects.exists())

    def test_contains_form(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        response = self.client.get(url)
        form = response.context.get('form')
        self.assertIsInstance(form, CommentForm)

    def post_comment_invalid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('yaksh:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        data = {}
        response = self.client.post(url, data)
        form = response.context.get('form')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(form.errors)

    def test_hide_post_comment(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        self.course.students.add(self.user)
        comment = Comment.objects.create(
            post_field=self.post,
            description='post 1 comment',
            creator=self.user
        )
        url = reverse('yaksh:hide_comment', kwargs={
            'course_id': self.course.id,
            'uuid': comment.uid
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.course.delete()
        self.mod_group.delete()


class TestStartExam(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')

        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo'
        self.user1 = User.objects.create_user(
            username='demo_user',
            password=self.user1_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com',
        )
        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )
        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        # Create courses for user1
        self.user1_course1 = Course.objects.create(
            name="Demo Course",
            enrollment="Enroll Request", creator=self.user1
        )
        # course1 status
        self.course1_status = CourseStatus.objects.create(
            course=self.user1_course1, user=self.user1
        )

        # Create learning modules for user1
        self.learning_module1 = LearningModule.objects.create(
            order=1, name="Demo Module", description="Demo Module",
            check_prerequisite=False, creator=self.user1
        )
        self.learning_module2 = LearningModule.objects.create(
            order=2, name="Demo Module 2", description="Demo Module 2",
            check_prerequisite=False, creator=self.user1
        )

        self.quiz1 = Quiz.objects.create(
            time_between_attempts=0, description='Demo Quiz',
            creator=self.user1
        )

        self.quiz2 = Quiz.objects.create(
            time_between_attempts=0, description='Demo Quiz 2',
            creator=self.user1
        )

        self.question_paper1 = QuestionPaper.objects.create(
            quiz=self.quiz1, total_marks=1.0
        )

        self.question_paper2 = QuestionPaper.objects.create(
            quiz=self.quiz2, total_marks=1.0
        )

        self.question1 = Question.objects.create(
            summary="Test_question 1", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user1
        )

        user_answer = "def add(a, b)\n\treturn a+b"
        self.new_answer = Answer.objects.create(
            question=self.question1, answer=user_answer,
            correct=True, error=json.dumps([])
        )

        self.answerpaper = AnswerPaper.objects.create(
            user=self.student, question_paper=self.question_paper1,
            attempt_number=1,
            start_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_time=datetime(2020, 10, 9, 10, 15, 15, 0, tzone),
            user_ip="127.0.0.1", status="inprogress", passed=True,
            percent=1, marks_obtained=1, course=self.user1_course1
        )

        self.answerpaper.answers.add(self.new_answer)
        self.answerpaper.questions_answered.add(self.question1)

        # Create lessons for user1
        self.lesson1 = Lesson.objects.create(
            name="Demo Lesson", description="Demo Lession",
            creator=self.user1
        )

        self.lesson2 = Lesson.objects.create(
            name="Test Lesson", description="Test Lession",
            creator=self.user1
        )

        # Create units for lesson and quiz
        self.lesson_unit1 = LearningUnit.objects.create(
            order=1, type="lesson", lesson=self.lesson1
        )
        self.quiz_unit1 = LearningUnit.objects.create(
            order=2, type="quiz", quiz=self.quiz1
        )
        self.lesson_unit2 = LearningUnit.objects.create(
            order=1, type="lesson", lesson=self.lesson2
        )
        self.quiz_unit2 = LearningUnit.objects.create(
            order=2, type="quiz", quiz=self.quiz2
        )

        # Add units to module
        self.learning_module1.learning_unit.add(self.lesson_unit1)
        self.learning_module1.learning_unit.add(self.quiz_unit1)

        self.learning_module2.learning_unit.add(self.lesson_unit2)
        self.learning_module2.learning_unit.add(self.quiz_unit2)

        # Add module to course
        self.user1_course1.learning_module.add(self.learning_module1)
        self.user1_course1.learning_module.add(self.learning_module2)

    def test_start_question_paper_does_not_exists_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': 99,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_start_question_paper_does_not_exists_for_moderator(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': 99,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_question_paper_has_no_question_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_start_question_paper_has_no_question_for_moderator(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_has_no_active_learning_module_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)
        self.learning_module1.active = False
        self.learning_module1.save()
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_start_learning_module_has_prerequisite_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper2.fixed_questions.add(self.question1)
        self.learning_module2.active = True
        self.learning_module2.check_prerequisite = True
        self.learning_module2.save()
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper2.id,
            'module_id': self.learning_module2.id,
            'course_id': self.user1_course1.id
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_learning_module_prerequisite_passes_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper2.fixed_questions.add(self.question1)
        self.learning_module2.active = True
        self.learning_module2.check_prerequisite = False
        self.learning_module2.check_prerequisite_passes = True
        self.learning_module2.save()
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper2.id,
            'module_id': self.learning_module2.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_user_enrolled_in_the_course_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)
        self.learning_module1.active = True
        self.learning_module1.check_prerequisite = False
        self.learning_module1.check_prerequisite_passes = False
        self.learning_module1.save()
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_user_enrolled_in_the_course_for_moderator(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)
        self.learning_module1.active = True
        self.learning_module1.check_prerequisite = False
        self.learning_module1.check_prerequisite_passes = False
        self.learning_module1.save()

        self.user1_course1.is_trial = True
        self.user1_course1.save()
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_course_is_active_and_not_expired_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)
        self.learning_module1.active = True
        self.learning_module1.check_prerequisite = False
        self.learning_module1.check_prerequisite_passes = False
        self.learning_module1.save()

        self.user1_course1.students.add(self.student)
        self.user1_course1.active = False
        self.user1_course1.end_enroll_time = timezone.now()
        self.user1_course1.save()
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_course_is_active_and_not_expired_for_moderator(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)
        self.learning_module1.active = True
        self.learning_module1.check_prerequisite = False
        self.learning_module1.check_prerequisite_passes = False
        self.learning_module1.save()

        self.user1_course1.students.add(self.user1)
        self.user1_course1.active = False
        self.user1_course1.end_enroll_time = timezone.now()
        self.user1_course1.is_trial = True
        self.user1_course1.save()
        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_quiz_is_active_and_is_not_expired_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)
        self.learning_module1.active = True
        self.learning_module1.check_prerequisite = False
        self.learning_module1.check_prerequisite_passes = False
        self.learning_module1.save()

        self.user1_course1.students.add(self.student)
        self.user1_course1.save()

        self.question_paper1.quiz.end_date_time = timezone.now()
        self.question_paper1.quiz.active = False
        self.question_paper1.quiz.save()

        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_quiz_is_active_and_is_not_expired_for_moderator(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)
        self.learning_module1.active = True
        self.learning_module1.check_prerequisite = False
        self.learning_module1.check_prerequisite_passes = False
        self.learning_module1.save()

        self.user1_course1.students.add(self.user1)
        self.user1_course1.is_trial = True
        self.user1_course1.save()

        self.question_paper1.quiz.end_date_time = timezone.now()
        self.question_paper1.quiz.active = False
        self.question_paper1.quiz.save()

        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_prereq_check_and_pass_criteria_for_quiz_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper2.fixed_questions.add(self.question1)
        self.learning_module2.active = True
        self.learning_module2.check_prerequisite = False
        self.learning_module2.check_prerequisite_passes = False
        self.learning_module2.save()

        self.user1_course1.students.add(self.student)
        self.user1_course1.is_trial = True
        self.user1_course1.save()

        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper2.id,
            'module_id': self.learning_module2.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_prereq_check_and_pass_criteria_for_quiz_for_moderator(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        self.question_paper2.fixed_questions.add(self.question1)
        self.learning_module2.active = True
        self.learning_module2.check_prerequisite = False
        self.learning_module2.check_prerequisite_passes = False
        self.learning_module2.save()

        self.user1_course1.students.add(self.user1)
        self.user1_course1.is_trial = True
        self.user1_course1.save()

        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper2.id,
            'module_id': self.learning_module2.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_not_allowed_to_start_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)

        self.learning_module1.active = True
        self.learning_module1.check_prerequisite = False
        self.learning_module1.check_prerequisite_passes = False
        self.learning_module1.save()

        self.user1_course1.students.add(self.student)
        self.user1_course1.is_trial = True
        self.user1_course1.save()

        learning_unit = self.learning_module1.learning_unit.get(
            quiz=self.question_paper1.quiz.id
        )
        learning_unit.check_prerequisite = False
        learning_unit.save()

        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper1.id,
            'module_id': self.learning_module1.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_not_allowed_to_start_for_moderator(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        self.question_paper1.fixed_questions.add(self.question1)

        self.learning_module1.active = True
        self.learning_module1.check_prerequisite = False
        self.learning_module1.check_prerequisite_passes = False
        self.learning_module1.save()

        self.user1_course1.students.add(self.user1)
        self.user1_course1.is_trial = True
        self.user1_course1.save()

        learning_unit = self.learning_module1.learning_unit.get(
            quiz=self.question_paper1.quiz.id
        )
        learning_unit.check_prerequisite = False
        learning_unit.save()

    def test_start_allowed_to_start_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper2.fixed_questions.add(self.question1)

        self.learning_module2.active = True
        self.learning_module2.check_prerequisite = False
        self.learning_module2.check_prerequisite_passes = False
        self.learning_module2.save()

        self.user1_course1.students.add(self.student)
        self.user1_course1.is_trial = True
        self.user1_course1.save()

        learning_unit = self.learning_module2.learning_unit.get(
            quiz=self.question_paper2.quiz.id
        )
        learning_unit.check_prerequisite = False
        learning_unit.save()

        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper2.id,
            'module_id': self.learning_module2.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_allowed_to_start_for_moderator(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        self.question_paper2.fixed_questions.add(self.question1)

        self.learning_module2.active = True
        self.learning_module2.check_prerequisite = False
        self.learning_module2.check_prerequisite_passes = False
        self.learning_module2.save()

        self.user1_course1.students.add(self.user1)
        self.user1_course1.is_trial = True
        self.user1_course1.save()

        learning_unit = self.learning_module2.learning_unit.get(
            quiz=self.question_paper2.quiz.id
        )
        learning_unit.check_prerequisite = False
        learning_unit.save()

        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper2.id,
            'module_id': self.learning_module2.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_start_allowed_to_start_when_quiz_is_exercise_for_user(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.question_paper2.fixed_questions.add(self.question1)

        self.learning_module2.active = True
        self.learning_module2.check_prerequisite = False
        self.learning_module2.check_prerequisite_passes = False
        self.learning_module2.save()

        self.user1_course1.students.add(self.student)
        self.user1_course1.is_trial = True
        self.user1_course1.save()

        learning_unit = self.learning_module2.learning_unit.get(
            quiz=self.question_paper2.quiz.id
        )
        learning_unit.check_prerequisite = False
        learning_unit.save()

        self.question_paper2.quiz.is_exercise = True
        self.question_paper2.quiz.save()

        url = reverse('yaksh:start_quiz', kwargs={
            'questionpaper_id': self.question_paper2.id,
            'module_id': self.learning_module2.id,
            'course_id': self.user1_course1.id
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.student.delete()
        self.quiz1.delete()
        self.user1_course1.delete()


class TestLessonContents(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')
        tzone = pytz.timezone('UTC')

        # Create Moderator with profile
        self.user1_plaintext_pass = 'demo'
        self.user1 = User.objects.create_user(
            username='demo_user',
            password=self.user1_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com',
        )
        Profile.objects.create(
            user=self.user1,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC',
            is_moderator=True
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )
        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        # Create courses for user1
        self.user1_course1 = Course.objects.create(
            name="My Course", enrollment="Enroll Request", creator=self.user1
        )

        # Create learning modules for user1
        self.learning_module1 = LearningModule.objects.create(
            order=1, name="My Module", description="My Module",
            check_prerequisite=False, creator=self.user1
        )
        self.lesson1 = Lesson.objects.create(
            name="My Lesson", description="My Lesson",
            creator=self.user1
        )

        # Create units for lesson
        self.lesson_unit1 = LearningUnit.objects.create(
            order=1, type="lesson", lesson=self.lesson1
        )
        self.learning_module1.learning_unit.add(self.lesson_unit1)
        self.user1_course1.learning_module.add(self.learning_module1)

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.lesson_unit1.delete()
        self.user1_course1.delete()
        self.learning_module1.delete()

    def test_create_marker(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        # disallow user other than moderator or course creator or course teacher
        response = self.client.post(
            reverse('yaksh:add_marker',
                    kwargs={"course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'content': '1', 'question_type': ''}
            )
        self.assertEqual(response.status_code, 404)
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # Get json response for topic
        response = self.client.post(
            reverse('yaksh:add_marker',
                    kwargs={"course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'content': '1', 'question_type': ''}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(json_response.get("content_type"), '1')

        # Get json response for question form
        response = self.client.post(
            reverse('yaksh:add_marker',
                    kwargs={"course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'content': '2', 'question_type': ''}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(json_response.get("content_type"), '2')

    def test_add_lesson_topic(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        # disallow user other than moderator or course creator or course teacher
        response = self.client.post(
            reverse('yaksh:add_topic',
                    kwargs={"content_type": '1',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'name': 'My Lesson Topic',
                  'description': 'My lesson topic description'}
            )
        self.assertEqual(response.status_code, 404)

        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # Post json response for topic
        response = self.client.post(
            reverse('yaksh:add_topic',
                    kwargs={"content_type": '1',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'name': 'My_Lesson_Topic',
                  'description': 'My lesson topic description'}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(
            json_response.get("message"), "Saved topic successfully"
        )
        topics = Topic.objects.filter(name="My_Lesson_Topic")
        self.assertTrue(topics.exists())

        # Get json response for topic form
        single_topic = topics.first()
        toc = TableOfContents.objects.get(
            course_id=self.user1_course1.id, lesson_id=self.lesson1.id,
            object_id=single_topic.id
        )
        response = self.client.get(
            reverse('yaksh:edit_topic',
                    kwargs={"content_type": '1',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id,
                            "topic_id": single_topic.id,
                            "toc_id": toc.id})
                    )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))

        # delete topic Toc
        response = self.client.post(
            reverse('yaksh:delete_toc',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": toc.id}),
            data={'redirect_url': reverse("yaksh:login")}
            )
        self.assertEqual(response.status_code, 302)

    def test_add_lesson_quiz(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        # disallow user other than moderator or course creator or course teacher
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '1',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'My_Lesson_question',
                  'description': 'My lesson topic description',
                  'language': 'mcq', 'type': 'other', 'topic': 'test'}
            )
        self.assertEqual(response.status_code, 404)

        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # Post json response for lesson quiz (with 400 error)
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '1',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'My_Lesson_question',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'integer', 'topic': 'test'}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(json_response.get("success"))

        # Post json response for lesson quiz (with 200 success)
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '2',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'My_Lesson_question',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'integer', 'topic': 'test',
                  'points': '1', 'form-TOTAL_FORMS': 1,
                  'form-MAX_NUM_FORMS': '',
                  'form-INITIAL_FORMS': 0, 'integertestcase_set-TOTAL_FORMS': 0,
                  'integertestcase_set-INITIAL_FORMS': 0,
                  'integertestcase_set-MIN_NUM_FORMS': 0,
                  'integertestcase_set-MAX_NUM_FORMS': 0,
                  'integertestcase_set-0-correct': "1"}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))

        self.assertEqual(
            json_response.get("message"), "Saved question successfully"
        )
        que = Question.objects.filter(summary="My_Lesson_question")
        self.assertTrue(que.exists())

        # Get edit question form
        single_que = que.first()
        toc = TableOfContents.objects.get(
            course_id=self.user1_course1.id, lesson_id=self.lesson1.id,
            object_id=single_que.id
        )
        response = self.client.get(
            reverse('yaksh:edit_marker_quiz',
                    kwargs={"content_type": '2',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id,
                            "question_id": single_que.id,
                            "toc_id": toc.id})
                    )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(json_response.get("content_type"), 2)

        # delete question Toc
        response = self.client.post(
            reverse('yaksh:delete_toc',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": toc.id}),
            data={'redirect_url': reverse("yaksh:login")}
            )
        self.assertEqual(response.status_code, 302)

    def test_get_and_submit_marker_quiz(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # Create a question for lesson exercise
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '3',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'My_Lesson_question',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'integer', 'topic': 'test',
                  'points': '1', 'form-TOTAL_FORMS': 1,
                  'form-MAX_NUM_FORMS': '',
                  'form-INITIAL_FORMS': 0,
                  'integertestcase_set-TOTAL_FORMS': 1,
                  'integertestcase_set-INITIAL_FORMS': 0,
                  'integertestcase_set-MIN_NUM_FORMS': 0,
                  'integertestcase_set-MAX_NUM_FORMS': 0,
                  'integertestcase_set-0-type': 'integertestcase',
                  'integertestcase_set-0-correct': "1"}
            )

        self.client.logout()
        que = Question.objects.filter(summary="My_Lesson_question")

        single_que = que.first()
        toc = TableOfContents.objects.get(
            course_id=self.user1_course1.id, lesson_id=self.lesson1.id,
            object_id=single_que.id
        )

        # Get lesson exercise as student
        # Given
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:get_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": toc.id})
            )

        # Then
        self.assertEqual(response.status_code, 404)

        # Given
        self.user1_course1.students.add(self.student)
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:get_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": toc.id})
            )
        json_response = json.loads(response.content)

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))

        # Submit empty answer for lesson quiz
        response = self.client.post(
            reverse('yaksh:submit_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": toc.id}),
            data={'answer': ''}
            )
        json_response = json.loads(response.content)

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertFalse(json_response.get("success"))

        # Submit valid answer for lesson quiz
        # When
        response = self.client.post(
            reverse('yaksh:submit_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": toc.id}),
            data={'answer': '1'}
            )
        json_response = json.loads(response.content)

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(
            json_response.get("message"), "You answered the question correctly"
        )


    def test_lesson_statistics(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # Create a question for lesson exercise
        # When
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '3',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'My_Lesson_question',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'integer', 'topic': 'test',
                  'points': '1', 'form-TOTAL_FORMS': 1,
                  'form-MAX_NUM_FORMS': '',
                  'form-INITIAL_FORMS': 0,
                  'integertestcase_set-TOTAL_FORMS': 1,
                  'integertestcase_set-INITIAL_FORMS': 0,
                  'integertestcase_set-MIN_NUM_FORMS': 0,
                  'integertestcase_set-MAX_NUM_FORMS': 0,
                  'integertestcase_set-0-type': 'integertestcase',
                  'integertestcase_set-0-correct': "1"}
            )
        self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '3',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'Mcc_Lesson_stats',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'mcc', 'topic': 'test',
                  'points': '1', 'form-TOTAL_FORMS': 2,
                  'form-MAX_NUM_FORMS': '',
                  'form-INITIAL_FORMS': 0,
                  'mcqtestcase_set-TOTAL_FORMS': 2,
                  'mcqtestcase_set-INITIAL_FORMS': 0,
                  'mcqtestcase_set-MIN_NUM_FORMS': 0,
                  'mcqtestcase_set-MAX_NUM_FORMS': 0,
                  'mcqtestcase_set-0-type': 'mcqtestcase',
                  'mcqtestcase_set-0-options': "1",
                  'mcqtestcase_set-0-correct': True,
                  'mcqtestcase_set-1-type': 'mcqtestcase',
                  'mcqtestcase_set-1-options': "2",
                  'mcqtestcase_set-1-correct': False
                }
            )
        que = Question.objects.filter(summary="My_Lesson_question")

        single_que = que.first()
        toc = TableOfContents.objects.get(
            course_id=self.user1_course1.id, lesson_id=self.lesson1.id,
            object_id=single_que.id
        )
        self.client.logout()
        self.user1_course1.students.add(self.student)
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:submit_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": toc.id}),
            data={'answer': '1'}
            )
        self.client.logout()

        # Then
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:lesson_statistics',
                    kwargs={"course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id})
            )
        response_data = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            next(iter(response_data.get("data").keys())).id, toc.id
        )

        # Then
        response = self.client.get(
            reverse('yaksh:lesson_statistics',
                    kwargs={"course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id,
                            "toc_id": toc.id})
            )
        response_data = response.context
        student_info = response_data.get("objects").object_list[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            next(iter(response_data.get("data").keys())).id, toc.id
        )
        self.assertEqual(student_info.get("student_id"), self.student.id)

        # Test for mcc lesson question statistics
        # Given
        que = Question.objects.filter(summary="Mcc_Lesson_stats")

        single_que = que.first()
        toc = TableOfContents.objects.get(
            course_id=self.user1_course1.id, lesson_id=self.lesson1.id,
            object_id=single_que.id
        )
        self.client.logout()

        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:submit_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": toc.id}),
            data={'answer': [str(i.id) for i in single_que.get_test_cases()]}
            )
        self.client.logout()

        # Then
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:lesson_statistics',
                    kwargs={"course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id,
                            "toc_id": toc.id})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(student_info.get("student_id"), self.student.id)

    def test_multiple_lesson_question_types(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # Create float based question
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '3',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'Float_Lesson',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'float', 'topic': 'test',
                  'points': '1', 'form-TOTAL_FORMS': 1,
                  'form-MAX_NUM_FORMS': '',
                  'form-INITIAL_FORMS': 0,
                  'floattestcase_set-TOTAL_FORMS': 1,
                  'floattestcase_set-INITIAL_FORMS': 0,
                  'floattestcase_set-MIN_NUM_FORMS': 0,
                  'floattestcase_set-MAX_NUM_FORMS': 0,
                  'floattestcase_set-0-type': 'floattestcase',
                  'floattestcase_set-0-correct': "1",
                  'floattestcase_set-0-error_margin': "0.1"
                }
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(
            json_response.get("message"), "Saved question successfully"
        )


        # Create a mcq question
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '3',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'Mcq_Lesson',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'mcq', 'topic': 'test',
                  'points': '1', 'form-TOTAL_FORMS': 2,
                  'form-MAX_NUM_FORMS': '',
                  'form-INITIAL_FORMS': 0,
                  'mcqtestcase_set-TOTAL_FORMS': 2,
                  'mcqtestcase_set-INITIAL_FORMS': 0,
                  'mcqtestcase_set-MIN_NUM_FORMS': 0,
                  'mcqtestcase_set-MAX_NUM_FORMS': 0,
                  'mcqtestcase_set-0-type': 'mcqtestcase',
                  'mcqtestcase_set-0-options': "1",
                  'mcqtestcase_set-0-correct': True,
                  'mcqtestcase_set-1-type': 'mcqtestcase',
                  'mcqtestcase_set-1-options': "2",
                  'mcqtestcase_set-1-correct': False
                }
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(
            json_response.get("message"), "Saved question successfully"
        )

        # Create a mcc question
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '3',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'Mcc_Lesson',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'mcc', 'topic': 'test',
                  'points': '1', 'form-TOTAL_FORMS': 2,
                  'form-MAX_NUM_FORMS': '',
                  'form-INITIAL_FORMS': 0,
                  'mcqtestcase_set-TOTAL_FORMS': 2,
                  'mcqtestcase_set-INITIAL_FORMS': 0,
                  'mcqtestcase_set-MIN_NUM_FORMS': 0,
                  'mcqtestcase_set-MAX_NUM_FORMS': 0,
                  'mcqtestcase_set-0-type': 'mcqtestcase',
                  'mcqtestcase_set-0-options': "1",
                  'mcqtestcase_set-0-correct': True,
                  'mcqtestcase_set-1-type': 'mcqtestcase',
                  'mcqtestcase_set-1-options': "2",
                  'mcqtestcase_set-1-correct': False
                }
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(
            json_response.get("message"), "Saved question successfully"
        )


        # Create a string based question
        response = self.client.post(
            reverse('yaksh:add_marker_quiz',
                    kwargs={"content_type": '3',
                            "course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id}),
            data={'timer': '00:00:00', 'summary': 'String_Lesson',
                  'description': 'My lesson question description',
                  'language': 'other', 'type': 'string', 'topic': 'test',
                  'points': '1', 'form-TOTAL_FORMS': 1,
                  'form-MAX_NUM_FORMS': '',
                  'form-INITIAL_FORMS': 0,
                  'stringtestcase_set-TOTAL_FORMS': 1,
                  'stringtestcase_set-INITIAL_FORMS': 0,
                  'stringtestcase_set-MIN_NUM_FORMS': 0,
                  'stringtestcase_set-MAX_NUM_FORMS': 0,
                  'stringtestcase_set-0-type': 'stringtestcase',
                  'stringtestcase_set-0-correct': "test",
                  'stringtestcase_set-0-string_check': "lower"
                }
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(
            json_response.get("message"), "Saved question successfully"
        )

        ques = Question.objects.filter(
            summary__in=["Mcq_Lesson", "Mcc_Lesson",
                         "Float_Lesson", "String_Lesson"]
            ).values_list("id", flat=True)
        self.assertTrue(ques.exists())
        tocs = TableOfContents.objects.filter(
            course_id=self.user1_course1.id, lesson_id=self.lesson1.id,
            object_id__in=ques
        ).values_list("id", flat=True)
        self.assertTrue(tocs.exists())

        # Student submits answers to all the questions
        self.user1_course1.students.add(self.student)
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # submit mcq question
        response = self.client.post(
            reverse('yaksh:submit_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": tocs[0]}),
            data={'answer': '1'}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(
            json_response.get("message"), "You answered the question correctly"
        )

        # submit mcc question
        response = self.client.post(
            reverse('yaksh:submit_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": tocs[1]}),
            data={'answer': ['1']}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(json_response.get("success"))
        self.assertIn(
            "You have answered the question incorrectly",
            json_response.get("message"),
        )

        # submit float question
        response = self.client.post(
            reverse('yaksh:submit_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": tocs[2]}),
            data={'answer': '1.0'}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(json_response.get("success"))
        self.assertIn(
            "You have answered the question incorrectly",
            json_response.get("message"),
        )


        # submit string question
        response = self.client.post(
            reverse('yaksh:submit_marker_quiz',
                    kwargs={"course_id": self.user1_course1.id,
                            "toc_id": tocs[3]}),
            data={'answer': 'test'}
            )
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response.get("success"))
        self.assertEqual(
            json_response.get("message"), "You answered the question correctly"
        )
        self.client.logout()
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # Get statistics for mcc question
        response = self.client.get(
            reverse('yaksh:lesson_statistics',
                    kwargs={"course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id,
                            "toc_id": tocs[1]})
            )
        response_data = response.context
        student_info = response_data.get("objects").object_list[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(student_info.get("student_id"), self.student.id)

        # Get statistics for mcq question
        response = self.client.get(
            reverse('yaksh:lesson_statistics',
                    kwargs={"course_id": self.user1_course1.id,
                            "lesson_id": self.lesson1.id,
                            "toc_id": tocs[0]})
            )
        response_data = response.context
        student_info = response_data.get("objects").object_list[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(student_info.get("student_id"), self.student.id)

    def test_upload_download_lesson_contents(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        dummy_file = SimpleUploadedFile("test.txt", b"test")
        # Invalid file type
        response = self.client.post(
            reverse('yaksh:edit_lesson',
                    kwargs={"lesson_id": self.lesson1.id,
                            "course_id": self.user1_course1.id,
                            "module_id": self.learning_module1.id}),
            data={"toc": dummy_file,
                  "upload_toc": "upload_toc"}
            )
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertIn('Please upload yaml or yml type file', messages)

        # Valid yaml file for TOC
        yaml_path = os.sep.join((FIXTURES_DIR_PATH, 'sample_lesson_toc.yaml'))
        with open(yaml_path, 'rb') as fp:
            yaml_file = SimpleUploadedFile("test.yml", fp.read())
            response = self.client.post(
                reverse('yaksh:edit_lesson',
                        kwargs={"lesson_id": self.lesson1.id,
                                "course_id": self.user1_course1.id,
                                "module_id": self.learning_module1.id}),
                data={"toc": yaml_file,
                      "upload_toc": "upload_toc"}
                )
            contents = [
                'Sample lesson quiz 1', 'Sample lesson quiz 2',
                'Sample lesson topic 1', 'Sample lesson topic 2'
            ]
            self.assertEqual(response.status_code, 200)
            has_que = Question.objects.filter(
                summary__in=contents[:2]
                ).exists()
            has_topics = Topic.objects.filter(
                name__in=contents[2:]
                ).exists()
            self.assertTrue(has_que)
            self.assertTrue(has_topics)

        # Invalid YAML file data
        yaml_content = b"""
        ---
        name: 'Sample lesson topic 2'
        description: 'Topic 2 description'
        """
        yaml_file = SimpleUploadedFile("test.yml", yaml_content)
        response = self.client.post(
                reverse('yaksh:edit_lesson',
                        kwargs={"lesson_id": self.lesson1.id,
                                "course_id": self.user1_course1.id,
                                "module_id": self.learning_module1.id}),
                data={"toc": yaml_file,
                      "upload_toc": "upload_toc"}
                )
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error parsing yaml", messages[0])

        # Invalid YAML with no content_type and invalid time format
        yaml_path = os.sep.join((FIXTURES_DIR_PATH, 'invalid_yaml.yaml'))
        with open(yaml_path, 'rb') as fp:
            yaml_file = SimpleUploadedFile("test.yml", fp.read())
            response = self.client.post(
                reverse('yaksh:edit_lesson',
                        kwargs={"lesson_id": self.lesson1.id,
                                "course_id": self.user1_course1.id,
                                "module_id": self.learning_module1.id}),
                data={"toc": yaml_file,
                      "upload_toc": "upload_toc"}
                )
            messages = [m.message for m in get_messages(response.wsgi_request)]
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                "content_type or time key is missing", messages[0]
            )
            self.assertIn("Invalid time format", messages[1])

        # Download yaml sample
        response = self.client.get(reverse('yaksh:download_sample_toc'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'),
                         'attachment; filename="sample_lesson_toc.yaml"')
