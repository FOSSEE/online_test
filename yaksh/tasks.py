# Python Imports
from __future__ import absolute_import, unicode_literals
from textwrap import dedent

# Django and celery imports
from celery import shared_task
from django.urls import reverse
from django.shortcuts import get_object_or_404

# Local imports
from .models import Course, QuestionPaper, Quiz, AnswerPaper, CourseStatus
from notifications_plugin.models import NotificationMessage, Notification


@shared_task
def regrade_papers(data):
    question_id = data.get("question_id")
    questionpaper_id = data.get("questionpaper_id")
    answerpaper_id = data.get("answerpaper_id")
    course_id = data.get("course_id")
    user_id = data.get("user_id")
    quiz_id = data.get("quiz_id")
    quiz_name = data.get("quiz_name")
    course_name = data.get("course_name")

    url = reverse("yaksh:grade_user", args=[quiz_id, course_id])

    try:
        if answerpaper_id is not None and question_id is None:
            # Regrade specific user for all questions
            answerpaper = AnswerPaper.objects.get(id=answerpaper_id)
            url = reverse("yaksh:grade_user",
                          args=[quiz_id, answerpaper.user_id, course_id])
            for question in answerpaper.questions.all():
                answerpaper.regrade(question.id)
                course_status = CourseStatus.objects.filter(
                    user=answerpaper.user, course=answerpaper.course)
                if course_status.exists():
                    course_status.first().set_grade()

        elif answerpaper_id is not None and question_id is not None:
            # Regrade specific user for a specific question
            answerpaper = AnswerPaper.objects.get(pk=answerpaper_id)
            url = reverse("yaksh:grade_user",
                          args=[quiz_id, answerpaper.user_id, course_id])
            answerpaper.regrade(question_id)
            course_status = CourseStatus.objects.filter(
                user=answerpaper.user, course=answerpaper.course)
            if course_status.exists():
                course_status.first().set_grade()

        elif questionpaper_id is not None and question_id is not None:
            # Regrade all users for a specific question
            answerpapers = AnswerPaper.objects.filter(
                questions=question_id,
                question_paper_id=questionpaper_id, course_id=course_id)
            for answerpaper in answerpapers:
                answerpaper.regrade(question_id)
                course_status = CourseStatus.objects.filter(
                    user=answerpaper.user, course=answerpaper.course)
                if course_status.exists():
                    course_status.first().set_grade()

        message = dedent("""
            Quiz re-evaluation is complete.
            Click <a href="{0}">here</a> to view
            """.format(url)
            )
        notification_type = "success"
    except Exception as e:
        message = dedent("""
            Unable to regrade please try again.
            Click <a href="{0}">here</a> to view""".format(url)
            )
        notification_type = "warning"
    nm = NotificationMessage.objects.add_single_message(
        user_id, "{0} re-evaluation status".format(quiz_name),
        message, notification_type
    )
    notification = Notification.objects.add_single_notification(
        user_id, nm.id
    )
