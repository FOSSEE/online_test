from textwrap import dedent
from collections import OrderedDict

from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string

from celery import task
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from notifications_plugin.models import NotificationMessage, Notification

from yaksh.models import Course, Quiz, QuestionPaper, AnswerPaper
from .models import Subscription


@periodic_task(
    run_every=(
        crontab(
            hour='08', minute=36, day_of_week='*/3', day_of_month='*',
            month_of_year='*'
        )
    ), name='course_deadline_task'
)
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


@periodic_task(
    run_every=(
        crontab(
            hour='09', minute=12, day_of_week='*/3', day_of_month='*',
            month_of_year='*'
        )
    ), name='quiz_deadline_task'
)
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


@periodic_task(
    run_every=(
        crontab(
            hour='23', minute=30, day_of_week='Tuesday', day_of_month='*',
            month_of_year='*'
        )
    ), name='course_quiz_deadline_mail_task'
)
def course_quiz_deadline_mail_task():
    courses = Course.objects.filter(active=True, is_trial=False)
    for course in courses:
        if course.is_active_enrollment():
            students = course.students.all()
            quizzes = course.get_quizzes()
            for student in students:
                subscribed = student.subscription.exists()
                if subscribed:
                    data = []
                    for quiz in quizzes:
                        quiz_data = {}
                        answer_paper = AnswerPaper.objects.filter(
                            course=course, user=student
                        )
                        if answer_paper.exists():
                            quiz_data['quiz'] = quiz
                            quiz_data['status'] = True
                        else:
                            quiz_data['quiz'] = quiz
                            quiz_data['status'] = False
                            quiz_data['deadline'] = quiz.end_date_time
                        data.append(quiz_data)
                    msg_html = render_to_string('notification/email.html', {
                            'data': data
                        }
                    )
                    msg_plain = render_to_string('notification/email.txt', {
                            'data': data
                        }
                    )
                    send_mail('email title', msg_plain, 'some@sender.com',
                        [student.email], html_message=msg_html
                    )
