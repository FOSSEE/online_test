from __future__ import unicode_literals
import os
import re

from django.db import models
from django.conf import settings
from django.utils.text import get_valid_filename

from certificates.formatters.utils import HTMLFormatter, PDFFormatter, render_certificate_template
from certificates.settings import CERTIFICATE_STATIC_ROOT, CERTIFICATE_FILE_NAME
from yaksh.models import Course, CourseStatus

def get_valid_directory_name(s):
    s = str(s).lower().strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w]', '', s)

def get_cert_template_dir(instance):
    if CERTIFICATE_STATIC_ROOT:
        return os.path.join(
            CERTIFICATE_STATIC_ROOT,
            'course_{0}_{1}'.format(
                get_valid_directory_name(instance.course.name),
                instance.course.id
            )
        )
    else:
        return os.path.join(
            ('course_{0}_{1}'.format(
                get_valid_directory_name(instance.course.name),
                instance.course.id
            ))
        )


class Certificate(models.Model):
    course = models.OneToOneField(Course)
    html = models.TextField()
    active = models.BooleanField(default=True)
    static_files = models.FileField(upload_to=get_cert_template_dir, blank=True)

    def create_certificate_html(self, student):
        course_status = CourseStatus.objects.get(user=student, course=self.course)
        context = {'student': student, 'course': self.course, 'course_status': course_status}
        filepath = get_cert_template_dir(self)
        template = os.path.join(filepath, CERTIFICATE_FILE_NAME)
        return render_certificate_template(template, context)

    def create_certificate_pdf(self, student):
        html = self.create_certificate_html(student, self.course)
        template_path = get_cert_template_dir(self)
        pdf_formatter = PDFFormatter(template_path, html)
        return pdf_formatter.get_pdf()

