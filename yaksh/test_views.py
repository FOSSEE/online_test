from datetime import datetime
import pytz
import os
import json
try:
    from StringIO import StringIO as string_io
except ImportError:
    from io import BytesIO as string_io
import zipfile
import shutil
from textwrap import dedent

from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import Client
from django.utils import timezone
from django.core import mail
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from yaksh.decorators import user_has_profile
from yaksh.models import (
    User, Profile, Question, Quiz, QuestionPaper, AnswerPaper, Answer, Course,
    AssignmentUpload, Room, Message
)

# Channels imports
from channels.test import WSClient, ChannelTestCase


class TestUserRegistration(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        self.registered_user.delete()

    def test_register_user_post(self):
        self.client.post(
            reverse('yaksh:register'),
            data={'username': 'register_user',
                  'email': 'register_user@mail.com', 'password': 'reg_user',
                  'confirm_password': 'reg_user', 'first_name': 'user1_f_name',
                  'last_name': 'user1_l_name', 'roll_number': '1',
                  'institute': 'demo_institute', 'department': 'demo_dept',
                  'position': 'student', 'timezone': pytz.utc.zone}
        )
        self.registered_user = User.objects.get(username='register_user')
        self.assertEqual(self.registered_user.email, 'register_user@mail.com')
        self.assertEqual(self.registered_user.first_name, 'user1_f_name')
        self.assertEqual(self.registered_user.last_name, 'user1_l_name')
        self.assertEqual(self.registered_user.profile.roll_number, '1')
        self.assertEqual(
            self.registered_user.profile.institute,
            'demo_institute'
        )
        self.assertEqual(self.registered_user.profile.department, 'demo_dept')
        self.assertEqual(self.registered_user.profile.position, 'student')
        self.assertEqual(self.registered_user.profile.timezone, 'UTC')


class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()

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
            reverse('yaksh:new_activation'), data={'email': self.user2.email}
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
            name="Python Course", enrollment="Enroll Request",
            creator=self.user
        )

        self.hidden_course = Course.objects.create(
            name="Hidden Course", enrollment="Enroll Request",
            creator=self.user, code="hide", hidden=True
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.course.delete()

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
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/quizzes_user.html")
        self.assertEqual(response.context['title'], 'All Courses')
        self.assertEqual(response.context['courses'][0], self.course)

    def test_student_dashboard_enrolled_courses_get(self):
        """
            Check student dashboard for all courses in which student is
            enrolled
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        response = self.client.get(
            reverse('yaksh:quizlist_user', kwargs={'enrolled': "enrolled"}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/quizzes_user.html")
        self.assertEqual(response.context['title'], 'Enrolled Courses')
        self.assertEqual(response.context['courses'][0], self.course)

    def test_student_dashboard_hidden_courses_post(self):
        """
            Get courses for student based on the course code
        """

        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:quizlist_user'), data={'course_code': 'hide'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/quizzes_user.html")
        self.assertEqual(response.context['title'], 'Search')
        self.assertEqual(response.context['courses'][0], self.hidden_course)


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

        # Create a different moderator
        self.user1_plaintext_pass = 'demo'
        self.user1 = User.objects.create_user(
            username='demo_user1',
            password=self.user1_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
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
        self.mod_group.user_set.add(self.user1)
        self.course = Course.objects.create(
            name="Python Course", enrollment="Open Enrollment",
            creator=self.user
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            language='Python', course=self.course
        )

        self.question = Question.objects.create(
            summary="Test_question", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user
        )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=1.0,
            fixed_question_order=str(self.question)
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
            percent=1, marks_obtained=1
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

    def test_monitor_display_quizzes(self):
        """
            Check all the available quizzes in monitor
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:monitor'),
                                   follow=True
                                   )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/monitor.html")
        self.assertEqual(response.context['course_details'][0], self.course)
        self.assertEqual(response.context['msg'], "Monitor")

    def test_monitor_display_quiz_results(self):
        """
            Check all the quiz results in monitor
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:monitor', kwargs={'quiz_id': self.quiz.id}),
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/monitor.html")
        self.assertEqual(response.context['msg'], "Quiz Results")
        self.assertEqual(response.context['papers'][0], self.answerpaper)
        self.assertEqual(
            response.context['latest_attempts'][0],
            self.answerpaper
        )

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
                            'questionpaper_id': self.question_paper.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/user_data.html')
        self.assertEqual(
            response.context['data']['papers'][0],
            self.answerpaper
        )
        self.assertEqual(
            response.context['data']['profile'],
            self.student.profile
        )
        self.assertEqual(response.context['data']['user'], self.student)
        self.assertEqual(
            response.context['data']['questionpaperid'],
            str(self.question_paper.id)
        )

    def test_get_question_answer_for_answerpaper(self):
        """
            Check to get latest answer for questions in monitor
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:get_question_answer',
                    kwargs={'user_id': self.student.id,
                            'answerpaper_id': self.answerpaper.id,
                            'question_id': self.question.id}),
            follow=True
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['question'], self.question.description)
        self.assertEqual(data['user'], self.student.get_full_name().title())

    def test_get_question_answer_invalid_user(self):
        """
            Check to raise Http404 message for invalid user
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:get_question_answer',
                    kwargs={'user_id': self.student.id,
                            'answerpaper_id': self.answerpaper.id,
                            'question_id': self.question.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

        get_response = self.client.get(
            reverse('yaksh:get_question_answer',
                    kwargs={'user_id': self.student.id,
                            'answerpaper_id': self.answerpaper.id,
                            'question_id': self.question.id}),
            follow=True
        )
        self.assertEqual(get_response.status_code, 404)


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
            timezone='UTC'
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
            name="Python Course", enrollment="Open Enrollment",
            creator=self.user
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            language='Python', course=self.course
        )

        self.question = Question.objects.create(
            summary="Test_question", description="Add two numbers",
            points=1.0, language="python", type="code", user=self.user
        )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=1.0,
            fixed_question_order=str(self.question.id)
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
            marks_obtained=0.5
        )
        self.answerpaper.answers.add(self.new_answer)
        self.answerpaper.questions_answered.add(self.question)
        self.answerpaper.questions.add(self.question)
        self.data = {"quiz_id": self.quiz.id, "user_id": self.student.id}

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
        self.assertEqual(response.context['course_details'][0], self.course)

    def test_grade_user_get_quiz_users(self):
        """
            Check all the available users in quiz in grade user
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:grade_user', kwargs={"quiz_id": self.quiz.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/grade_user.html")
        self.assertEqual(
            response.context['users'][0]['user__first_name'],
            self.student.first_name
        )
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
            reverse('yaksh:grade_user', kwargs=self.data),
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
        self.client.get(
            reverse('yaksh:grade_user', kwargs=self.data),
            follow=True
        )
        question_marks = "q{0}_marks".format(self.question.id)
        data = {"quiz_id": self.quiz.id, "user_id": self.student.id,
                "attempt_number": self.answerpaper.attempt_number}
        response = self.client.post(
            reverse('yaksh:grade_user', kwargs=data),
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
            timezone='UTC'
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
            name="Python Course", enrollment="Enroll Request",
            creator=self.user
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo_quiz', pass_criteria=40,
            language='Python', course=self.course
        )

        self.question = Question.objects.create(
            summary="Test_question", description="Assignment Upload",
            points=1.0, language="python", type="upload", user=self.user
        )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=1.0,
            fixed_question_order=str(self.question.id)
        )
        self.question_paper.fixed_questions.add(self.question)

        # create assignment file
        assignment_file1 = SimpleUploadedFile("file1.txt", b"Test")
        assignment_file2 = SimpleUploadedFile("file2.txt", b"Test")
        assignment_file3 = SimpleUploadedFile("file3.txt", b"Test")
        self.assignment1 = AssignmentUpload.objects.create(
            user=self.student1,
            assignmentQuestion=self.question,
            assignmentFile=assignment_file1,
            question_paper=self.question_paper
        )
        self.assignment2 = AssignmentUpload.objects.create(
            user=self.student2,
            assignmentQuestion=self.question,
            assignmentFile=assignment_file2,
            question_paper=self.question_paper
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student1.delete()
        self.student2.delete()
        self.assignment1.delete()
        self.assignment2.delete()
        self.quiz.delete()
        self.course.delete()
        dir_name = self.quiz.description.replace(" ", "_")
        file_path = os.sep.join((settings.MEDIA_ROOT, dir_name))
        if os.path.exists(file_path):
            shutil.rmtree(file_path)

    def test_download_assignment_denies_student(self):
        """
            Check download assignment denies student
        """
        self.client.login(
            username=self.student1.username,
            password=self.student1_plaintext_pass
        )
        response = self.client.get(
            reverse(
                'yaksh:download_quiz_assignment',
                kwargs={'quiz_id': self.quiz.id}
            ),
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
        response = self.client.get(reverse('yaksh:download_quiz_assignment',
                                           kwargs={'quiz_id': self.quiz.id}),
                                   follow=True
                                   )
        file_name = "{0}_Assignment_files.zip".format(self.quiz.description)
        file_name = file_name.replace(" ", "_")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Disposition'),
            "attachment; filename={0}".format(file_name)
        )
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
            reverse(
                'yaksh:download_user_assignment',
                kwargs={'quiz_id': self.quiz.id,
                        'question_id': self.question.id,
                        'user_id': self.student2.id}
            ),
            follow=True
        )
        file_name = "{0}.zip".format(self.student2.get_full_name())
        file_name = file_name.replace(" ", "_")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Disposition'),
            "attachment; filename={0}".format(file_name)
        )
        zip_file = string_io(response.content)
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        self.assertIsNone(zipped_file.testzip())
        self.assertIn('file2.txt', zipped_file.namelist()[0])
        zip_file.close()
        zipped_file.close()


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
            timezone='UTC'
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
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='pre requisite quiz', pass_criteria=40,
            language='Python', prerequisite=None,
            course=self.course
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            language='Python', prerequisite=self.pre_req_quiz,
            course=self.course
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.pre_req_quiz.delete()
        self.course.delete()

    def test_add_quiz_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:add_quiz',
                    kwargs={'course_id': self.course.id}),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/addquiz/{0}/'.format(
                self.course.id
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
            reverse('yaksh:add_quiz', kwargs={'course_id': self.course.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_add_quiz_get(self):
        """
        GET request to add question should display add quiz form
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(reverse('yaksh:add_quiz',
                                   kwargs={'course_id': self.course.id})
                                   )
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
            reverse('yaksh:edit_quiz',
                    kwargs={'course_id': self.course.id,
                            'quiz_id': self.quiz.id}),
            data={
                'start_date_time': '2016-01-10 09:00:15',
                'end_date_time': '2016-01-15 09:00:15',
                'duration': 30,
                'active': False,
                'attempts_allowed': 5,
                'time_between_attempts': 1,
                'description': 'updated demo quiz',
                'pass_criteria': 40,
                'language': 'java',
                'instructions': "Demo Instructions",
                'prerequisite': self.pre_req_quiz.id,
                'course': self.course.id
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
        self.assertEqual(updated_quiz.language, 'java')
        self.assertEqual(updated_quiz.prerequisite, self.pre_req_quiz)
        self.assertEqual(updated_quiz.course, self.course)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exam/manage/courses/')

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
                    kwargs={"course_id": self.course.id}),
            data={
                'start_date_time': '2016-01-10 09:00:15',
                'end_date_time': '2016-01-15 09:00:15',
                'duration': 50,
                'active': True,
                'attempts_allowed': -1,
                'time_between_attempts': 2,
                'description': 'new demo quiz',
                'pass_criteria': 50,
                'language': 'python',
                'instructions': "Demo Instructions",
                'prerequisite': self.pre_req_quiz.id,
                'course': self.course.id
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
        self.assertEqual(new_quiz.language, 'python')
        self.assertEqual(new_quiz.prerequisite, self.pre_req_quiz)
        self.assertEqual(new_quiz.course, self.course)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exam/manage/courses/')


class TestAddTeacher(TestCase):
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
            timezone='UTC'
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
            language='Python', prerequisite=None,
            course=self.course
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            language='Python', prerequisite=self.pre_req_quiz,
            course=self.course
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.pre_req_quiz.delete()
        self.course.delete()

    def test_add_teacher_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:add_teacher',
                    kwargs={'course_id': self.course.id}),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/addteacher/{0}/'.format(
                self.course.id
            )
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
                    kwargs={'course_id': self.course.id}),
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
                    kwargs={'course_id': self.course.id})
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
                    kwargs={'course_id': self.course.id}),
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
            timezone='UTC'
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
            language='Python', prerequisite=None,
            course=self.course
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            language='Python', prerequisite=self.pre_req_quiz,
            course=self.course
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.pre_req_quiz.delete()
        self.course.delete()

    def test_remove_teacher_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:remove_teacher',
                    kwargs={'course_id': self.course.id}),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/remove_teachers/{0}/'.format(
                self.course.id
            )
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
                    kwargs={'course_id': self.course.id}),
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
                    kwargs={'course_id': self.course.id}),
            data={'remove': teacher_id_list}
        )

        self.assertEqual(response.status_code, 302)
        redirect_destination = '/exam/manage/courses'
        self.assertRedirects(
            response, redirect_destination, status_code=302,
            target_status_code=301
        )
        for t_id in teacher_id_list:
            teacher = User.objects.get(id=t_id)
            self.assertNotIn(teacher, self.course.teachers.all())


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
            timezone='UTC'
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
            timezone='UTC'
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

        self.user1_course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user1
        )

        self.user2_course = Course.objects.create(
            name="Java Course",
            enrollment="Enroll Request", creator=self.user2
        )

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.user2.delete()
        self.student.delete()
        self.user1_course.delete()
        self.user2_course.delete()

    def test_courses_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:courses'),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/courses/'
        )
        self.assertRedirects(response, redirect_destination)

    def test_courses_denies_non_moderator(self):
        """
        If not moderator redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:courses'),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_courses_get(self):
        """
        GET request should return courses page
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:courses'),
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/courses.html')
        self.assertIn(self.user1_course, response.context['courses'])
        self.assertNotIn(self.user2_course, response.context['courses'])


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
            timezone='UTC'
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
            language='Python', prerequisite=None,
            course=self.course
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            language='Python', prerequisite=self.pre_req_quiz,
            course=self.course
        )

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.student.delete()
        self.quiz.delete()
        self.pre_req_quiz.delete()
        self.course.delete()

    def test_add_course_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(reverse('yaksh:add_course'),
                                   follow=True
                                   )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/add_course/'
        )
        self.assertRedirects(response, redirect_destination)

    def test_add_course_denies_non_moderator(self):
        """
        If not moderator in redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:add_course'),
            follow=True
        )
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
            data={
                'name': 'new_demo_course_1',
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
        self.assertRedirects(response, '/exam/manage/')


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
            timezone='UTC'
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
            timezone='UTC'
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

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.user2.delete()
        self.student.delete()
        self.user1_course.delete()

    def test_course_detail_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:course_detail',
                    kwargs={'course_id': self.user1_course.id}),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/manage/course_detail/{0}/'.format(
                self.user1_course.id
            )
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
                    kwargs={'course_id': self.user1_course.id}),
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
                    kwargs={'course_id': self.user1_course.id}),
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
                    kwargs={'course_id': self.user1_course.id}),
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
        self.assertEqual(response.status_code, 200)
        self.assertSequenceEqual([self.student], enrolled_student)

    def test_student_course_enroll_post(self):
        """
            Enroll student in a course using post request
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:enroll_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'check': self.student1.id}
        )
        enrolled_student = self.user1_course.students.all()
        self.assertEqual(response.status_code, 200)
        self.assertSequenceEqual([self.student1], enrolled_student)

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
        self.assertEqual(response.status_code, 200)
        self.assertSequenceEqual([self.student], enrolled_student)

    def test_student_course_reject_post(self):
        """
            Reject student in a course using post request
        """
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:reject_users',
                    kwargs={'course_id': self.user1_course.id}),
            data={'check': self.student1.id}
        )
        enrolled_student = self.user1_course.rejected.all()
        self.assertEqual(response.status_code, 200)
        self.assertSequenceEqual([self.student1], enrolled_student)

    def test_toggle_course_status_get(self):
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:toggle_course_status',
                    kwargs={'course_id': self.user1_course.id})
        )
        self.assertEqual(response.status_code, 200)
        course = Course.objects.get(name="Python Course")
        self.assertFalse(course.active)
        self.assertEqual(self.user1_course, response.context['course'])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/course_detail.html')

    def test_send_mail_to_course_students(self):
        """ Check if bulk mail is sent to multiple students
            enrolled in a course
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
        recipients = mail.outbox[0].recipients()
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
        self.assertEqual(get_response.context['state'], 'mail')


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
            timezone='UTC'
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
            timezone='UTC'
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

    def test_enroll_request_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse('yaksh:enroll_request',
                    kwargs={'course_id': self.course.id}),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/enroll_request/{}/'.format(
                self.course.id
            )
        )
        self.assertRedirects(response, redirect_destination)

    def test_enroll_request_get_for_student(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:enroll_request',
                    kwargs={'course_id': self.course.id}),
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
                    kwargs={'course_id': self.course.id}),
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
        self.user2 = User.objects.get(username="demo_user3")
        self.course = Course.objects.create(
            name="Python Course", enrollment="Enroll Request",
            creator=self.user1
        )

        self.question = Question.objects.create(
            summary='Dummy', points=1, type='code', user=self.user1
        )

        self.quiz = Quiz.objects.create(
            time_between_attempts=0, course=self.course,
            description='demo quiz', language='Python'
        )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=1.0
        )
        self.question_paper.fixed_questions.add(self.question)
        self.question_paper.save()

        self.ans_paper = AnswerPaper.objects.create(
            user_id=self.user2.id,
            attempt_number=1, question_paper=self.question_paper,
            start_time=timezone.now(), user_ip='101.0.0.1',
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
            '/exam/login/?next=/exam/view_answerpaper/{0}/'.format(
                self.question_paper.id
            )
        )

        # When
        response = self.client.get(
            reverse('yaksh:view_answerpaper',
                    kwargs={'questionpaper_id': self.question_paper.id}),
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
                    kwargs={'questionpaper_id': self.question_paper.id}),
            follow=True
        )

        # Then
        self.assertRedirects(response, '/exam/quizzes/')

    def test_can_view_answerpaper(self):
        # Given, user enrolled and can view
        user3 = User.objects.get(username="demo_user3")
        self.course.students.add(user3)
        self.course.save()
        AnswerPaper.objects.get(pk=self.ans_paper.id)
        self.quiz.view_answerpaper = True
        self.quiz.save()
        self.client.login(
            username=user3.username,
            password=self.plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:view_answerpaper',
                    kwargs={'questionpaper_id': self.question_paper.id}),
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
                    kwargs={'questionpaper_id': 190}),
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
                    kwargs={'questionpaper_id': self.question_paper.id}),
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
            timezone='UTC'
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
            timezone='UTC'
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

    def test_self_enroll_denies_anonymous(self):
        response = self.client.get(
            reverse('yaksh:self_enroll',
                    kwargs={'course_id': self.course.id}),
            follow=True
        )
        redirect_destination = (
            '/exam/login/?next=/exam/self_enroll/{}/'.format(
                self.course.id
            )
        )
        self.assertRedirects(response, redirect_destination)

    def test_enroll_request_get_for_student(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(
            reverse('yaksh:self_enroll',
                    kwargs={'course_id': self.course.id}),
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
                    kwargs={'course_id': self.course.id}),
            follow=True
        )
        self.assertRedirects(response, '/exam/manage/')


class TestGrader(TestCase):
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
            timezone='UTC'
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

        self.quiz = Quiz.objects.create(
            time_between_attempts=0, course=self.course,
            description='demo quiz', language='Python'
        )

        self.question_paper = QuestionPaper.objects.create(
            quiz=self.quiz, total_marks=1.0
        )
        self.question_paper.fixed_questions.add(self.question)
        self.question_paper.save()

        self.answerpaper = AnswerPaper.objects.create(
            user_id=3,
            attempt_number=1, question_paper=self.question_paper,
            start_time=timezone.now(), user_ip='101.0.0.1',
            end_time=timezone.now()+timezone.timedelta(minutes=20)
        )

    def tearDown(self):
        User.objects.all().delete()
        Course.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        QuestionPaper.objects.all().delete()
        AnswerPaper.objects.all().delete()

    def test_grader_denies_anonymous(self):
        # Given
        redirect_destination = ('/exam/login/?next=/exam/manage/grader/')

        # When
        response = self.client.get(reverse('yaksh:grader'), follow=True)

        # Then
        self.assertRedirects(response, redirect_destination)

    def test_grader_denies_students(self):
        # Given
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # When
        response = self.client.get(reverse('yaksh:grader'), follow=True)

        # Then
        self.assertEqual(response.status_code, 404)

    def test_regrade_denies_anonymous(self):
        # Given
        redirect_destination = dedent('''\
        /exam/login/?next=/exam/manage/regrade/answerpaper/{}/{}/{}/'''.format(
            self.course.id, self.question.id, self.answerpaper.id
        )
        )

        # When
        response = self.client.get(
            reverse('yaksh:regrade',
                    kwargs={'course_id': self.course.id,
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
            reverse('yaksh:regrade',
                    kwargs={'course_id': self.course.id,
                            'question_id': self.question.id,
                            'answerpaper_id': self.answerpaper.id}),
            follow=True
        )

        # Then
        self.assertEqual(response.status_code, 404)

    def test_grader_by_moderator(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # When
        response = self.client.get(reverse('yaksh:grader'), follow=True)

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertTrue('courses' in response.context)
        self.assertTemplateUsed(response, 'yaksh/regrade.html')

    def test_regrade_by_moderator(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:regrade',
                    kwargs={'course_id': self.course.id,
                            'question_id': self.question.id,
                            'answerpaper_id': self.answerpaper.id}),
            follow=True
        )

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertTrue('courses' in response.context)
        self.assertTrue('details' in response.context)
        self.assertTemplateUsed(response, 'yaksh/regrade.html')

    def test_regrade_denies_moderator_not_in_course(self):
        # Given
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )

        # When
        response = self.client.get(
            reverse('yaksh:regrade',
                    kwargs={'course_id': self.course.id,
                            'question_id': self.question.id,
                            'answerpaper_id': self.answerpaper.id}),
            follow=True
        )

        # Then
        self.assertEqual(response.status_code, 404)


class TestPasswordReset(TestCase):
    def setUp(self):
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

    def test_password_reset_post(self):
        """
        POST request to password_reset view should return a valid response
        """
        # When
        response = self.client.post(
            reverse('password_reset'),
            data={'email': self.user1.email}
        )

        # Then
        self.assertEqual(response.context['email'], self.user1.email)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exam/reset/password_reset/mail_sent/')

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
        self.assertIsNotNone(
            authenticate(username='demo_user1', password='new_demo1_pass')
        )
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
            timezone='UTC'
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
            language='Python', course=self.course
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
            marks_obtained=0.5
        )
        self.answerpaper.answers.add(self.new_answer)
        self.answerpaper.questions_answered.add(self.question)
        self.answerpaper.questions.add(self.question)

        # moderator trial answerpaper
        self.trial_quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='trial quiz', pass_criteria=40,
            language='Python', course=self.course, is_trial=True
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
            marks_obtained=0.5
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
        self.assertRedirects(response, '/exam/quizzes/')

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
        self.assertEqual(
            response.context['trial_paper'][0],
            self.trial_answerpaper
        )
        paper, answer_papers, users_passed, users_failed =\
            response.context['users_per_paper'][0]
        self.assertEqual(paper, self.question_paper)
        self.assertEqual(answer_papers[0], self.answerpaper)
        self.assertEqual(users_passed, 1)
        self.assertEqual(users_failed, 0)

    def test_moderator_dashboard_delete_trial_papers(self):
        """
            Check moderator dashboard to delete trial papers
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        self.course.is_trial = True
        self.course.save()
        response = self.client.post(
            reverse('yaksh:manage'),
            data={'delete_paper': [self.trial_answerpaper.id]}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/moderator_dashboard.html")
        updated_answerpaper = AnswerPaper.objects.filter(user=self.user)
        updated_quiz = Quiz.objects.filter(
            description=self.trial_question_paper.quiz.description
        )
        updated_course = Course.objects.filter(
            name=self.trial_question_paper.quiz.course.name
        )
        self.assertSequenceEqual(updated_answerpaper, [])
        self.assertSequenceEqual(updated_quiz, [])
        self.assertSequenceEqual(updated_course, [])


class TestUserLogin(TestCase):
    def setUp(self):
        self.client = Client()

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

    def test_successful_user_login(self):
        """
            Check if user is successfully logged in
        """
        response = self.client.post(
            reverse('yaksh:login'),
            data={
                'username': self.user1.username,
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
            data={
                'username': self.user1.username,
                'password': self.user1_plaintext_pass
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "yaksh/activation_status.html")


class TestDownloadcsv(TestCase):
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
            timezone='UTC'
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
            language='Python', course=self.course
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
            marks_obtained=0.5
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

    def test_download_csv_denies_student(self):
        """
            Check download csv denies student
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_csv',
                    kwargs={"questionpaper_id": self.question_paper.id}),
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
        response = self.client.get(
            reverse('yaksh:download_csv',
                    kwargs={"questionpaper_id": self.question_paper.id}),
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
        file_name = "{0}.csv".format(self.course.name.lower())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment; filename="{0}"'.format(file_name)
        )

    def test_download_quiz_csv(self):
        """
            Check for csv result of a quiz
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:download_csv',
                    kwargs={'questionpaper_id': self.question_paper.id}),
            follow=True
        )
        file_name = "{0}.csv".format(self.quiz.description)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment; filename="{0}"'.format(file_name)
        )


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
            timezone='UTC'
        )
        self.mod_group.user_set.add(self.user)
        self.question = Question.objects.create(
            summary="Test_question1", description="Add two numbers",
            points=2.0, language="python", type="code", user=self.user,
            active=True
        )
        self.question1 = Question.objects.create(
            summary="Test_question2", description="Add two numbers",
            points=1.0, language="python", type="mcq", user=self.user,
            active=True
        )

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
            reverse('yaksh:show_questions'),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertEqual(response.context['questions'][0], self.question)

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
            data={
                'question': [self.question.id],
                'download': 'download'
            }
        )
        file_name = "{0}_questions.zip".format(self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Disposition'),
            "attachment; filename={0}".format(file_name)
        )
        zip_file = string_io(response.content)
        zipped_file = zipfile.ZipFile(zip_file, 'r')
        self.assertIsNone(zipped_file.testzip())
        self.assertIn('questions_dump.yaml', zipped_file.namelist())
        zip_file.close()
        zipped_file.close()

        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'question': [], 'download': 'download'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertIn("download", response.context['msg'])

    def test_upload_questions(self):
        """
            Check for uploading questions zip file
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ques_file = os.path.join(settings.FIXTURE_DIRS, "demo_questions.zip")
        f = open(ques_file, 'rb')
        questions_file = SimpleUploadedFile(
            ques_file, f.read(), content_type="application/zip"
        )
        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'file': questions_file, 'upload': 'upload'}
        )
        summaries = ['Roots of quadratic equation', 'Print Output',
                     'Adding decimals', 'For Loop over String',
                     'Hello World in File', 'Extract columns from files',
                     'Check Palindrome', 'Add 3 numbers', 'Reverse a string'
                     ]
        uploaded_ques = Question.objects.filter(
            active=True, summary__in=summaries,
            user=self.user
        ).count()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertEqual(uploaded_ques, 9)
        f.close()
        dummy_file = SimpleUploadedFile("test.txt", b"test")
        response = self.client.post(
            reverse('yaksh:show_questions'),
            data={'file': dummy_file, 'upload': 'upload'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/showquestions.html')
        self.assertIn("ZIP file", response.context['message'])

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
            data={'question': [self.question.id], 'test': 'test'}
        )
        trial_que_paper = QuestionPaper.objects.get(
            quiz__description="trial_questions"
        )
        redirection_url = "/exam/start/1/{}".format(trial_que_paper.id)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirection_url, target_status_code=301)

    def test_ajax_questions_filter(self):
        """
            Check for filter questions based type, marks and
            language of a question
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.post(
            reverse('yaksh:questions_filter'),
            data={
                'question_type': 'mcq', 'marks': '1.0', 'language': 'python'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/ajax_question_filter.html')
        self.assertEqual(response.context['questions'][0], self.question1)


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
            timezone='UTC'
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
            language='Python', course=self.course
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
            percent=1, marks_obtained=1
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
                    kwargs={"questionpaper_id": self.question_paper.id}),
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
                    kwargs={'questionpaper_id': self.question_paper.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/statistics_question.html')
        self.assertEqual(response.context['quiz'], self.quiz)
        self.assertEqual(
            response.context['attempts'][0],
            self.answerpaper.attempt_number
        )
        self.assertEqual(
            response.context['questionpaper_id'],
            str(self.question_paper.id)
        )

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
                    kwargs={
                        'questionpaper_id': self.question_paper.id,
                        'attempt_number': self.answerpaper.attempt_number
                    }),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/statistics_question.html')
        self.assertSequenceEqual(
            response.context['question_stats'][self.question],
            [1, 1]
        )
        self.assertEqual(response.context['attempts'][0], 1)
        self.assertEqual(response.context['total'], 1)


class TestConsumers(ChannelTestCase):
    def setUp(self):
        self.client = WSClient()

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
            timezone='UTC'
        )

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

        # Create a new chat room
        self.room = Room.objects.create(
            course=self.course,
            label="test_room"
        )

    def tearDown(self):
        self.room.delete()
        self.user.delete()
        self.student.delete()
        self.course.delete()
        self.mod_group.delete()

    def test_consumers_ws_connect_success(self):
        # Check for successful connection
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ws_correct_path = '/chat/test_room/{0}'.format(self.room.course_id)
        self.client.send_and_consume(u'websocket.connect',
                                     path=ws_correct_path)
        # check that there is nothing to receive
        self.assertIsNone(self.client.receive())

    def test_consumers_ws_connect_invalid_path(self):
        # Check for wrong path
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ws_wrong_path = '/chatting/test_room/{0}'.format(self.room.course_id)
        self.client.send_and_consume(
            u'websocket.connect', path=ws_wrong_path,
            check_accept=False
        )
        self.assertEqual(self.client.receive(), {"close": True})

    def test_consumers_ws_connect_value_error(self):
        # Check if path has all the information
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ws_path = '/chat/test_room/'
        self.client.send_and_consume(
            u'websocket.connect', path=ws_path,
            check_accept=False
        )
        self.assertEqual(self.client.receive(), {"close": True})

    def test_consumers_ws_connect_room_does_not_exist(self):
        # Check if path has all the information
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ws_path = '/chat/test/1'
        self.client.send_and_consume(
            u'websocket.connect', path=ws_path,
            check_accept=False
        )
        self.assertEqual(self.client.receive(), {"close": True})

    def test_consumers_ws_connect_incorrect_user(self):
        # Check if user is a course creator or teacher or student
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        ws_correct_path = '/chat/test_room/{0}'.format(self.room.course_id)
        self.client.send_and_consume(
            u'websocket.connect', path=ws_correct_path,
            check_accept=False
        )
        self.assertEqual(self.client.receive(), {"close": True})

    def test_consumers_ws_receive_success(self):
        # Check if message is received successfully
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ws_correct_path = '/chat/test_room/{0}'.format(self.room.course_id)
        self.client.send_and_consume(u'websocket.connect',
                                     path=ws_correct_path)
        self.client.send_and_consume(
            u'websocket.receive', path=ws_correct_path,
            text={"message": "Test", "sender_id": self.user.id}
        )
        message = self.client.receive()
        user_full_name = self.user.get_full_name().title()
        self.assertTrue(message['success'])
        self.assertEqual(message['messages']['sender'], self.user.id)
        self.assertEqual(message['messages']['message'], "Test")
        self.assertEqual(message['messages']['sender_name'], user_full_name)

    def test_consumers_ws_receive_incorrect_json_data(self):
        # Check for incorrect json data
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ws_path = '/chat/test_room/{0}'.format(self.room.course_id)
        self.client.send_and_consume(u'websocket.connect', path=ws_path)
        self.client.send_and_consume(
            u'websocket.receive', path=ws_path,
            check_accept=False, text={"message": "Test"}
        )
        self.assertEqual(self.client.receive(), {"close": True})

    def test_consumers_ws_receive_incorrect_key_error(self):
        # Check for no channel session
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ws_path = '/chat/test_room/{0}'.format(self.room.course_id)
        self.client.send_and_consume(
            u'websocket.receive', path=ws_path,
            check_accept=False
        )
        self.assertEqual(self.client.receive(), {"close": True})

    def test_consumers_ws_disconnect(self):
        # Check for disconnect channel
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        ws_path = '/chat/test_room/{0}'.format(self.room.course_id)
        self.client.send_and_consume(u'websocket.connect', path=ws_path)
        self.client.send_and_consume(
            u'websocket.disconnect', path=ws_path,
            check_accept=False
        )
        self.assertEqual(self.client.receive(), {"close": True})


class TestChatMessages(TestCase):
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
            timezone='UTC'
        )

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

        self.course1 = Course.objects.create(
            name="Python Course",
            enrollment="Open Enrollment", creator=self.user
        )

        self.quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0, tzone),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzone),
            duration=30, active=True, instructions="Demo Instructions",
            attempts_allowed=-1, time_between_attempts=0,
            description='demo quiz', pass_criteria=40,
            language='Python', course=self.course1
        )

        self.course2 = Course.objects.create(
            name="Demo Course",
            enrollment="Open Enrollment", creator=self.user
        )

        self.room = Room.objects.create(
            course=self.course1,
            label="test_room"
        )
        self.message = Message.objects.create(
            room=self.room, sender=self.user,
            message="Test", timestamp=timezone.now()
        )

    def tearDown(self):
        Room.objects.all().delete()
        User.objects.all().delete()
        Course.objects.all().delete()
        Message.objects.all().delete()

    def test_get_chat_messages(self):
        # Check to get all messages for a room
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:new_room',
                    kwargs={'course_id': self.course1.id}),
            follow=True
        )
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message['success'])
        self.assertEqual(message['room_label'], 'test_room')
        self.assertEqual(message['messages'][0]['message'], 'Test')
        self.assertEqual(message['messages'][0]['sender'], self.user.id)

    def test_create_new_room(self):
        # Check to create a new room
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:new_room',
                    kwargs={'course_id': self.course2.id}),
            follow=True
        )
        new_room = Room.objects.get(course_id=self.course2.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(new_room.course_id, self.course2.id)

    def test_chat_room_invalid_user(self):
        # Check if user is a course creator or teacher or student
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:new_room',
                    kwargs={'course_id': self.course1.id}),
            follow=True
        )
        message = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(message['success'])
        err_msg = "You do not belong to this course"
        self.assertEqual(message['messages'][0]['message'], err_msg)

    def test_toggle_chat_status(self):
        # Check quiz chat toggle status
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse('yaksh:toggle_quiz_chat',
                    kwargs={'quiz_id': self.quiz.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.quiz.enable_chat)
        updated_quiz = Quiz.objects.get(id=self.quiz.id)
        self.assertTrue(updated_quiz.enable_chat)
