from textwrap import dedent

from django.utils import timezone

from celery import task
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from notifications_plugin.models import NotificationMessage, Notification

from yaksh.models import Course, Quiz, QuestionPaper, AnswerPaper
from yaksh.send_emails import send_bulk_mail

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
                subject = 'Course Notification'
                send_bulk_mail(subject=subject, email_body=message,
                               recipients=students_id, attachments=None)


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
