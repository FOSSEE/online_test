from datetime import datetime
import pytz
import os
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import Client
from django.utils import timezone

from yaksh.models import User, Profile, Question, Quiz, QuestionPaper,\
    QuestionSet, AnswerPaper, Answer, Course, StandardTestCase,\
    StdIOBasedTestCase, has_profile


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


    def test_has_profile_for_user_without_profile(self):
        """
        If no profile exists for user passed as argument return False
        """
        has_profile_status = has_profile(self.user1)
        self.assertFalse(has_profile_status)

    def test_has_profile_for_user_with_profile(self):
        """
        If profile exists for user passed as argument return True
        """
        has_profile_status = has_profile(self.user2)
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

    def test_edit_profile_post(self):
        """
        POST request to edit_profile view should update the user's profile
        """
        self.client.login(
            username=self.user2.username,
            password=self.user2_plaintext_pass
        )
        response = self.client.post(reverse('yaksh:edit_profile'),
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

        self.course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user)

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
        response = self.client.get(reverse('yaksh:add_quiz',
                                           kwargs={'course_id': self.course.id}),
                                   follow=True
                                   )
        redirect_destination = '/exam/login/?next=/exam/manage/addquiz/{0}/'.format(self.course.id)
        self.assertRedirects(response, redirect_destination)

    def test_add_quiz_denies_non_moderator(self):
        """
        If not moderator in redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        course_id = self.course.id
        response = self.client.get(reverse('yaksh:add_quiz',
                                           kwargs={'course_id': self.course.id}),
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
        response = self.client.post(reverse('yaksh:edit_quiz',
            kwargs={'course_id':self.course.id, 'quiz_id': self.quiz.id}),
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
        self.assertEqual(updated_quiz.start_date_time,
            datetime(2016, 1, 10, 9, 0, 15, 0, tzone)
        )
        self.assertEqual(updated_quiz.end_date_time,
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
        response = self.client.post(reverse('yaksh:add_quiz', kwargs={"course_id": self.course.id}),
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
        self.assertEqual(new_quiz.start_date_time,
            datetime(2016, 1, 10, 9, 0, 15, 0, tzone)
        )
        self.assertEqual(new_quiz.end_date_time,
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

        self.course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user)

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
        response = self.client.get(reverse('yaksh:add_teacher',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        redirect_destination = ('/exam/login/?next=/exam'
            '/manage/addteacher/{0}/'.format(self.course.id))
        self.assertRedirects(response, redirect_destination)

    def test_add_teacher_denies_non_moderator(self):
        """
        If not moderator redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(reverse('yaksh:add_teacher',
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
        response = self.client.get(reverse('yaksh:add_teacher',
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

            teacher_profile = Profile.objects.create(
                user=teacher,
                roll_number='T{}'.format(i),
                institute='IIT',
                department='Chemical',
                position='Teacher',
                timezone='UTC'
            )
            teacher_id_list.append(teacher.id)

        response = self.client.post(reverse('yaksh:add_teacher',
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

        self.course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user)

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
        response = self.client.get(reverse('yaksh:remove_teacher',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        redirect_destination = ('/exam/login/?next=/exam'
            '/manage/remove_teachers/{0}/'.format(self.course.id))
        self.assertRedirects(response, redirect_destination)

    def test_remove_teacher_denies_non_moderator(self):
        """
        If not moderator redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(reverse('yaksh:remove_teacher',
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

            teacher_profile = Profile.objects.create(
                user=teacher,
                roll_number='RT{}'.format(i),
                institute='IIT',
                department='Aeronautical',
                position='Teacher',
                timezone='UTC'
            )
            teacher_id_list.append(teacher.id)
            self.course.teachers.add(teacher)

        response = self.client.post(reverse('yaksh:remove_teacher',
                kwargs={'course_id': self.course.id}
            ),
            data={'remove': teacher_id_list}
        )

        self.assertEqual(response.status_code, 302)
        redirect_destination = '/exam/manage/courses'
        self.assertRedirects(response, redirect_destination,
            status_code=302,
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

        self.user1_course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user1)

        self.user2_course = Course.objects.create(name="Java Course",
            enrollment="Enroll Request", creator=self.user2)

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
        response = self.client.get(reverse('yaksh:courses'),
            follow=True
        )
        redirect_destination = ('/exam/login/?next=/exam'
            '/manage/courses/')
        self.assertRedirects(response, redirect_destination)

    def test_courses_denies_non_moderator(self):
        """
        If not moderator redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(reverse('yaksh:courses'),
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
        response = self.client.get(reverse('yaksh:courses'),
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

        self.course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user)

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
        redirect_destination = ('/exam/login/?next=/'
            'exam/manage/add_course/')
        self.assertRedirects(response, redirect_destination)

    def test_add_course_denies_non_moderator(self):
        """
        If not moderator in redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        course_id = self.course.id
        response = self.client.get(reverse('yaksh:add_course'),
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

        response = self.client.post(reverse('yaksh:add_course'),
            data={'name': 'new_demo_course_1',
                'active': True,
                'enrollment': 'open'
            }
        )
        course_list = Course.objects.all().order_by('-id')
        new_course = course_list[0]
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

        # Add to moderator group
        self.mod_group.user_set.add(self.user1)
        self.mod_group.user_set.add(self.user2)

        self.user1_course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user1)

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
        response = self.client.get(reverse('yaksh:course_detail',
                kwargs={'course_id': self.user1_course.id}
            ),
            follow=True
        )
        redirect_destination = ('/exam/login/?next=/exam/'
            'manage/course_detail/1/')
        self.assertRedirects(response, redirect_destination)

    def test_course_detail_denies_non_moderator(self):
        """
        If not moderator redirect to 404
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(reverse('yaksh:course_detail',
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
        response = self.client.get(reverse('yaksh:course_detail',
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
        response = self.client.get(reverse('yaksh:course_detail',
                kwargs={'course_id': self.user1_course.id}
            ),
            follow=True
        )
        self.assertEqual(self.user1_course, response.context['course'])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'yaksh/course_detail.html')


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

        self.course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user1)

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
        response = self.client.get(reverse('yaksh:enroll_request',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        redirect_destination = ('/exam/login/?next=/exam'
            '/enroll_request/{}/'.format(self.course.id))
        self.assertRedirects(response, redirect_destination)

    def test_enroll_request_get_for_student(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(reverse('yaksh:enroll_request',
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

        response = self.client.get(reverse('yaksh:enroll_request',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        self.assertRedirects(response, '/exam/manage/')


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

        self.user1 = User.objects.get(pk=1)

        self.course = Course.objects.create(name="Python Course",
                                       enrollment="Enroll Request",
                                       creator=self.user1)

        self.question = Question.objects.create(summary='Dummy', points=1,
                                               type='code', user=self.user1)

        self.quiz = Quiz.objects.create(time_between_attempts=0, course=self.course,
                                        description='demo quiz', language='Python')

        self.question_paper = QuestionPaper.objects.create(quiz=self.quiz,
            total_marks=1.0)
        self.question_paper.fixed_questions.add(self.question)
        self.question_paper.save()

        AnswerPaper.objects.create(user_id=3,
                attempt_number=1, question_paper=self.question_paper,
                start_time=timezone.now(), user_ip='101.0.0.1',
                end_time=timezone.now()+timezone.timedelta(minutes=20))

    def tearDown(self):
        User.objects.all().delete()
        Course.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        QuestionPaper.objects.all().delete()
        AnswerPaper.objects.all().delete()

    def test_anonymous_user(self):
        # Given, user not logged in
        redirect_destination = ('/exam/login/?next=/exam'
            '/view_answerpaper/{0}/'.format(self.question_paper.id))

        # When
        response = self.client.get(reverse('yaksh:view_answerpaper',
                kwargs={'questionpaper_id': self.question_paper.id}
            ),
            follow=True
        )

        # Then
        self.assertRedirects(response, redirect_destination)

    def test_cannot_view(self):
        # Given, enrolled user tries to view when not permitted by moderator
        user2 = User.objects.get(pk=2)
        self.course.students.add(user2)
        self.course.save()
        self.quiz.view_answerpaper = False
        self.quiz.save()
        self.client.login(
            username=user2.username,
            password=self.plaintext_pass
        )

        # When
        response = self.client.get(reverse('yaksh:view_answerpaper',
                kwargs={'questionpaper_id': self.question_paper.id}
            ),
            follow=True
        )

        # Then
        self.assertRedirects(response, '/exam/quizzes/')

    def test_can_view(self):
        # Given, user enrolled and can view
        user3 = User.objects.get(pk=3)
        self.course.students.add(user3)
        self.course.save()
        answerpaper = AnswerPaper.objects.get(pk=1)
        self.quiz.view_answerpaper = True
        self.quiz.save()
        self.client.login(
            username=user3.username,
            password=self.plaintext_pass
        )

        # When
        response = self.client.get(reverse('yaksh:view_answerpaper',
                kwargs={'questionpaper_id': self.question_paper.id}
            ),
            follow=True
        )

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertTrue('data' in response.context)
        self.assertTrue('quiz' in response.context)
        self.assertTemplateUsed(response, 'yaksh/view_answerpaper.html')


        # When, wrong question paper id
        response = self.client.get(reverse('yaksh:view_answerpaper',
                kwargs={'questionpaper_id': 190}
            ),
            follow=True
        )

        # Then
        self.assertEqual(response.status_code, 404)


    def test_view_when_not_enrolled(self):
        # Given, user tries to view when not enrolled in the course
        user2 = User.objects.get(pk=2)
        self.client.login(
            username=user2.username,
            password=self.plaintext_pass
        )
        self.course.students.remove(user2)
        self.course.save()
        self.quiz.view_answerpaper = True
        self.quiz.save()

        # When
        response = self.client.get(reverse('yaksh:view_answerpaper',
                kwargs={'questionpaper_id': self.question_paper.id}
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

        self.course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user1)

    def tearDown(self):
        self.client.logout()
        self.user1.delete()
        self.user2.delete()
        self.student.delete()
        self.course.delete()

    def test_self_enroll_denies_anonymous(self):
        response = self.client.get(reverse('yaksh:self_enroll',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        redirect_destination = ('/exam/login/?next=/exam'
            '/self_enroll/{}/'.format(self.course.id))
        self.assertRedirects(response, redirect_destination)

    def test_enroll_request_get_for_student(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        response = self.client.get(reverse('yaksh:self_enroll',
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

        response = self.client.get(reverse('yaksh:self_enroll',
                kwargs={'course_id': self.course.id}
            ),
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

        self.course = Course.objects.create(name="Python Course",
            enrollment="Enroll Request", creator=self.user1)

        self.question = Question.objects.create(summary='Dummy', points=1,
                                               type='code', user=self.user1)

        self.quiz = Quiz.objects.create(time_between_attempts=0, course=self.course,
                                        description='demo quiz', language='Python')

        self.question_paper = QuestionPaper.objects.create(quiz=self.quiz,
            total_marks=1.0)
        self.question_paper.fixed_questions.add(self.question)
        self.question_paper.save()

        self.answerpaper = AnswerPaper.objects.create(user_id=3,
                attempt_number=1, question_paper=self.question_paper,
                start_time=timezone.now(), user_ip='101.0.0.1',
                end_time=timezone.now()+timezone.timedelta(minutes=20))

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
        redirect_destination = ('/exam/login/?next=/exam/manage/regrade/answerpaper/1/1/1/')

        # When
        response = self.client.get(reverse('yaksh:regrade',
            kwargs={'course_id': self.course.id,
                'question_id': self.question.id,
                'answerpaper_id': self.answerpaper.id}),
            follow=True)

        # Then
        self.assertRedirects(response, redirect_destination)


    def test_regrade_denies_students(self):
        # Given
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # When
        response = self.client.get(reverse('yaksh:regrade',
                kwargs={'course_id': self.course.id,
                    'question_id': self.question.id,
                    'answerpaper_id': self.answerpaper.id}),
                follow=True)

        # Then
        self.assertEqual(response.status_code, 404)


    def test_grader_by_moderator(self):
        # Given
        self.client.login(
            username=self.user1.username,
            password=self.user1_plaintext_pass
        )

        # When
        response = self.client.get(reverse('yaksh:grader'),
                follow=True)

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
        response = self.client.get(reverse('yaksh:regrade',
            kwargs={'course_id': self.course.id,
                'question_id': self.question.id,
                'answerpaper_id': self.answerpaper.id}),
            follow=True)

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
        response = self.client.get(reverse('yaksh:regrade',
            kwargs={'course_id': self.course.id,
                'question_id': self.question.id,
                'answerpaper_id': self.answerpaper.id}),
            follow=True)

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
        response = self.client.post(reverse('password_reset'),
            data={
                'email': self.user1.email,
            }
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
        response = self.client.post(reverse('password_change'),
            data={
                'old_password': self.user1_plaintext_pass,
                'new_password1': 'new_demo1_pass',
                'new_password2': 'new_demo1_pass'
            }
        )

        # Then
        self.assertIsNotNone(authenticate(username='demo_user1', password='new_demo1_pass'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/exam/reset/password_change/done/')

        # Finally
        self.client.logout()
