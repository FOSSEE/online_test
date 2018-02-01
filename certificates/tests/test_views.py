import pdfkit
import os
import shutil

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from yaksh.models import Course, CourseStatus, Profile
from certificates.models import Certificate, get_cert_template_dir

try:
    from unittest import mock
except ImportError:
    import mock


class TestDownloadCertificates(TestCase):
    def setUp(self):
        self.client = Client()

        # Create User with profile
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
            position='Creator',
            timezone='UTC'
        )

        # Create User with profile
        self.student_plaintext_pass = 'demo2'
        self.student = User.objects.create_user(
            username='demo_user2',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Student',
            timezone='UTC'
        )

        # Create a course
        self.course = Course.objects.create(
            name="Completed Course",
            enrollment="Enroll Request",
            creator=self.user
        )

        # Create a course status object
        self.course_status = CourseStatus.objects.create(
            course=self.course,
            user=self.student,
            percentage=100.0,
            grade='A'
        )

        # Create a certificate
        self.certificate = Certificate.objects.create(
            course=self.course,
            html='<body>Test HTML</body>',
            active=True
        )

    def tearDown(self):
        self.client.logout()
        self.certificate.delete()
        self.course_status.delete()
        self.course.delete()
        self.student.delete()
        self.user.delete()

    @mock.patch.object(Course, 'get_course_completion_status')
    @mock.patch.object(Certificate, 'create_certificate_html')
    @mock.patch.object(Certificate, 'create_certificate_pdf')
    def test_download_certificate_for_completed_course(
        self, mock_create_certificate_pdf, mock_create_certificate_html,
        mock_get_course_completion_status):
        """
        Test certificate downloading is successful
        for completed course
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        mock_get_course_completion_status.return_value = True
        mock_create_certificate_html.return_value = html = (
            '<html lang="en">\n    <head>\n'
            '    <body>\n        Hello World\n    </body>\n'
            '</html>'
        )
        pdf_file = pdfkit.from_string(html, output_path=False)
        mock_create_certificate_pdf = pdf_file

        response = self.client.get(
            reverse(
                'certificates:download_certificate',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch.object(Course, 'get_course_completion_status')
    def test_download_certificate_for_incomplete_course(
        self, mock_get_course_completion_status):
        """
        Test certificate downloading fails with 403 response
        for incomplete course
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        mock_get_course_completion_status.return_value = False
        response = self.client.get(
            reverse(
                'certificates:download_certificate',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 403)

class TestAddCertificates(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

        # Create User with profile
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
            position='Creator',
            timezone='UTC'
        )

        # Create User with profile
        self.student_plaintext_pass = 'demo2'
        self.student = User.objects.create_user(
            username='demo_user2',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo2@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Student',
            timezone='UTC'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        # Create a course
        self.course = Course.objects.create(
            name="Completed Course",
            enrollment="Enroll Request",
            creator=self.user
        )

        # Create a course status object
        self.course_status = CourseStatus.objects.create(
            course=self.course,
            user=self.student,
            percentage=100.0,
            grade='A'
        )

        # Create a certificate
        self.certificate = Certificate.objects.create(
            course=self.course,
            html='<body>Test HTML</body>',
            active=True
        )

    def tearDown(self):
        self.client.logout()
        self.certificate.delete()
        self.course_status.delete()
        self.course.delete()
        self.student.delete()
        self.user.delete()


    def test_add_certificate_denies_anonymous(self):
        """
        If not logged in redirect to login page
        """
        response = self.client.get(
            reverse(
                'certificates:add_certificate',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        redirect_destination = '/exam/login/?next=/certificate/add/1/'
        self.assertRedirects(response, redirect_destination)

    def test_add_certificate_denies_non_moderator(self):
        """
        If not moderator in redirect to login page
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        course_id = self.course.id
        response = self.client.get(
            reverse(
                'certificates:add_certificate',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_add_certificates_get(self):
        """
        GET request should return courses page
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        response = self.client.get(
            reverse(
                'certificates:add_certificate',
                kwargs={'course_id': self.course.id}
            ),
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'certificates/add_certificate.html')
        self.assertIsNotNone(response.context['form'])

    def test_add_certificate_post_new(self):
        """
        POST request to add certificate should add new certificate
        if no certificate exists
        """
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )

        response = self.client.post(
            reverse(
                'certificates:add_certificate',
                kwargs={'course_id': self.course.id}
            ),
            data={
                'html': 'test_html_body',
                'active': True,
            }
        )
        new_cert = Certificate.objects.get(course_id=self.course.id)
        self.assertEqual(new_cert.html, 'test_html_body')
        self.assertEqual(new_cert.active, True)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, '/exam/manage/courses', target_status_code=301
        )

        # Delete residual directory
        shutil.rmtree(
            os.path.join(get_cert_template_dir(self.certificate))
        )
