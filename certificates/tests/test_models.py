import os

from django.test import TestCase
from django.contrib.auth.models import User

from yaksh.models import Course, CourseStatus
from certificates.models import Certificate, get_cert_template_dir, get_valid_directory_name
from certificates import settings
from certificates.formatters.utils import PDFFormatter

try:
    from unittest import mock
except ImportError:
    import mock

class CertificateTestCases(TestCase):
    def setUp(self):
        # Create a user
        user = User.objects.create_user(
            username='demo_user',
            password='demo',
            email='demo@test.com'
        )

        # Create a student
        self.student = User.objects.create_user(
            username='student_demo_user',
            password='demo',
            email='student_demo4@test.com'
        )

        # Create a course
        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request",
            creator=user
        )

        # Create a course status object
        self.course_status = CourseStatus.objects.create(
            course=self.course,
            user=self.student
        )

        # Create a certificate
        self.certificate = Certificate.objects.create(
            course=self.course,
            html='<body>Test HTML</body>',
            active=True
        )

    def test_certificate(self):
        self.assertEqual(self.certificate.course, self.course)
        self.assertEqual(self.certificate.html, '<body>Test HTML</body>')
        self.assertEqual(self.certificate.active, True)

    def test_get_cert_template_dir(self):
        dir_name = 'course_{0}_{1}'.format(
            get_valid_directory_name(self.certificate.course.name),
            self.certificate.course.id
        )
        self.assertEqual(dir_name, get_cert_template_dir(self.certificate))

    @mock.patch('certificates.models.render_certificate_template')
    def test_create_certificate_html(self, mock_render_certificate_template):
        context = {
            'student': self.student,
            'course': self.course,
            'course_status': self.course_status,
        }
        template = os.path.join(
            get_cert_template_dir(self),
            settings.CERTIFICATE_FILE_NAME
        )

        self.certificate.create_certificate_html(self.student)
        mock_render_certificate_template.assert_called_with(template, context)

    @mock.patch.object(PDFFormatter, 'get_pdf')
    @mock.patch.object(Certificate, 'create_certificate_html')
    def test_create_certificate_pdf(self, mock_create_certificate_html, mock_get_pdf):
        # set up the certificate HTML mock
        mock_create_certificate_html.return_value = html = (
            '<html lang="en">\n    <head>\n'
            '    <body>\n        Hello World\n    </body>\n'
            '</html>'
        )
        template_path = get_cert_template_dir(self.certificate)
        pdf_formatter = PDFFormatter(template_path, html)

        self.certificate.create_certificate_pdf(self.student)
        # Check that it called the get_pdf method of some PDFFormatter
        self.assertTrue(mock_get_pdf.called)
        # Check that it called the get_pdf method of *our* PDFFormatter
        self.assertTrue(pdf_formatter.get_pdf.called)
