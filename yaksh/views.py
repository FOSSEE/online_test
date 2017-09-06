import random
import string
import os
from datetime import datetime, timedelta
import collections
import csv
import uuid
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.template import RequestContext
from django.http import Http404
from django.db.models import Sum, Max, Q, F
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.forms.models import inlineformset_factory
from django.utils import timezone
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.conf import settings
import pytz
from taggit.models import Tag
from itertools import chain
import json
import six
from textwrap import dedent
import zipfile
try:
    from StringIO import StringIO as string_io
except ImportError:
    from io import BytesIO as string_io
import re
# Local imports.
from yaksh.models import (
    Answer, AnswerPaper, AssignmentUpload, Course, FileUpload, FloatTestCase,
    HookTestCase, IntegerTestCase, McqTestCase, Profile,
    QuestionPaper, QuestionSet, Quiz, Question, StandardTestCase,
    StdIOBasedTestCase, StringTestCase, TestCase, User,
    get_model_class
)
from yaksh.forms import (
    UserRegisterForm, UserLoginForm, QuizForm, QuestionForm,
    RandomQuestionForm, QuestionFilterForm, CourseForm, ProfileForm,
    UploadFileForm, get_object_form, FileForm, QuestionPaperForm
)
from .settings import URL_ROOT
from yaksh.models import AssignmentUpload
from .file_utils import extract_files
from .send_emails import send_user_mail, generate_activation_key, send_bulk_mail
from .decorators import email_verified, has_profile


def my_redirect(url):
    """An overridden redirect to deal with URL_ROOT-ing. See settings.py
    for details."""
    return redirect(URL_ROOT + url)


def my_render_to_response(template, context=None, **kwargs):
    """Overridden render_to_response.
    """
    if context is None:
        context = {'URL_ROOT': URL_ROOT}
    else:
        context['URL_ROOT'] = URL_ROOT
    return render_to_response(template, context, **kwargs)


def is_moderator(user):
    """Check if the user is having moderator rights"""
    if user.groups.filter(name='moderator').exists():
        return True


def add_to_group(users):
    """ add users to moderator group """
    group = Group.objects.get(name="moderator")
    for user in users:
        if not is_moderator(user):
            user.groups.add(group)


@email_verified
def index(request, next_url=None):
    """The start page.
    """
    user = request.user
    if user.is_authenticated():
        if is_moderator(user):
            return my_redirect('/exam/manage/' if not next_url else next_url)
        return my_redirect("/exam/quizzes/" if not next_url else next_url)

    return my_redirect("/exam/login/")


def user_register(request):
    """ Register a new user.
    Create a user and corresponding profile and store roll_number also."""

    user = request.user
    ci = RequestContext(request)
    if user.is_authenticated():
        return my_redirect("/exam/quizzes/")
    context = {}
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            u_name, pwd, user_email, key = form.save()
            new_user = authenticate(username=u_name, password=pwd)
            login(request, new_user)
            if user_email and key:
                success, msg = send_user_mail(user_email, key)
                context = {'activation_msg': msg}
                return my_render_to_response(
                    'yaksh/activation_status.html', context
                )
            return index(request)
        else:
            return my_render_to_response('yaksh/register.html', {'form': form},
                                         context_instance=ci)
    else:
        form = UserRegisterForm()
        return my_render_to_response(
            'yaksh/register.html', {'form': form}, context_instance=ci
        )


def user_logout(request):
    """Show a page to inform user that the quiz has been compeleted."""
    logout(request)
    context = {'message': "You have been logged out successfully"}
    return my_render_to_response('yaksh/complete.html', context)


@login_required
@has_profile
@email_verified
def quizlist_user(request, enrolled=None):
    """Show All Quizzes that is available to logged-in user."""
    user = request.user
    ci = RequestContext(request)

    if request.method == "POST":
        course_code = request.POST.get('course_code')
        hidden_courses = Course.objects.get_hidden_courses(code=course_code)
        courses = hidden_courses if hidden_courses else None
        title = 'Search'

    elif enrolled is not None:
        courses = user.students.all()
        title = 'Enrolled Courses'
    else:
        courses = Course.objects.filter(
            active=True, is_trial=False
        ).exclude(
           ~Q(requests=user), ~Q(rejected=user), hidden=True
        )
        title = 'All Courses'

    context = {'user': user, 'courses': courses, 'title': title}

    return my_render_to_response(
        "yaksh/quizzes_user.html", context, context_instance=ci
    )


@login_required
@email_verified
def results_user(request):
    """Show list of Results of Quizzes that is taken by logged-in user."""
    user = request.user
    papers = AnswerPaper.objects.get_user_answerpapers(user)
    context = {'papers': papers}
    return my_render_to_response("yaksh/results_user.html", context)


@login_required
@email_verified
def add_question(request, question_id=None):
    user = request.user
    ci = RequestContext(request)
    test_case_type = None

    if question_id is None:
        question = Question(user=user)
        question.save()
    else:
        question = Question.objects.get(id=question_id)

    if request.method == "POST" and 'delete_files' in request.POST:
        remove_files_id = request.POST.getlist('clear')
        if remove_files_id:
            files = FileUpload.objects.filter(id__in=remove_files_id)
            for file in files:
                file.remove()

    if request.method == 'POST':
        qform = QuestionForm(request.POST, instance=question)
        fileform = FileForm(request.POST, request.FILES)
        files = request.FILES.getlist('file_field')
        extract_files_id = request.POST.getlist('extract')
        hide_files_id = request.POST.getlist('hide')
        if files:
            for file in files:
                FileUpload.objects.get_or_create(question=question, file=file)
        if extract_files_id:
            files = FileUpload.objects.filter(id__in=extract_files_id)
            for file in files:
                file.set_extract_status()
        if hide_files_id:
            files = FileUpload.objects.filter(id__in=hide_files_id)
            for file in files:
                file.toggle_hide_status()
        formsets = []
        for testcase in TestCase.__subclasses__():
            formset = inlineformset_factory(Question, testcase, extra=0,
                                            fields='__all__')
            formsets.append(formset(
                request.POST, request.FILES, instance=question
                )
            )
        files = request.FILES.getlist('file_field')
        uploaded_files = FileUpload.objects.filter(question_id=question.id)
        if qform.is_valid():
            question = qform.save(commit=False)
            question.user = user
            question.save()
            # many-to-many field save function used to save the tags
            qform.save_m2m()
            for formset in formsets:
                if formset.is_valid():
                    formset.save()
            test_case_type = request.POST.get('case_type', None)
        else:
            context = {
                'qform': qform,
                'fileform': fileform,
                'question': question,
                'formsets': formsets,
                'uploaded_files': uploaded_files
            }
            return my_render_to_response(
                "yaksh/add_question.html", context, context_instance=ci
            )

    qform = QuestionForm(instance=question)
    fileform = FileForm()
    uploaded_files = FileUpload.objects.filter(question_id=question.id)
    formsets = []
    for testcase in TestCase.__subclasses__():
        if test_case_type == testcase.__name__.lower():
            formset = inlineformset_factory(Question, testcase, extra=1,
                                            fields='__all__')
        else:
            formset = inlineformset_factory(Question, testcase, extra=0,
                                            fields='__all__')
        formsets.append(formset(instance=question))
    context = {'qform': qform, 'fileform': fileform, 'question': question,
               'formsets': formsets, 'uploaded_files': uploaded_files}
    return my_render_to_response(
        "yaksh/add_question.html", context, context_instance=ci
    )


@login_required
@email_verified
def add_quiz(request, course_id, quiz_id=None):
    """To add a new quiz in the database.
    Create a new quiz and store it."""
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    ci = RequestContext(request)
    if not is_moderator(user) or (user != course.creator and user not in course.teachers.all()):
        raise Http404('You are not allowed to view this course !')
    context = {}
    if request.method == "POST":
        if quiz_id is None:
            form = QuizForm(request.POST, user=user, course=course_id)
            if form.is_valid():
                form.save()
                return my_redirect("/exam/manage/courses/")

        else:
            quiz = Quiz.objects.get(id=quiz_id)
            form = QuizForm(request.POST, user=user, course=course_id,
                instance=quiz
            )
            if form.is_valid():
                form.save()
                return my_redirect("/exam/manage/courses/")
    else:
        quiz = Quiz.objects.get(id=quiz_id) if quiz_id else None
        form = QuizForm(user=user,course=course_id, instance=quiz)
        context["quiz_id"] = quiz_id
    context["form"] = form
    return my_render_to_response(
        'yaksh/add_quiz.html', context, context_instance=ci
    )


@login_required
@has_profile
@email_verified
def prof_manage(request, msg=None):
    """Take credentials of the user with professor/moderator
    rights/permissions and log in."""
    user = request.user
    ci = RequestContext(request)
    new_room = False
    if user.is_authenticated() and is_moderator(user):
        question_papers = QuestionPaper.objects.filter(
            Q(quiz__course__creator=user) |
            Q(quiz__course__teachers=user),
            quiz__is_trial=False
        ).distinct()
        trial_paper = AnswerPaper.objects.filter(
            user=user, question_paper__quiz__is_trial=True
        )
        if request.method == "POST":
            delete_paper = request.POST.getlist('delete_paper')
            for answerpaper_id in delete_paper:
                answerpaper = AnswerPaper.objects.get(id=answerpaper_id)
                qpaper = answerpaper.question_paper
                if qpaper.quiz.course.is_trial:
                    qpaper.quiz.course.delete()
                else:
                    if qpaper.answerpaper_set.count() == 1:
                        qpaper.quiz.delete()
                    else:
                        answerpaper.delete()
        users_per_paper = []
        for paper in question_papers:
            answer_papers = AnswerPaper.objects.filter(question_paper=paper)
            users_passed = AnswerPaper.objects.filter(
                question_paper=paper, passed=True
            ).count()
            users_failed = AnswerPaper.objects.filter(
                question_paper=paper,
                passed=False
            ).count()
            temp = paper, answer_papers, users_passed, users_failed
            users_per_paper.append(temp)
        context = {'user': user, 'users_per_paper': users_per_paper,
                   'trial_paper': trial_paper, 'msg': msg
                   }
        return my_render_to_response(
            'yaksh/moderator_dashboard.html', context, context_instance=ci
        )
    return my_redirect('/exam/login/')


def user_login(request):
    """Take the credentials of the user and log the user in."""

    user = request.user
    ci = RequestContext(request)
    context = {}
    if user.is_authenticated():
        return index(request)

    next_url = request.GET.get('next')

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data
            login(request, user)
            return index(request, next_url)
        else:
            context = {"form": form}

    else:
        form = UserLoginForm()
        context = {"form": form}

    return my_render_to_response('yaksh/login.html', context,
                                 context_instance=ci)


@login_required
@email_verified
def start(request, questionpaper_id=None, attempt_num=None):
    """Check the user cedentials and if any quiz is available,
    start the exam."""
    user = request.user
    ci = RequestContext(request)
    # check conditions
    try:
        quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
    except QuestionPaper.DoesNotExist:
        msg = 'Quiz not found, please contact your '\
            'instructor/administrator.'
        return complete(request, msg, attempt_num, questionpaper_id=None)
    if not quest_paper.get_ordered_questions() and not \
            quest_paper.random_questions.all():
        msg = 'Quiz does not have Questions, please contact your '\
            'instructor/administrator.'
        return complete(request, msg, attempt_num, questionpaper_id=None)
    if not quest_paper.quiz.course.is_enrolled(user):
        raise Http404('You are not allowed to view this page!')
    # prerequisite check and passing criteria
    if quest_paper.quiz.is_expired() or not quest_paper.quiz.course.active:
        if is_moderator(user):
            return redirect("/exam/manage")
        return redirect("/exam/quizzes")
    if quest_paper.quiz.has_prerequisite() and not quest_paper.is_prerequisite_passed(user):
        if is_moderator(user):
            return redirect("/exam/manage")
        return redirect("/exam/quizzes")
    # if any previous attempt
    last_attempt = AnswerPaper.objects.get_user_last_attempt(
            questionpaper=quest_paper, user=user)
    if last_attempt and last_attempt.is_attempt_inprogress():
        return show_question(
            request, last_attempt.current_question(), last_attempt
        )
    # allowed to start
    if not quest_paper.can_attempt_now(user):
        if is_moderator(user):
            return redirect("/exam/manage")
        return redirect("/exam/quizzes")
    if not last_attempt:
        attempt_number = 1
    else:
        attempt_number = last_attempt.attempt_number + 1
    if attempt_num is None:
        context = {
            'user': user,
            'questionpaper': quest_paper,
            'attempt_num': attempt_number
        }
        if is_moderator(user):
            context["user"] = "moderator"
        return my_render_to_response('yaksh/intro.html', context,
                                     context_instance=ci)
    else:
        ip = request.META['REMOTE_ADDR']
        if not hasattr(user, 'profile'):
            msg = 'You do not have a profile and cannot take the quiz!'
            raise Http404(msg)
        new_paper = quest_paper.make_answerpaper(user, ip, attempt_number)
        if new_paper.status ==  'inprogress':
            return show_question(request, new_paper.current_question(),
                                 new_paper
                                 )
        else:
            msg = 'You have already finished the quiz!'
            raise Http404(msg)

@login_required
@email_verified
def show_question(request, question, paper, error_message=None, notification=None):
    """Show a question if possible."""
    user = request.user
    if not question:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(
            request, msg, paper.attempt_number, paper.question_paper.id
        )
    if not paper.question_paper.quiz.active:
        reason = 'The quiz has been deactivated!'
        return complete(
            request, reason, paper.attempt_number, paper.question_paper.id
        )
    if paper.time_left() <= 0:
        reason = 'Your time is up!'
        return complete(
            request, reason, paper.attempt_number, paper.question_paper.id
        )
    if question in paper.questions_answered.all():
        notification = (
            'You have already attempted this question successfully'
            if question.type == "code" else
            'You have already attempted this question'
        )
    test_cases = question.get_test_cases()
    files = FileUpload.objects.filter(question_id=question.id, hide=False)
    context = {
        'question': question,
        'paper': paper,
        'error_message': error_message,
        'test_cases': test_cases,
        'files': files,
        'notification': notification,
        'last_attempt': question.snippet.encode('unicode-escape')
    }
    answers = paper.get_previous_answers(question)
    if answers:
        last_attempt = answers[0].answer
        context['last_attempt'] = last_attempt.encode('unicode-escape')
    ci = RequestContext(request)
    return my_render_to_response('yaksh/question.html', context,
                                 context_instance=ci)


@login_required
@email_verified
def skip(request, q_id, next_q=None, attempt_num=None, questionpaper_id=None):
    user = request.user
    paper = get_object_or_404(
        AnswerPaper, user=request.user, attempt_number=attempt_num,
        question_paper=questionpaper_id
    )
    question = get_object_or_404(Question, pk=q_id)

    if request.method == 'POST' and question.type == 'code':
        user_code = request.POST.get('answer')
        new_answer = Answer(question=question, answer=user_code,
                            correct=False, skipped=True,
                            error=json.dumps([]))
        new_answer.save()
        paper.answers.add(new_answer)
    if next_q is not None:
        next_q = get_object_or_404(Question, pk=next_q)
    else:
        next_q = paper.next_question(q_id)
    return show_question(request, next_q, paper)


@login_required
@email_verified
def check(request, q_id, attempt_num=None, questionpaper_id=None):
    """Checks the answers of the user for particular question"""
    user = request.user
    paper = get_object_or_404(
        AnswerPaper,
        user=request.user,
        attempt_number=attempt_num,
        question_paper=questionpaper_id
    )
    current_question = get_object_or_404(Question, pk=q_id)

    if request.method == 'POST':
        snippet_code = request.POST.get('snippet')
        # Add the answer submitted, regardless of it being correct or not.
        if current_question.type == 'mcq':
            user_answer = request.POST.get('answer')
        elif current_question.type == 'integer':
            try:
                user_answer = int(request.POST.get('answer'))
            except ValueError:
                msg = "Please enter an Integer Value"
                return show_question(
                    request, current_question, paper, notification=msg
                )
        elif current_question.type == 'float':
            try:
                user_answer = float(request.POST.get('answer'))
            except ValueError:
                msg = "Please enter a Float Value"
                return show_question(request, current_question,
                                     paper, notification=msg)
        elif current_question.type == 'string':
            user_answer = str(request.POST.get('answer'))

        elif current_question.type == 'mcc':
            user_answer = request.POST.getlist('answer')
        elif current_question.type == 'upload':
            # if time-up at upload question then the form is submitted without
            # validation
            assignment_filename = request.FILES.getlist('assignment')
            if not assignment_filename:
                msg = "Please upload assignment file"
                return show_question(
                    request, current_question, paper, notification=msg
                )
            for fname in assignment_filename:
                assignment_files = AssignmentUpload.objects.filter(
                            assignmentQuestion=current_question,
                            assignmentFile__icontains=fname, user=user,
                            question_paper=questionpaper_id)
                if assignment_files.exists():
                    assign_file = assignment_files.get(
                            assignmentQuestion=current_question,
                            assignmentFile__icontains=fname, user=user,
                            question_paper=questionpaper_id)
                    os.remove(assign_file.assignmentFile.path)
                    assign_file.delete()
                AssignmentUpload.objects.create(
                    user=user, assignmentQuestion=current_question,
                    assignmentFile=fname, question_paper_id=questionpaper_id
                )
            user_answer = 'ASSIGNMENT UPLOADED'
            if not current_question.grade_assignment_upload:
                new_answer = Answer(
                    question=current_question, answer=user_answer,
                    correct=False, error=json.dumps([])
                )
                new_answer.save()
                paper.answers.add(new_answer)
                next_q = paper.add_completed_question(current_question.id)
                return show_question(request, next_q, paper)
        else:
            user_code = request.POST.get('answer')
            user_answer = snippet_code + "\n" + user_code if snippet_code else user_code
        if not user_answer:
            msg = ["Please submit a valid option or code"]
            return show_question(
                request, current_question, paper, notification=msg
            )
        new_answer = Answer(
            question=current_question, answer=user_answer,
            correct=False, error=json.dumps([])
        )
        new_answer.save()
        paper.answers.add(new_answer)
        # If we were not skipped, we were asked to check.  For any non-mcq
        # questions, we obtain the results via XML-RPC with the code executed
        # safely in a separate process (the code_server.py) running as nobody.
        json_data = current_question.consolidate_answer_data(user_answer, user) \
            if current_question.type == 'code' or \
            current_question.type == 'upload' else None
        result = paper.validate_answer(
            user_answer, current_question, json_data
        )
        if result.get('success'):
            new_answer.marks = (current_question.points * result['weight'] /
                current_question.get_maximum_test_case_weight()) \
                if current_question.partial_grading and \
                current_question.type == 'code' or current_question.type == 'upload' \
                else current_question.points
            new_answer.correct = result.get('success')
            error_message = None
            new_answer.error = json.dumps(result.get('error'))
            next_question = paper.add_completed_question(current_question.id)
        else:
            new_answer.marks = (current_question.points * result['weight'] /
                current_question.get_maximum_test_case_weight()) \
                if current_question.partial_grading and \
                current_question.type == 'code' or current_question.type == 'upload' \
                else 0
            error_message = result.get('error') if current_question.type == 'code' \
                or current_question.type == 'upload' else None
            new_answer.error = json.dumps(result.get('error'))
            next_question = current_question if current_question.type == 'code' \
                or current_question.type == 'upload' \
                else paper.add_completed_question(current_question.id)
        new_answer.save()
        paper.update_marks('inprogress')
        paper.set_end_time(timezone.now())
        return show_question(request, next_question, paper, error_message)
    else:
        return show_question(request, current_question, paper)

@login_required
@email_verified
def quit(request, reason=None, attempt_num=None, questionpaper_id=None):
    """Show the quit page when the user logs out."""
    paper = AnswerPaper.objects.get(user=request.user,
                                    attempt_number=attempt_num,
                                    question_paper=questionpaper_id)
    context = {'paper': paper, 'message': reason}
    return my_render_to_response('yaksh/quit.html', context,
                                 context_instance=RequestContext(request))


@login_required
@email_verified
def complete(request, reason=None, attempt_num=None, questionpaper_id=None):
    """Show a page to inform user that the quiz has been compeleted."""
    user = request.user
    if questionpaper_id is None:
        message = reason or "An Unexpected Error occurred. Please contact your '\
            'instructor/administrator.'"
        context = {'message': message}
        return my_render_to_response('yaksh/complete.html', context)
    else:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(
            user=user, question_paper=q_paper,
            attempt_number=attempt_num
        )
        paper.update_marks()
        paper.set_end_time(timezone.now())
        message = reason or "Quiz has been submitted"
        context = {'message': message, 'paper': paper}
        return my_render_to_response('yaksh/complete.html', context)


@login_required
@email_verified
def add_course(request, course_id=None):
    user = request.user
    ci = RequestContext(request)
    if course_id:
        course = Course.objects.get(id=course_id)
    else:
        course = None

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            new_course = form.save(commit=False)
            new_course.creator = user
            new_course.save()
            return my_redirect('/exam/manage/')
        else:
            return my_render_to_response(
                'yaksh/add_course.html', {'form': form}, context_instance=ci
            )
    else:
        form = CourseForm(instance=course)
        return my_render_to_response(
            'yaksh/add_course.html', {'form': form}, context_instance=ci
        )


@login_required
@email_verified
def enroll_request(request, course_id):
    user = request.user
    ci = RequestContext(request)
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_active_enrollment and course.hidden:
        msg = (
            'Unable to add enrollments for this course, please contact your '
            'instructor/administrator.'
        )
        return complete(request, msg, attempt_num=None, questionpaper_id=None)

    course.request(user)
    if is_moderator(user):
        return my_redirect('/exam/manage/courses')
    else:
        return my_redirect('/exam/quizzes/')


@login_required
@email_verified
def self_enroll(request, course_id):
    user = request.user
    ci = RequestContext(request)
    course = get_object_or_404(Course, pk=course_id)
    if course.is_self_enroll():
        was_rejected = False
        course.enroll(was_rejected, user)
    if is_moderator(user):
        return my_redirect('/exam/manage/')
    else:
        return my_redirect('/exam/quizzes/')


@login_required
@email_verified
def courses(request):
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    courses = Course.objects.filter(creator=user, is_trial=False)
    allotted_courses = Course.objects.filter(teachers=user, is_trial=False)
    context = {'courses': courses, "allotted_courses": allotted_courses}
    return my_render_to_response('yaksh/courses.html', context,
                                 context_instance=ci)


@login_required
@email_verified
def course_detail(request, course_id):
    user = request.user
    ci = RequestContext(request)

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    return my_render_to_response(
        'yaksh/course_detail.html', {'course': course}, context_instance=ci
    )


@login_required
@email_verified
def enroll(request, course_id, user_id=None, was_rejected=False):
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_active_enrollment:
        msg = (
            'Enrollment for this course has been closed,'
            ' please contact your '
            'instructor/administrator.'
        )
        return complete(request, msg, attempt_num=None, questionpaper_id=None)

    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    if request.method == 'POST':
        enroll_ids = request.POST.getlist('check')
    else:
        enroll_ids = [user_id]
    if not enroll_ids:
        return my_render_to_response(
            'yaksh/course_detail.html', {'course': course}, context_instance=ci
        )
    users = User.objects.filter(id__in=enroll_ids)
    course.enroll(was_rejected, *users)
    return course_detail(request, course_id)


@login_required
@email_verified
def send_mail(request, course_id, user_id=None):
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    message = None
    if request.method == 'POST':
        user_ids = request.POST.getlist('check')
        if request.POST.get('send_mail') == 'send_mail':
            users = User.objects.filter(id__in=user_ids)
            recipients = [student.email for student in users]
            email_body = request.POST.get('body')
            subject = request.POST.get('subject')
            attachments = request.FILES.getlist('email_attach')
            message = send_bulk_mail(
                subject, email_body, recipients, attachments
            )
    context = {
        'course': course, 'message': message,
        'state': 'mail'
    }
    return my_render_to_response(
        'yaksh/course_detail.html', context, context_instance=ci
    )


@login_required
@email_verified
def reject(request, course_id, user_id=None, was_enrolled=False):
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    if request.method == 'POST':
        reject_ids = request.POST.getlist('check')
    else:
        reject_ids = [user_id]
    if not reject_ids:
        message = "Please select atleast one User"
        return my_render_to_response(
            'yaksh/course_detail.html', {'course': course, 'message': message},
            context_instance=ci
        )
    users = User.objects.filter(id__in=reject_ids)
    course.reject(was_enrolled, *users)
    return course_detail(request, course_id)


@login_required
@email_verified
def toggle_course_status(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    if course.active:
        course.deactivate()
    else:
        course.activate()
    course.save()
    return course_detail(request, course_id)


@login_required
@email_verified
def show_statistics(request, questionpaper_id, attempt_number=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    attempt_numbers = AnswerPaper.objects.get_attempt_numbers(questionpaper_id)
    quiz = get_object_or_404(QuestionPaper, pk=questionpaper_id).quiz
    if attempt_number is None:
        context = {'quiz': quiz, 'attempts': attempt_numbers,
                   'questionpaper_id': questionpaper_id}
        return my_render_to_response('yaksh/statistics_question.html', context,
                                     context_instance=RequestContext(request))
    total_attempt = AnswerPaper.objects.get_count(questionpaper_id,
                                                  attempt_number)
    if not AnswerPaper.objects.has_attempt(questionpaper_id, attempt_number):
        return my_redirect('/exam/manage/')
    question_stats = AnswerPaper.objects.get_question_statistics(
        questionpaper_id, attempt_number
    )
    context = {'question_stats': question_stats, 'quiz': quiz,
               'questionpaper_id': questionpaper_id,
               'attempts': attempt_numbers, 'total': total_attempt}
    return my_render_to_response('yaksh/statistics_question.html', context,
                                 context_instance=RequestContext(request))


@login_required
@email_verified
def monitor(request, quiz_id=None):
    """Monitor the progress of the papers taken so far."""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if quiz_id is None:
        course_details = Course.objects.filter(
            Q(creator=user) | Q(teachers=user),
            is_trial=False
        ).distinct()
        context = {
            "papers": [], "course_details": course_details,
            "msg": "Monitor"
        }
        return my_render_to_response(
            'yaksh/monitor.html', context, context_instance=ci
        )
    # quiz_id is not None.
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id)
        if not quiz.course.is_creator(user) and not quiz.course.is_teacher(user):
            raise Http404('This course does not belong to you')
        q_paper = QuestionPaper.objects.filter(Q(quiz__course__creator=user) |
                                               Q(quiz__course__teachers=user),
                                               quiz__is_trial=False,
                                               quiz_id=quiz_id).distinct()
    except QuestionPaper.DoesNotExist:
        papers = []
        q_paper = None
        latest_attempts = []
    else:
        latest_attempts = []
        papers = AnswerPaper.objects.filter(question_paper=q_paper).order_by(
            'user__profile__roll_number'
        )
        users = papers.values_list('user').distinct()
        for auser in users:
            last_attempt = papers.filter(user__in=auser).aggregate(
                last_attempt_num=Max('attempt_number')
            )
            latest_attempts.append(
                papers.get(
                    user__in=auser,
                    attempt_number=last_attempt['last_attempt_num']
                )
            )
    context = {
        "papers": papers,
        "quiz": quiz,
        "msg": "Quiz Results",
        "latest_attempts": latest_attempts
    }
    return my_render_to_response('yaksh/monitor.html', context,
                                 context_instance=ci)


@csrf_exempt
def ajax_questions_filter(request):
    """Ajax call made when filtering displayed questions."""

    user = request.user
    filter_dict = {"user_id": user.id, "active": True}
    question_type = request.POST.get('question_type')
    marks = request.POST.get('marks')
    language = request.POST.get('language')

    if question_type != "select":
        filter_dict['type'] = str(question_type)

    if marks != "select":
        filter_dict['points'] = marks

    if language != "select":
        filter_dict['language'] = str(language)
    questions = list(Question.objects.filter(**filter_dict))

    return my_render_to_response(
        'yaksh/ajax_question_filter.html', {'questions': questions}
    )


def _get_questions(user, question_type, marks):
    if question_type is None and marks is None:
        return None
    if question_type:
        questions = Question.objects.filter(
            type=question_type,
            user=user,
            active=True
        )
        if marks:
            questions = questions.filter(points=marks)
    return questions


def _remove_already_present(questionpaper_id, questions):
    if questionpaper_id is None:
        return questions
    questionpaper = QuestionPaper.objects.get(pk=questionpaper_id)
    questions = questions.exclude(
            id__in=questionpaper.fixed_questions.values_list('id', flat=True))
    for random_set in questionpaper.random_questions.all():
        questions = questions.exclude(
                id__in=random_set.questions.values_list('id', flat=True))
    return questions


@login_required
@email_verified
def design_questionpaper(request, quiz_id, questionpaper_id=None):
    user = request.user

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    quiz = Quiz.objects.get(id=quiz_id)
    if not quiz.course.is_creator(user) and not quiz.course.is_teacher(user):
        raise Http404('This course does not belong to you')
    filter_form = QuestionFilterForm(user=user)
    questions = None
    marks = None
    state = None
    if questionpaper_id is None:
        question_paper = QuestionPaper.objects.get_or_create(quiz_id=quiz_id)[0]
    else:
        question_paper = get_object_or_404(QuestionPaper, id=questionpaper_id)
    qpaper_form = QuestionPaperForm(instance=question_paper)

    if request.method == 'POST':

        filter_form = QuestionFilterForm(request.POST, user=user)
        qpaper_form = QuestionPaperForm(request.POST, instance=question_paper)
        question_type = request.POST.get('question_type', None)
        marks = request.POST.get('marks', None)
        state = request.POST.get('is_active', None)

        if 'add-fixed' in request.POST:
            question_ids = request.POST.get('checked_ques', None)
            if question_paper.fixed_question_order:
                ques_order = question_paper.fixed_question_order.split(",") +\
                            question_ids.split(",")
                questions_order = ",".join(ques_order)
            else:
                questions_order = question_ids
            questions = Question.objects.filter(id__in=question_ids.split(','))
            question_paper.fixed_question_order = questions_order
            question_paper.save()
            question_paper.fixed_questions.add(*questions)

        if 'remove-fixed' in request.POST:
            question_ids = request.POST.getlist('added-questions', None)
            if question_paper.fixed_question_order:
                que_order = question_paper.fixed_question_order.split(",")
                for qid in question_ids:
                    que_order.remove(qid)
                if que_order:
                    question_paper.fixed_question_order = ",".join(que_order)
                else:
                    question_paper.fixed_question_order = ""
                question_paper.save()
            question_paper.fixed_questions.remove(*question_ids)

        if 'add-random' in request.POST:
            question_ids = request.POST.getlist('random_questions', None)
            num_of_questions = request.POST.get('num_of_questions', 1)
            if question_ids and marks:
                random_set = QuestionSet(marks=marks, num_questions=num_of_questions)
                random_set.save()
                for question in Question.objects.filter(id__in=question_ids):
                    random_set.questions.add(question)
                question_paper.random_questions.add(random_set)

        if 'remove-random' in request.POST:
            random_set_ids = request.POST.getlist('random_sets', None)
            question_paper.random_questions.remove(*random_set_ids)

        if 'save' in request.POST or 'back' in request.POST:
            qpaper_form.save()
            return my_redirect('/exam/manage/courses/')

        if marks:
            questions = _get_questions(user, question_type, marks)
            questions = _remove_already_present(questionpaper_id, questions)

        question_paper.update_total_marks()
        question_paper.save()
    random_sets = question_paper.random_questions.all()
    fixed_questions = question_paper.get_ordered_questions()
    context = {
        'qpaper_form': qpaper_form,
        'filter_form': filter_form,
        'qpaper': question_paper,
        'questions': questions,
        'fixed_questions': fixed_questions,
        'state': state,
        'random_sets': random_sets
    }
    return my_render_to_response(
        'yaksh/design_questionpaper.html',
        context,
        context_instance=RequestContext(request)
    )


@login_required
@email_verified
def show_all_questions(request):
    """Show a list of all the questions currently in the database."""

    user = request.user
    ci = RequestContext(request)
    context = {}
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    questions = Question.objects.filter(user_id=user.id, active=True)
    form = QuestionFilterForm(user=user)
    user_tags = questions.values_list('tags', flat=True).distinct()
    all_tags = Tag.objects.filter(id__in = user_tags)
    upload_form = UploadFileForm()
    context['questions'] = questions
    context['all_tags'] = all_tags
    context['papers'] = []
    context['question'] = None
    context['form'] = form
    context['upload_form'] = upload_form

    if request.method == 'POST':
        if request.POST.get('delete') == 'delete':
            data = request.POST.getlist('question')
            if data is not None:
                questions = Question.objects.filter(id__in=data, user_id=user.id,
                                                    active=True)
                for question in questions:
                    question.active = False
                    question.save()

        if request.POST.get('upload') == 'upload':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                questions_file = request.FILES['file']
                file_name = questions_file.name.split('.')
                if file_name[-1] == "zip":
                    ques = Question()
                    files, extract_path = extract_files(questions_file)
                    context['message'] = ques.read_yaml(extract_path, user,
                                                        files)
                else:
                    message = "Please Upload a ZIP file"
                    context['message'] = message

        if request.POST.get('download') == 'download':
            question_ids = request.POST.getlist('question')
            if question_ids:
                question = Question()
                zip_file = question.dump_questions(question_ids, user)
                response = HttpResponse(content_type='application/zip')
                response['Content-Disposition'] = dedent(
                    '''attachment; filename={0}_questions.zip'''.format(user)
                )
                zip_file.seek(0)
                response.write(zip_file.read())
                return response
            else:
                context['msg'] = "Please select atleast one question to download"

        if request.POST.get('test') == 'test':
            question_ids = request.POST.getlist("question")
            if question_ids:
                trial_paper = test_mode(user, False, question_ids, None)
                trial_paper.update_total_marks()
                trial_paper.save()
                return my_redirect("/exam/start/1/{0}".format(trial_paper.id))
            else:
                context["msg"] = "Please select atleast one question to test"

        if request.POST.get('question_tags'):
            question_tags = request.POST.getlist("question_tags")
            search_tags = []
            for tags in question_tags:
                search_tags.extend(re.split('[; |, |\*|\n]',tags))
            search_result = Question.objects.filter(tags__name__in=search_tags,
                                                    user=user).distinct()
            context['questions'] = search_result

    return my_render_to_response('yaksh/showquestions.html', context,
                                 context_instance=ci)


@login_required
@email_verified
def user_data(request, user_id, questionpaper_id=None):
    """Render user data."""
    current_user = request.user
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    user = User.objects.get(id=user_id)
    data = AnswerPaper.objects.get_user_data(user, questionpaper_id)

    context = {'data': data}
    return my_render_to_response('yaksh/user_data.html', context,
                                 context_instance=RequestContext(request))


@login_required
@email_verified
def download_csv(request, questionpaper_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    quiz = Quiz.objects.get(questionpaper=questionpaper_id)

    if not quiz.course.is_creator(user) and not quiz.course.is_teacher(user):
        raise Http404('The question paper does not belong to your course')
    papers = AnswerPaper.objects.get_latest_attempts(questionpaper_id)
    if not papers:
        return monitor(request, questionpaper_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{0}.csv"'.format(
                                      (quiz.description).replace('.', ''))
    writer = csv.writer(response)
    header = [
                'name',
                'username',
                'roll_number',
                'institute',
                'marks_obtained',
                'total_marks',
                'percentage',
                'questions',
                'questions_answered',
                'status'
    ]
    writer.writerow(header)
    for paper in papers:
        row = [
                '{0} {1}'.format(paper.user.first_name, paper.user.last_name),
                paper.user.username,
                paper.user.profile.roll_number,
                paper.user.profile.institute,
                paper.marks_obtained,
                paper.question_paper.total_marks,
                paper.percent,
                paper.questions.all(),
                paper.questions_answered.all(),
                paper.status
        ]
        writer.writerow(row)
    return response


@login_required
@email_verified
def grade_user(request, quiz_id=None, user_id=None, attempt_number=None):
    """Present an interface with which we can easily grade a user's papers
    and update all their marks and also give comments for each paper.
    """
    current_user = request.user
    ci = RequestContext(request)
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    course_details = Course.objects.filter(Q(creator=current_user) |
                                           Q(teachers=current_user),
                                           is_trial=False).distinct()
    context = {"course_details": course_details}
    if quiz_id is not None:
        questionpaper_id = QuestionPaper.objects.filter(
            quiz_id=quiz_id
        ).values("id")
        user_details = AnswerPaper.objects.get_users_for_questionpaper(
            questionpaper_id
        )
        quiz = get_object_or_404(Quiz, id=quiz_id)
        if not quiz.course.is_creator(current_user) and not \
                quiz.course.is_teacher(current_user):
            raise Http404('This course does not belong to you')

        has_quiz_assignments = AssignmentUpload.objects.filter(
                                question_paper_id=questionpaper_id
                                ).exists()
        context = {
            "users": user_details,
            "quiz_id": quiz_id,
            "quiz": quiz,
            "has_quiz_assignments": has_quiz_assignments
        }
        if user_id is not None:
            attempts = AnswerPaper.objects.get_user_all_attempts(
                questionpaper_id, user_id
            )
            try:
                if attempt_number is None:
                    attempt_number = attempts[0].attempt_number
            except IndexError:
                raise Http404('No attempts for paper')
            has_user_assignments = AssignmentUpload.objects.filter(
                                question_paper_id=questionpaper_id,
                                user_id=user_id
                                ).exists()
            user = User.objects.get(id=user_id)
            data = AnswerPaper.objects.get_user_data(
                user, questionpaper_id, attempt_number
            )
            context = {
                "data": data,
                "quiz_id": quiz_id,
                "users": user_details,
                "attempts": attempts,
                "user_id": user_id,
                "has_user_assignments": has_user_assignments,
                "has_quiz_assignments": has_quiz_assignments
            }
    if request.method == "POST":
        papers = data['papers']
        for paper in papers:
            for question, answers in six.iteritems(paper.get_question_answers()):
                marks = float(request.POST.get('q%d_marks' % question.id, 0))
                answer = answers[-1]['answer']
                answer.set_marks(marks)
                answer.save()
            paper.update_marks()
            paper.comments = request.POST.get(
                'comments_%d' % paper.question_paper.id, 'No comments')
            paper.save()

    return my_render_to_response(
        'yaksh/grade_user.html', context, context_instance=ci
    )


@login_required
@has_profile
@email_verified
def view_profile(request):
    """ view moderators and users profile """
    user = request.user
    ci = RequestContext(request)
    if is_moderator(user):
        template = 'manage.html'
    else:
        template = 'user.html'
    context = {'template': template, 'user': user}
    return my_render_to_response('yaksh/view_profile.html', context)


@login_required
@has_profile
@email_verified
def edit_profile(request):
    """ edit profile details facility for moderator and students """

    user = request.user
    ci = RequestContext(request)
    if is_moderator(user):
        template = 'manage.html'
    else:
        template = 'user.html'
    context = {'template': template}
    profile = Profile.objects.get(user_id=user.id)

    if request.method == 'POST':
        form = ProfileForm(request.POST, user=user, instance=profile)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.user = user
            form_data.user.first_name = request.POST['first_name']
            form_data.user.last_name = request.POST['last_name']
            form_data.user.save()
            form_data.save()
            return my_render_to_response(
                'yaksh/profile_updated.html', context_instance=ci
            )
        else:
            context['form'] = form
            return my_render_to_response(
                'yaksh/editprofile.html', context, context_instance=ci
            )
    else:
        form = ProfileForm(user=user, instance=profile)
        context['form'] = form
        return my_render_to_response(
            'yaksh/editprofile.html', context, context_instance=ci
        )


@login_required
@email_verified
def search_teacher(request, course_id):
    """ search teachers for the course """
    user = request.user
    ci = RequestContext(request)

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    context = {'success': False}
    course = get_object_or_404(Course, pk=course_id)
    context['course'] = course

    if user != course.creator and user not in course.teachers.all():
        raise Http404('You are not allowed to view this page!')

    if request.method == 'POST':
        u_name = request.POST.get('uname')
        if not len(u_name) == 0:
            teachers = User.objects.filter(
                Q(username__icontains=u_name) |
                Q(first_name__icontains=u_name) |
                Q(last_name__icontains=u_name) |
                Q(email__icontains=u_name)
            ).exclude(
                Q(id=user.id) |
                Q(is_superuser=1) |
                Q(id=course.creator.id)
            )
            context['success'] = True
            context['teachers'] = teachers
    return my_render_to_response(
        'yaksh/addteacher.html', context, context_instance=ci
    )


@login_required
@email_verified
def add_teacher(request, course_id):
    """ add teachers to the course """

    user = request.user
    ci = RequestContext(request)

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    context = {}
    course = get_object_or_404(Course, pk=course_id)
    if user == course.creator or user in course.teachers.all():
        context['course'] = course
    else:
        raise Http404('You are not allowed to view this page!')

    if request.method == 'POST':
        teacher_ids = request.POST.getlist('check')
        teachers = User.objects.filter(id__in=teacher_ids)
        add_to_group(teachers)
        course.add_teachers(*teachers)
        context['status'] = True
        context['teachers_added'] = teachers
    return my_render_to_response(
        'yaksh/addteacher.html', context, context_instance=ci
    )


@login_required
@email_verified
def remove_teachers(request, course_id):
    """ remove user from a course """

    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not is_moderator(user) and (user != course.creator and user
        not in course.teachers.all()):
        raise Http404('You are not allowed to view this page!')

    if request.method == "POST":
        teacher_ids = request.POST.getlist('remove')
        teachers = User.objects.filter(id__in=teacher_ids)
        course.remove_teachers(*teachers)
    return my_redirect('/exam/manage/courses')


def test_mode(user, godmode=False, questions_list=None, quiz_id=None):
    """creates a trial question paper for the moderators"""

    if questions_list is not None:
        trial_course = Course.objects.create_trial_course(user)
        trial_quiz = Quiz.objects.create_trial_quiz(trial_course, user)
        trial_questionpaper = QuestionPaper.objects.create_trial_paper_to_test_questions(
            trial_quiz, questions_list
        )
    else:
        trial_quiz = Quiz.objects.create_trial_from_quiz(
            quiz_id, user, godmode
        )
        trial_questionpaper = QuestionPaper.objects.create_trial_paper_to_test_quiz(
            trial_quiz, quiz_id
        )
    return trial_questionpaper


@login_required
@email_verified
def test_quiz(request, mode, quiz_id):
    """creates a trial quiz for the moderators"""
    godmode = True if mode == "godmode" else False
    current_user = request.user
    quiz = Quiz.objects.get(id=quiz_id)
    if (quiz.is_expired() or not quiz.active) and not godmode:
        return my_redirect('/exam/manage')

    trial_questionpaper = test_mode(current_user, godmode, None, quiz_id)
    return my_redirect("/exam/start/{0}".format(trial_questionpaper.id))


@login_required
@email_verified
def view_answerpaper(request, questionpaper_id):
    user = request.user
    quiz = get_object_or_404(QuestionPaper, pk=questionpaper_id).quiz
    if quiz.view_answerpaper and user in quiz.course.students.all():
        data = AnswerPaper.objects.get_user_data(user, questionpaper_id)
        has_user_assignment = AssignmentUpload.objects.filter(
            user=user,
            question_paper_id=questionpaper_id
        ).exists()
        context = {'data': data, 'quiz': quiz,
                   "has_user_assignment": has_user_assignment}
        return my_render_to_response('yaksh/view_answerpaper.html', context)
    else:
        return my_redirect('/exam/quizzes/')


@login_required
@email_verified
def create_demo_course(request):
    """ creates a demo course for user """
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise("You are not allowed to view this page")
    demo_course = Course()
    success = demo_course.create_demo(user)
    if success:
        msg = "Created Demo course successfully"
    else:
        msg = "Demo course already created"
    return prof_manage(request, msg)


@login_required
@email_verified
def grader(request, extra_context=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    courses = Course.objects.filter(is_trial=False)
    user_courses = list(courses.filter(creator=user)) + list(courses.filter(teachers=user))
    context = {'courses': user_courses}
    if extra_context:
        context.update(extra_context)
    return my_render_to_response('yaksh/regrade.html', context)


@login_required
@email_verified
def regrade(request, course_id, question_id=None, answerpaper_id=None, questionpaper_id=None):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not is_moderator(user) or (user != course.creator and user not in course.teachers.all()):
        raise Http404('You are not allowed to view this page!')
    details = []
    if answerpaper_id is not None and question_id is None:
        answerpaper = get_object_or_404(AnswerPaper, pk=answerpaper_id)
        for question in answerpaper.questions.all():
            details.append(answerpaper.regrade(question.id))
    if questionpaper_id is not None and question_id is not None:
        answerpapers = AnswerPaper.objects.filter(questions=question_id,
                question_paper_id=questionpaper_id)
        for answerpaper in answerpapers:
            details.append(answerpaper.regrade(question_id))
    if answerpaper_id is not None and question_id is not None:
        answerpaper = get_object_or_404(AnswerPaper, pk=answerpaper_id)
        details.append(answerpaper.regrade(question_id))
    return grader(request, extra_context={'details': details})


@login_required
@email_verified
def download_course_csv(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('The question paper does not belong to your course')
    students = course.get_only_students().annotate(
        roll_number=F('profile__roll_number'),
        institute=F('profile__institute')
    ).values(
        "id", "first_name", "last_name",
        "email", "institute", "roll_number"
    )
    quizzes = Quiz.objects.filter(course=course, is_trial=False)

    for student in students:
        total_course_marks = 0.0
        user_course_marks = 0.0
        for quiz in quizzes:
            quiz_best_marks = AnswerPaper.objects.get_user_best_of_attempts_marks\
                               (quiz, student["id"])
            user_course_marks += quiz_best_marks
            total_course_marks += quiz.questionpaper_set.values_list(
                "total_marks", flat=True)[0]
            student["{}".format(quiz.description)] = quiz_best_marks
        student["total_scored"] = user_course_marks
        student["out_of"] = total_course_marks
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{0}.csv"'.format(
                                      (course.name).lower().replace('.', ''))
    header = ['first_name', 'last_name', "roll_number", "email", "institute"]\
            + [quiz.description for quiz in quizzes] + ['total_scored', 'out_of']
    writer = csv.DictWriter(response, fieldnames=header, extrasaction='ignore')
    writer.writeheader()
    for student in students:
        writer.writerow(student)
    return response


def activate_user(request, key):
    ci = RequestContext(request)
    profile = get_object_or_404(Profile, activation_key=key)
    context = {}
    context['success'] = False
    if profile.is_email_verified:
        context['activation_msg'] = "Your account is already verified"
        return my_render_to_response(
            'yaksh/activation_status.html', context, context_instance=ci
        )

    if timezone.now() > profile.key_expiry_time:
        context['msg'] = dedent("""
                    Your activation time expired.
                    Please try again.
                    """)
    else:
        context['success'] = True
        profile.is_email_verified = True
        profile.save()
        context['msg'] = "Your account is activated"
    return my_render_to_response(
        'yaksh/activation_status.html', context, context_instance=ci
    )


def new_activation(request, email=None):
    ci = RequestContext(request)
    context = {}
    if request.method == "POST":
        email = request.POST.get('email')

    try:
        user = User.objects.get(email=email)
    except MultipleObjectsReturned:
        context['email_err_msg'] = "Multiple entries found for this email"\
                                    "Please change your email"
        return my_render_to_response(
            'yaksh/activation_status.html', context, context_instance=ci
        )
    except ObjectDoesNotExist:
        context['success'] = False
        context['msg'] = "Your account is not verified. \
                            Please verify your account"
        return render_to_response(
            'yaksh/activation_status.html', context, context_instance=ci
        )

    if not user.profile.is_email_verified:
        user.profile.activation_key = generate_activation_key(user.username)
        user.profile.key_expiry_time = timezone.now() + \
            timezone.timedelta(minutes=20)
        user.profile.save()
        new_user_data = User.objects.get(email=email)
        success, msg = send_user_mail(new_user_data.email,
                                      new_user_data.profile.activation_key
                                      )
        if success:
            context['activation_msg'] = msg
        else:
            context['msg'] = msg
    else:
        context['activation_msg'] = "Your account is already verified"

    return my_render_to_response(
        'yaksh/activation_status.html', context, context_instance=ci
    )


def update_email(request):
    context = {}
    ci = RequestContext(request)
    if request.method == "POST":
        email = request.POST.get('email')
        username = request.POST.get('username')
        user = get_object_or_404(User, username=username)
        user.email = email
        user.save()
        return new_activation(request, email)
    else:
        context['email_err_msg'] = "Please Update your email"
        return my_render_to_response(
            'yaksh/activation_status.html', context, context_instance=ci
        )


@login_required
@email_verified
def download_assignment_file(request, quiz_id, question_id=None, user_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page")
    qp = QuestionPaper.objects.get(quiz_id=quiz_id)
    assignment_files, file_name = AssignmentUpload.objects.get_assignments(
        qp, question_id, user_id
    )
    zipfile_name = string_io()
    zip_file = zipfile.ZipFile(zipfile_name, "w")
    for f_name in assignment_files:
        folder = f_name.user.get_full_name().replace(" ", "_")
        sub_folder = f_name.assignmentQuestion.summary.replace(" ", "_")
        folder_name = os.sep.join((folder, sub_folder, os.path.basename(
                        f_name.assignmentFile.name))
                        )
        zip_file.write(
            f_name.assignmentFile.path, folder_name
        )
    zip_file.close()
    zipfile_name.seek(0)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename={0}.zip'.format(
                                            file_name.replace(" ", "_")
                                            )
    response.write(zipfile_name.read())
    return response


@login_required
@email_verified
def duplicate_course(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if course.is_teacher(user) or course.is_creator(user):
        course.create_duplicate_course(user)
    else:
        msg = 'You do not have permissions to clone this course, please contact your '\
            'instructor/administrator.'
        return complete(request, msg, attempt_num=None, questionpaper_id=None)
    return my_redirect('/exam/manage/courses/')

@login_required
@email_verified
def download_yaml_template(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    template_path = os.path.join(os.path.dirname(__file__), "fixtures",
                                 "demo_questions.zip"
                                 )
    yaml_file = zipfile.ZipFile(template_path, 'r')
    template_yaml = yaml_file.open('questions_dump.yaml', 'r')
    response = HttpResponse(template_yaml, content_type='text/yaml')
    response['Content-Disposition'] = 'attachment;\
                                      filename="questions_dump.yaml"'

    return response


def chat_room(request, label, course_id):
    """
    Create a new chat room or get mesasges for already created chat room
    """
    user = request.user
    context = {}
    response_kwargs = {}
    context['success'] = False
    response_kwargs['content_type'] = 'application/json'
    course = Course.objects.get(id=course_id)
    result = [course.is_creator(user), course.is_teacher(user),
              course.is_student(user)]
    if not any(result):
        context['messages'] = [{"message": "You do not belong to this course"}]
        data = json.dumps(context)
        return HttpResponse(data, **response_kwargs)

    room, created = Room.objects.get_or_create(
        label=label, course_id=course_id
    )
    chat_msgs_dict = []
    messages = room.messages.order_by('-timestamp')
    if messages:
        messages = reversed(messages)
        tz = pytz.timezone(user.profile.timezone) if has_profile(user)\
            else pytz.timezone("UTC")
        for message in messages:
            msg_date = message.timestamp.astimezone(tz)
            chat_dict = {
                "sender": message.sender.id,
                "sender_name": message.sender.get_full_name().title(),
                "timestamp": datetime.strftime(msg_date, "%Y-%m-%d %H:%M:%S"),
                "message": message.message
            }
            chat_msgs_dict.append(chat_dict)
        context['success'] = True
    context['messages'] = chat_msgs_dict
    context['room_label'] = room.label
    data = json.dumps(context)
    return HttpResponse(data, **response_kwargs)


@login_required
@email_verified
def new_room(request, course_id):
    """
    Randomly create a new room, and redirect to it.
    """
    room = Room.objects.filter(course_id=course_id)
    if room.exists():
        room_label = room.get(course_id=course_id).label
    else:
        room_label = uuid.uuid4().__str__()
    return chat_room(request, room_label, course_id)


@login_required
@email_verified
def toggle_quiz_chat(request, quiz_id):
    """
    Enable/Disable chat per quiz
    """
    user = request.user
    quiz = Quiz.objects.get(id=quiz_id)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    if not quiz.course.is_creator(user) and not quiz.course.is_teacher(user):
        raise Http404('This course does not belong to you')
    quiz.toggle_chat_status()
    return my_redirect('/exam/manage/monitor/'+quiz_id)
