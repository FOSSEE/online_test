from textwrap import dedent

from django.utils import timezone

from celery import task
from notifications_plugin.models import NotificationMessage, Notification

from yaksh.models import Course, Quiz, QuestionPaper, AnswerPaper


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
            students = course.students.all()
            creator = course.creator
            if students:
                students_id = students.values_list('id', flat=True)
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
        students = course.students.all()
        students_id = students.values_list('id', flat=True)
        creator = course.creator
        modules = course.learning_module.all()
        for module in modules:
            units = module.learning_unit.all()
            for unit in units:
                if unit.type == 'quiz':
                    quiz = unit.quiz
                    if not quiz.is_expired():
                        message = dedent("""
                            The deadline for the quiz {0} is {1}, please
                            complete the quiz if not completed before the
                            deadline.
                            """.format(quiz, quiz.end_date_time)
                        )
                        notification_type = 'warning'
                        nm = NotificationMessage.objects.add_single_message(
                            creator_id=creator.id, summary='Quiz Notification',
                            description=message, msg_type=notification_type
                        )
                        Notification.objects.add_bulk_user_notifications(
                            receiver_ids=students_id, msg_id=nm.id
                        )