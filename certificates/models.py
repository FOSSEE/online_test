from __future__ import unicode_literals
import os
import re
from textwrap import dedent

from django.db import models
from django.conf import settings
from django.utils.text import get_valid_filename

from certificates.formatters.utils import HTMLFormatter, PDFFormatter, render_certificate_template
from certificates.settings import CERTIFICATE_STATIC_ROOT, CERTIFICATE_FILE_NAME
from yaksh.models import Course, CourseStatus

DEFAULT_HTML = dedent("""
    <!-- Sample Certificate Template -->

    <!-- Set the HTML to landscape mode-->
    <style type="text/css" media="print">
        @page { 
            size: landscape;
        }
        body { 
            writing-mode: tb-rl;
        }
    </style>
    <!-- Define the body for your certificate -->
    <body>
    <!-- You can ether define the CSS inline as shown here OR design your own CSS file and upload it separately in the Static Files field -->
        <div style="width:800px; height:600px; padding:20px; text-align:center; border: 10px solid #787878">
        <div style="width:750px; height:550px; padding:20px; text-align:center; border: 5px solid #787878">
               <span style="font-size:50px; font-weight:bold">Certificate of Completion</span>
               <br><br>
               <span style="font-size:25px"><i>This is to certify that</i></span>
               <br><br>
               <span style="font-size:30px"><b>{{ student.name }}</b></span><br/><br/>
               <span style="font-size:25px"><i>has completed the course</i></span> <br/><br/>
               <span style="font-size:30px">{{ course.name }}</span> <br/><br/>
               <span style="font-size:20px">with score of <b>{{ course_status.grade }}</b></span> <br/><br/><br/><br/>
        </div>
        </div>
    </body>
    """)

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
    html = models.TextField(default=DEFAULT_HTML)
    active = models.BooleanField(default=True)
    static_files = models.FileField(upload_to=get_cert_template_dir, blank=True)

    def create_certificate_html(self, student):
        course_status = CourseStatus.objects.get(user=student, course=self.course)
        context = {'student': student, 'course': self.course, 'course_status': course_status}
        filepath = get_cert_template_dir(self)
        template = os.path.join(filepath, CERTIFICATE_FILE_NAME)
        return render_certificate_template(template, context)

    def create_certificate_pdf(self, student):
        html = self.create_certificate_html(student)
        template_path = get_cert_template_dir(self)
        pdf_formatter = PDFFormatter(template_path, html)
        return pdf_formatter.get_pdf()

