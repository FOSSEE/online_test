from textwrap import dedent
from collections import OrderedDict

from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from celery import task
from notifications_plugin.models import NotificationMessage, Notification

from yaksh.models import Course, Quiz, QuestionPaper, AnswerPaper
from .models import Subscription


@task(name='course_deadline_task')
def course_deadline_task():
    courses = Course.objects.filter(active=True, is_trial=False)
    for course in courses:
        if course.is_active_enrollment():
            message = dedent("""
                The deadline for the course {0} is {1}, please complete
                the course if not completed before the deadline.
                """.format(course.name, course.end_enroll_time)
            )
            creator = course.creator
            students_id = course.students.values_list('id', flat=True)
            if students_id:
                notification_type = "warning"
                nm = NotificationMessage.objects.add_single_message(
                    creator_id=creator.id, summary='Course Notification',
                    description=message, msg_type=notification_type
                )
                Notification.objects.add_bulk_user_notifications(
                    receiver_ids=students_id, msg_id=nm.id
                )


@task(name='quiz_deadline_task')
def quiz_deadline_task():
    courses = Course.objects.filter(active=True, is_trial=False)
    for course in courses:
        students_id = course.students.values_list('id', flat=True)
        creator = course.creator
        quizzes = course.get_quizzes()
        if students_id:
            for quiz in quizzes:
                if not quiz.is_expired():
                    message = dedent("""
                        The deadline for the quiz {0} of course {1} is
                        {2}, please complete the quiz if not completed
                        before the deadline.
                        """.format(
                            quiz.description, course.name, quiz.end_date_time
                        )
                    )
                    notification_type = 'warning'
                    nm = NotificationMessage.objects.add_single_message(
                        creator_id=creator.id, summary='Quiz Notification',
                        description=message, msg_type=notification_type
                    )
                    Notification.objects.add_bulk_user_notifications(
                        receiver_ids=students_id, msg_id=nm.id
                    )


@task(name='course_quiz_deadline_mail_task')
def course_quiz_deadline_mail_task():
    ct = ContentType.objects.get_for_model(Course)
    subs = Subscription.objects.filter(target_ct=ct, subscribe=True)
    if subs.exists():
        for sub in subs:
            course = sub.target
            if course.is_active_enrollment():
                user = sub.user
                data = course.get_quizzes_digest(user)
                subject = 'Quiz deadline notification for course {0}'.format(
                    course.name
                )
                msg_html = render_to_string('notification/email.html', {
                    'data': data
                })
                msg_plain = render_to_string('notification/email.txt', {
                    'data': data
                })
                send_mail(
                    subject, msg_plain,
                    settings.SENDER_EMAIL, [user.email],
                    html_message=msg_html
                )
