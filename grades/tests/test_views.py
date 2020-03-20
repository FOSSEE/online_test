from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from grades.models import GradingSystem


def setUpModule():
    User.objects.create_user(username='grades_user', password='grades_user')


def tearDownModule():
    User.objects.all().delete()


class GradeViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        self.client.logout()

    def test_grade_view(self):
        # Given
        # URL redirection due to no login credentials
        status_code = 302
        # When
        response = self.client.get(reverse('grades:grading_systems'))
        # Then
        self.assertEqual(response.status_code, status_code)

        # Given
        # successful login and grading systems views
        self.client.login(username='grades_user', password='grades_user')
        status_code = 200
        # When
        response = self.client.get(reverse('grades:grading_systems'))
        # Then
        self.assertEqual(response.status_code, status_code)
        self.assertTemplateUsed(response, 'grading_systems.html')


class AddGradingSystemTest(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        self.client.logout()

    def test_add_grades_view(self):
        # Given
        status_code = 302
        # When
        response = self.client.get(reverse('grades:add_grade'))
        # Then
        self.assertEqual(response.status_code, status_code)

        # Given
        status_code = 200
        self.client.login(username='grades_user', password='grades_user')
        # When
        response = self.client.get(reverse('grades:add_grade'))
        # Then
        self.assertEqual(response.status_code, status_code)
        self.assertTemplateUsed(response, 'add_grades.html')

    def test_add_grades_post(self):
        # Given
        self.client.login(username='grades_user', password='grades_user')
        data = {'name': ['new_sys'], 'description': ['About grading system!'],
                'graderange_set-MIN_NUM_FORMS': ['0'],
                'graderange_set-TOTAL_FORMS': ['0'],
                'graderange_set-MAX_NUM_FORMS': ['1000'], 'add': ['Add'],
                'graderange_set-INITIAL_FORMS': ['0']}
        # When
        self.client.post(reverse('grades:add_grade'), data)
        # Then
        grading_systems = GradingSystem.objects.filter(name='new_sys')
        self.assertEqual(len(grading_systems), 1)

        # Given
        grading_system = grading_systems.first()
        # When
        ranges = grading_system.graderange_set.all()
        # Then
        self.assertEqual(len(ranges), 0)

        # Given
        data = {'graderange_set-0-upper_limit': ['40'],
                'graderange_set-0-description': ['Fail'],
                'graderange_set-0-lower_limit': ['0'],
                'graderange_set-0-system': [''], 'name': ['new_sys'],
                'graderange_set-MIN_NUM_FORMS': ['0'],
                'graderange_set-TOTAL_FORMS': ['1'],
                'graderange_set-MAX_NUM_FORMS': ['1000'],
                'graderange_set-0-id': [''],
                'description': ['About the grading system!'],
                'graderange_set-0-grade': ['F'],
                'graderange_set-INITIAL_FORMS': ['0'], 'save': ['Save']}
        # When
        self.client.post(reverse('grades:edit_grade',
                                 kwargs={'system_id': 2}), data)
        # Then
        ranges = grading_system.graderange_set.all()
        self.assertEqual(len(ranges), 1)
