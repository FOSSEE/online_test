# Python Imports
from __future__ import absolute_import, unicode_literals
from textwrap import dedent
import csv
import json

# Django and celery imports
from celery import shared_task
from django.urls import reverse
from django.shortcuts import get_object_or_404

# Local imports
from .models import (
    Course, QuestionPaper, Quiz, AnswerPaper, CourseStatus, User, Question,
    Answer
)
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


@shared_task
def update_user_marks(data):
    request_user = data.get("user_id")
    course_id = data.get("course_id")
    questionpaper_id = data.get("questionpaper_id")
    csv_data = data.get("csv_data")
    question_paper = QuestionPaper.objects.get(id=questionpaper_id)
    def _get_header_info(reader):
        question_ids = []
        fields = reader.fieldnames
        for field in fields:
            if field.startswith('Q') and field.count('-') > 0:
                qid = int(field.split('-')[1])
                if qid not in question_ids:
                    question_ids.append(qid)
        return question_ids
    try:
        reader = csv.DictReader(csv_data)
        question_ids = _get_header_info(reader)
        _read_marks_csv(
            reader, request_user, course_id, question_paper, question_ids
        )
    except TypeError:
        url = reverse(
            "yaksh:monitor", args=[question_paper.quiz_id, course_id]
        )
        message = dedent("""
            Unable to update quiz marks. Please re-upload correct CSV file
            Click <a href="{0}">here</a> to view
            """.format(url)
        )
        nm = NotificationMessage.objects.add_single_message(
            request_user, "{0} marks update status".format(
                question_paper.quiz.description
            ), message, "warning"
        )
        notification = Notification.objects.add_single_notification(
            request_user, nm.id
        )


def _read_marks_csv(
        reader, request_user, course_id, question_paper, question_ids):
    update_status = []
    for row in reader:
        username = row['user__username']
        user = User.objects.filter(username=username).first()
        if user:
            answerpapers = question_paper.answerpaper_set.filter(
                course_id=course_id, user_id=user.id)
        else:
            update_status.append(f'{username} user not found!')
            continue
        answerpaper = answerpapers.last()
        if not answerpaper:
            update_status.append(f'{username} has no answerpaper!')
            continue
        answers = answerpaper.answers.all()
        questions = answerpaper.questions.values_list('id', flat=True)
        for qid in question_ids:
            question = Question.objects.filter(id=qid).first()
            if not question:
                update_status.append(f'{qid} is an invalid question id!')
                continue
            if qid in questions:
                answer = answers.filter(question_id=qid).last()
                if not answer:
                    answer = Answer(question_id=qid, marks=0, correct=False,
                                    answer='', error=json.dumps([]))
                    answer.save()
                    answerpaper.answers.add(answer)
                key1 = 'Q-{0}-{1}-{2}-marks'.format(qid, question.summary,
                                                    question.points)
                key2 = 'Q-{0}-{1}-comments'.format(qid, question.summary)
                if key1 in reader.fieldnames:
                    try:
                        answer.set_marks(float(row[key1]))
                    except ValueError:
                        update_status.append(f'{row[key1]} invalid marks!')
                if key2 in reader.fieldnames:
                    answer.set_comment(row[key2])
                answer.save()
        answerpaper.update_marks(state='completed')
        answerpaper.save()
        update_status.append(
            'Updated successfully for user: {0}, question: {1}'.format(
            username, question.summary)
        )
    url = reverse(
        "yaksh:grade_user",
        args=[question_paper.quiz_id, course_id]
    )
    message = dedent("""
        Quiz mark update is complete.
        Click <a href="{0}">here</a> to view
        <br><br>{1}
        """.format(url, "\n".join(update_status))
    )
    summary = "{0} marks update status".format(
        question_paper.quiz.description
    )
    nm = NotificationMessage.objects.add_single_message(
        request_user, summary, message, "info"
    )
    notification = Notification.objects.add_single_notification(
        request_user, nm.id
    )
