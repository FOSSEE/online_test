import os

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseForbidden

from yaksh.decorators import email_verified, has_profile
from yaksh.models import Course
from certificates.models import Certificate, get_cert_template_dir
from certificates.forms import CertificateForm
from certificates.settings import CERTIFICATE_FILE_NAME

@login_required
@email_verified
def add_certificate(request, course_id=None):
    user = request.user
    if course_id:
        course = Course.objects.get(id=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404("You are not allowed to view this course")
    else:
        raise Http404('Need a course to create a certificate')

    certificate_template, created = Certificate.objects.get_or_create(course_id=course_id)

    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES, instance=certificate_template)
        if form.is_valid():
            form.save()
            return redirect('/exam/manage/courses')
        else:
            return render(
                request, 'yaksh/add_certificate.html', {'form': form}
            )
    else:
        form = CertificateForm(instance=certificate_template)
        if created:
            context = {'form': form}
        else:
            context = {'form': form, 'course_id': course_id}

        return render(
            request,
            'certificates/add_certificate.html',
            context
        )


@login_required
@has_profile
@email_verified
def preview_certificate(request, course_id):
    course = Course.objects.get(id=course_id)
    certificate = course.certificate
    filepath = get_cert_template_dir(certificate)
    template = os.path.join(filepath, CERTIFICATE_FILE_NAME)
    with open(template) as t:
        html = t.read()
    return HttpResponse(html)


@login_required
@has_profile
@email_verified
def download_certificate(request, course_id):
    user = request.user
    course = Course.objects.get(id=course_id)
    if not course.get_course_completion_status(user):
        return HttpResponseForbidden()
    certificate = course.certificate
    pdf = certificate.create_certificate_pdf(user)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="certificate.pdf"'
    return response