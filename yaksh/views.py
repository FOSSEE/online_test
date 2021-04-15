import os
import csv
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Context, Template, loader
from django.http import Http404
from django.db.models import Max, Q, F
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.forms.models import inlineformset_factory
from django.forms import fields
from django.utils import timezone
from django.core.exceptions import (
    MultipleObjectsReturned, ObjectDoesNotExist
)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from taggit.models import Tag
from django.urls import reverse
from django.conf import settings
import json
from textwrap import dedent
import zipfile
import markdown
import ruamel
import pandas as pd
try:
    from StringIO import StringIO as string_io
except ImportError:
    from io import BytesIO as string_io
import re
# Local imports.
from online_test.celery_settings import app
from yaksh.code_server import get_result as get_result_from_code_server
from yaksh.models import (
    Answer, AnswerPaper, AssignmentUpload, Course, FileUpload, FloatTestCase,
    HookTestCase, IntegerTestCase, McqTestCase, Profile,
    QuestionPaper, QuestionSet, Quiz, Question, StandardTestCase,
    StdIOBasedTestCase, StringTestCase, TestCase, User,
    get_model_class, FIXTURES_DIR_PATH, MOD_GROUP_NAME, Lesson, LessonFile,
    LearningUnit, LearningModule, CourseStatus, question_types, Post, Comment,
    Topic, TableOfContents, LessonQuizAnswer, MicroManager, QRcode,
    QRcodeHandler, dict_to_yaml
)
from stats.models import TrackLesson
from yaksh.forms import (
    UserRegisterForm, UserLoginForm, QuizForm, QuestionForm,
    QuestionFilterForm, CourseForm, ProfileForm,
    UploadFileForm, FileForm, QuestionPaperForm, LessonForm,
    LessonFileForm, LearningModuleForm, ExerciseForm, TestcaseForm,
    SearchFilterForm, PostForm, CommentForm, TopicForm, VideoQuizForm
)
from yaksh.settings import SERVER_POOL_PORT, SERVER_HOST_NAME
from .settings import URL_ROOT
from .file_utils import extract_files, is_csv
from .send_emails import (send_user_mail,
                          generate_activation_key, send_bulk_mail)
from .decorators import email_verified, has_profile
from .tasks import regrade_papers, update_user_marks
from notifications_plugin.models import Notification
import hashlib


def my_redirect(url):
    """An overridden redirect to deal with URL_ROOT-ing. See settings.py
    for details."""
    return redirect(URL_ROOT + url)


def my_render_to_response(request, template, context=None, **kwargs):
    """Overridden render_to_response.
    """
    if context is None:
        context = {'URL_ROOT': URL_ROOT}
    else:
        context['URL_ROOT'] = URL_ROOT
    return render(request, template, context, **kwargs)


def is_moderator(user, group_name=MOD_GROUP_NAME):
    """Check if the user is having moderator rights"""
    try:
        group = Group.objects.get(name=group_name)
        return (
                user.profile.is_moderator and
                group.user_set.filter(id=user.id).exists()
            )
    except Profile.DoesNotExist:
        return False
    except Group.DoesNotExist:
        return False


def add_as_moderator(users, group_name=MOD_GROUP_NAME):
    """ add users to moderator group """
    try:
        Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        raise Http404('The Group {0} does not exist.'.format(group_name))
    for user in users:
        if not is_moderator(user):
            user.profile.is_moderator = True
            user.profile.save()


def get_html_text(md_text):
    """Takes markdown text and converts it to html"""
    return markdown.markdown(
        md_text, extensions=['tables', 'fenced_code']
    )


def formfield_callback(field):
    if (isinstance(field, models.TextField) and field.name == 'expected_input'):
        return fields.CharField(strip=False, required = False)
    if (isinstance(field, models.TextField) and field.name == 'expected_output'):
        return fields.CharField(strip=False)
    return field.formfield()


@email_verified
def index(request, next_url=None):
    """The start page.
    """
    user = request.user
    if user.is_authenticated:
        if is_moderator(user):
            return my_redirect('/exam/manage/' if not next_url else next_url)
        return my_redirect("/exam/quizzes/" if not next_url else next_url)

    return my_redirect("/exam/login/")


def user_register(request):
    """ Register a new user.
    Create a user and corresponding profile and store roll_number also."""

    user = request.user
    if user.is_authenticated:
        return my_redirect("/exam/quizzes/")
    context = {}
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            u_name, pwd, user_email, key = form.save()
            new_user = authenticate(username=u_name, password=pwd)
            login(request, new_user)
            if user_email and key:
                success, msg = send_user_mail(user_email, key)
                context = {'activation_msg': msg}
                return my_render_to_response(
                    request,
                    'yaksh/activation_status.html', context
                )
            return index(request)
        else:
            return my_render_to_response(
                request, 'yaksh/register.html', {'form': form}
            )
    else:
        form = UserRegisterForm()
        return my_render_to_response(
            request, 'yaksh/register.html', {'form': form}
        )


def user_logout(request):
    """Show a page to inform user that the quiz has been compeleted."""
    logout(request)
    context = {'message': "You have been logged out successfully"}
    return my_render_to_response(request, 'yaksh/complete.html', context)


@login_required
@has_profile
@email_verified
def quizlist_user(request, enrolled=None, msg=None):
    """Show All Quizzes that is available to logged-in user."""
    user = request.user
    courses_data = []

    if request.method == "POST":
        course_code = request.POST.get('course_code')
        hidden_courses = Course.objects.get_hidden_courses(code=course_code)
        courses = hidden_courses
        title = 'Search Results'
    else:
        enrolled_courses = user.students.filter(is_trial=False).order_by('-id')
        remaining_courses = list(Course.objects.filter(
            active=True, is_trial=False, hidden=False
        ).exclude(
            id__in=enrolled_courses.values_list("id", flat=True)
            ).order_by('-id'))
        courses = list(enrolled_courses)
        courses.extend(remaining_courses)
        title = 'All Courses'

    for course in courses:
        if course.students.filter(id=user.id).exists():
            _percent = course.get_completion_percent(user)
        else:
            _percent = None
        courses_data.append(
            {
                'data': course,
                'completion_percentage': _percent,
            }
        )

    messages.info(request, msg)
    context = {
        'user': user, 'courses': courses_data,
        'title': title
    }

    return my_render_to_response(request, "yaksh/quizzes_user.html", context)


@login_required
@email_verified
def results_user(request):
    """Show list of Results of Quizzes that is taken by logged-in user."""
    user = request.user
    papers = AnswerPaper.objects.get_user_answerpapers(user)
    context = {'papers': papers}
    return my_render_to_response(request, "yaksh/results_user.html", context)


@login_required
@email_verified
def add_question(request, question_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page !')

    test_case_type = None

    if question_id is not None:
        question = Question.objects.get(id=question_id)
        uploaded_files = FileUpload.objects.filter(question_id=question.id)
    else:
        question = None
        uploaded_files = []

    if request.method == 'POST':
        qform = QuestionForm(request.POST, instance=question)
        fileform = FileForm(request.POST, request.FILES)
        remove_files_id = request.POST.getlist('clear')
        added_files = request.FILES.getlist('file_field')
        extract_files_id = request.POST.getlist('extract')
        hide_files_id = request.POST.getlist('hide')
        if remove_files_id:
            files = FileUpload.objects.filter(id__in=remove_files_id).delete()
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
            formset = inlineformset_factory(
                                Question, testcase, extra=0,
                                fields='__all__',
                                form=TestcaseForm,
                                formfield_callback=formfield_callback
                                )
            formsets.append(formset(
                request.POST, request.FILES, instance=question
                )
            )
        if qform.is_valid():
            question = qform.save(commit=False)
            question.user = user
            question.save()
            # many-to-many field save function used to save the tags
            if added_files:
                for file in added_files:
                    FileUpload.objects.get_or_create(
                        question=question, file=file
                    )
            qform.save_m2m()
            for formset in formsets:
                if formset.is_valid():
                    formset.save()
            test_case_type = request.POST.get('case_type', None)
            uploaded_files = FileUpload.objects.filter(question_id=question.id)
            messages.success(request, "Question saved successfully")
        else:
            context = {
                'qform': qform,
                'fileform': fileform,
                'question': question,
                'formsets': formsets,
                'uploaded_files': uploaded_files
            }
            messages.warning(request, "Unable to save the question")
            return render(request, "yaksh/add_question.html", context)

    qform = QuestionForm(instance=question)
    fileform = FileForm()
    formsets = []
    for testcase in TestCase.__subclasses__():
        if test_case_type == testcase.__name__.lower():
            formset = inlineformset_factory(
                Question, testcase, extra=1, fields='__all__',
                form=TestcaseForm
            )
        else:
            formset = inlineformset_factory(
                Question, testcase, extra=0, fields='__all__',
                form=TestcaseForm
            )
        formsets.append(
            formset(
                instance=question,
                initial=[{'type': test_case_type}]
            )
        )
    context = {'qform': qform, 'fileform': fileform, 'question': question,
               'formsets': formsets, 'uploaded_files': uploaded_files}
    if question is not None:
        context["testcase_options"] = question.get_test_case_options()

    return render(request, "yaksh/add_question.html", context)


@login_required
@email_verified
def add_quiz(request, course_id=None, module_id=None, quiz_id=None):
    """To add a new quiz in the database.
    Create a new quiz and store it."""
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this course !')
    if quiz_id:
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if quiz.creator != user and not course_id:
            raise Http404('This quiz does not belong to you')
    else:
        quiz = None
    if module_id:
        module = get_object_or_404(LearningModule, id=module_id)
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This quiz does not belong to you')

    context = {}
    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            if quiz is None:
                last_unit = module.get_learning_units().last()
                order = last_unit.order + 1 if last_unit else 1
                form.instance.creator = user
            else:
                order = module.get_unit_order("quiz", quiz)
            added_quiz = form.save()
            unit, created = LearningUnit.objects.get_or_create(
                    type="quiz", quiz=added_quiz, order=order
                )
            if created:
                module.learning_unit.add(unit.id)
            messages.success(request, "Quiz saved successfully")
            return redirect(
                reverse("yaksh:edit_quiz",
                        args=[course_id, module_id, added_quiz.id])
            )
    else:
        form = QuizForm(instance=quiz)
    context["course_id"] = course_id
    context["quiz"] = quiz
    context["form"] = form
    return my_render_to_response(request, 'yaksh/add_quiz.html', context)


@login_required
@email_verified
def add_exercise(request, course_id=None, module_id=None, quiz_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this course !')
    if quiz_id:
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if quiz.creator != user and not course_id:
            raise Http404('This quiz does not belong to you')
    else:
        quiz = None
    if module_id:
        module = get_object_or_404(LearningModule, id=module_id)
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This Course does not belong to you')

    context = {}
    if request.method == "POST":
        form = ExerciseForm(request.POST, instance=quiz)
        if form.is_valid():
            if quiz is None:
                last_unit = module.get_learning_units().last()
                order = last_unit.order + 1 if last_unit else 1
                form.instance.creator = user
            else:
                order = module.get_unit_order("quiz", quiz)
            quiz = form.save(commit=False)
            quiz.is_exercise = True
            quiz.time_between_attempts = 0
            quiz.weightage = 0
            quiz.allow_skip = False
            quiz.attempts_allowed = -1
            quiz.duration = 1000
            quiz.pass_criteria = 0
            quiz.save()
            unit, created = LearningUnit.objects.get_or_create(
                    type="quiz", quiz=quiz, order=order
                )
            if created:
                module.learning_unit.add(unit.id)
            messages.success(
                request, "{0} saved successfully".format(quiz.description)
            )
            return redirect(
                reverse("yaksh:edit_exercise",
                        args=[course_id, module_id, quiz.id])
            )
    else:
        form = ExerciseForm(instance=quiz)
        context["exercise"] = quiz
    context["course_id"] = course_id
    context["form"] = form
    return my_render_to_response(request, 'yaksh/add_exercise.html', context)


@login_required
@has_profile
@email_verified
def prof_manage(request, msg=None):
    """Take credentials of the user with professor/moderator
    rights/permissions and log in."""
    user = request.user
    if not user.is_authenticated:
        return my_redirect('/exam/login')
    if not is_moderator(user):
        return my_redirect('/exam/')
    courses = Course.objects.get_queryset().filter(
        Q(creator=user) | Q(teachers=user),
        is_trial=False).distinct().order_by("-active")

    paginator = Paginator(courses, 20)
    page = request.GET.get('page')
    courses = paginator.get_page(page)
    messages.info(request, msg)
    context = {'user': user, 'objects': courses}
    return my_render_to_response(
        request, 'yaksh/moderator_dashboard.html', context
    )


def user_login(request):
    """Take the credentials of the user and log the user in."""

    user = request.user
    context = {}
    if user.is_authenticated:
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

    return my_render_to_response(request, 'yaksh/login.html', context)


@login_required
@email_verified
def special_start(request, micromanager_id=None):
    user = request.user
    micromanager = get_object_or_404(MicroManager, pk=micromanager_id,
                                     student=user)
    course = micromanager.course
    quiz = micromanager.quiz
    module = course.get_learning_module(quiz)
    quest_paper = get_object_or_404(QuestionPaper, quiz=quiz)

    if not course.is_enrolled(user):
        msg = 'You are not enrolled in {0} course'.format(course.name)
        return quizlist_user(request, msg=msg)

    if not micromanager.can_student_attempt():
        msg = 'Your special attempts are exhausted for {0}'.format(
            quiz.description)
        return quizlist_user(request, msg=msg)

    last_attempt = AnswerPaper.objects.get_user_last_attempt(
        quest_paper, user, course.id)

    if last_attempt:
        if last_attempt.is_attempt_inprogress():
            return show_question(
                request, last_attempt.current_question(), last_attempt,
                course_id=course.id, module_id=module.id,
                previous_question=last_attempt.current_question()
            )

    attempt_num = micromanager.get_attempt_number()
    ip = request.META['REMOTE_ADDR']
    new_paper = quest_paper.make_answerpaper(user, ip, attempt_num, course.id,
                                             special=True)
    micromanager.increment_attempts_utilised()
    return show_question(request, new_paper.current_question(), new_paper,
                         course_id=course.id, module_id=module.id)


@login_required
@email_verified
def start(request, questionpaper_id=None, attempt_num=None, course_id=None,
          module_id=None):
    """Check the user cedentials and if any quiz is available,
    start the exam."""
    user = request.user
    # check conditions
    try:
        quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
    except QuestionPaper.DoesNotExist:
        msg = 'Quiz not found, please contact your '\
            'instructor/administrator.'
        if is_moderator(user):
            return prof_manage(request, msg=msg)
        return view_module(request, module_id=module_id, course_id=course_id,
                           msg=msg)
    if not quest_paper.has_questions():
        msg = 'Quiz does not have Questions, please contact your '\
            'instructor/administrator.'
        if is_moderator(user):
            return prof_manage(request, msg=msg)
        return view_module(request, module_id=module_id, course_id=course_id,
                           msg=msg)
    course = Course.objects.get(id=course_id)
    learning_module = course.learning_module.get(id=module_id)
    learning_unit = learning_module.learning_unit.get(quiz=quest_paper.quiz.id)

    # unit module active status
    if not learning_module.active:
        return view_module(request, module_id, course_id)

    # unit module prerequiste check
    if learning_module.has_prerequisite():
        if not learning_module.is_prerequisite_complete(user, course):
            msg = "You have not completed the module previous to {0}".format(
                learning_module.name)
            return course_modules(request, course_id, msg)

    if learning_module.check_prerequisite_passes:
        if not learning_module.is_prerequisite_passed(user, course):
            msg = (
                "You have not successfully passed the module"
                " previous to {0}".format(learning_module.name)
            )
            return course_modules(request, course_id, msg)

    # is user enrolled in the course
    if not course.is_enrolled(user):
        msg = 'You are not enrolled in {0} course'.format(course.name)
        if is_moderator(user) and course.is_trial:
            return prof_manage(request, msg=msg)
        return quizlist_user(request, msg=msg)

    # if course is active and is not expired
    if not course.active or not course.is_active_enrollment():
        msg = "{0} is either expired or not active".format(course.name)
        if is_moderator(user) and course.is_trial:
            return prof_manage(request, msg=msg)
        return quizlist_user(request, msg=msg)

    # is quiz is active and is not expired
    if quest_paper.quiz.is_expired() or not quest_paper.quiz.active:
        msg = "{0} is either expired or not active".format(
            quest_paper.quiz.description)
        if is_moderator(user) and course.is_trial:
            return prof_manage(request, msg=msg)
        return view_module(request, module_id=module_id, course_id=course_id,
                           msg=msg)

    # prerequisite check and passing criteria for quiz
    if learning_unit.has_prerequisite():
        if not learning_unit.is_prerequisite_complete(
                user, learning_module, course):
            msg = "You have not completed the previous Lesson/Quiz/Exercise"
            if is_moderator(user) and course.is_trial:
                return prof_manage(request, msg=msg)
            return view_module(request, module_id=module_id,
                               course_id=course_id, msg=msg)

    # update course status with current unit
    _update_unit_status(course_id, user, learning_unit)

    # if any previous attempt
    last_attempt = AnswerPaper.objects.get_user_last_attempt(
        quest_paper, user, course_id)

    if last_attempt:
        if last_attempt.is_attempt_inprogress():
            return show_question(
                request, last_attempt.current_question(), last_attempt,
                course_id=course_id, module_id=module_id,
                previous_question=last_attempt.current_question()
            )
        attempt_number = last_attempt.attempt_number + 1
    else:
        attempt_number = 1

    # allowed to start
    if not quest_paper.can_attempt_now(user, course_id)[0]:
        msg = quest_paper.can_attempt_now(user, course_id)[1]
        if is_moderator(user):
            return prof_manage(request, msg=msg)
        return complete(
            request, msg, last_attempt.attempt_number, quest_paper.id,
            course_id=course_id, module_id=module_id
        )

    if attempt_num is None and not quest_paper.quiz.is_exercise:
        context = {
            'user': user,
            'questionpaper': quest_paper,
            'attempt_num': attempt_number,
            'course': course,
            'module': learning_module,
        }
        if is_moderator(user):
            context["status"] = "moderator"
        return my_render_to_response(request, 'yaksh/intro.html', context)
    else:
        ip = request.META['REMOTE_ADDR']
        if not hasattr(user, 'profile'):
            msg = 'You do not have a profile and cannot take the quiz!'
            raise Http404(msg)
        new_paper = quest_paper.make_answerpaper(user, ip, attempt_number,
                                                 course_id)
        if new_paper.status == 'inprogress':
            return show_question(
                request, new_paper.current_question(),
                new_paper, course_id=course_id,
                module_id=module_id, previous_question=None
            )
        else:
            msg = 'You have already finished the quiz!'
            raise Http404(msg)


@login_required
@email_verified
def show_question(request, question, paper, error_message=None,
                  notification=None, course_id=None, module_id=None,
                  previous_question=None):
    """Show a question if possible."""
    quiz = paper.question_paper.quiz
    quiz_type = 'Exam'
    can_skip = False
    assignment_files = []
    qrcode = []
    if previous_question:
        delay_time = paper.time_left_on_question(previous_question)
    else:
        delay_time = paper.time_left_on_question(question)

    if previous_question and quiz.is_exercise:
        is_prev_que_answered = paper.questions_answered.filter(
            id=previous_question.id).exists()
        if (delay_time <= 0 or is_prev_que_answered):
            can_skip = True
        question = previous_question
    if not question:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(
            request, msg, paper.attempt_number, paper.question_paper.id,
            course_id=course_id, module_id=module_id
        )
    if not quiz.active and not paper.is_special:
        reason = 'The quiz has been deactivated!'
        return complete(
            request, reason, paper.attempt_number, paper.question_paper.id,
            course_id=course_id, module_id=module_id
        )
    if not quiz.is_exercise:
        if paper.time_left() <= 0:
            reason = 'Your time is up!'
            return complete(
                request, reason, paper.attempt_number, paper.question_paper.id,
                course_id, module_id=module_id
            )
    else:
        quiz_type = 'Exercise'
    if paper.questions_answered.filter(id=question.id).exists():
        notification = (
            'You have already attempted this question successfully'
            if question.type == "code" else
            'You have already attempted this question'
        )
    if question.type in ['mcc', 'mcq', 'arrange']:
        test_cases = question.get_ordered_test_cases(paper)
    else:
        test_cases = question.get_test_cases()
    if question.type == 'upload':
        assignment_files = AssignmentUpload.objects.filter(
                            assignmentQuestion_id=question.id,
                            answer_paper=paper
                        )
        handlers = QRcodeHandler.objects.filter(user=request.user,
                                                question=question,
                                                answerpaper=paper)
        qrcode = None
        if handlers.exists():
            handler = handlers.last()
            qrcode = handler.qrcode_set.filter(active=True, used=False).last()
    files = FileUpload.objects.filter(question_id=question.id, hide=False)
    course = Course.objects.get(id=course_id)
    module = course.learning_module.get(id=module_id)
    all_modules = course.get_learning_modules()
    context = {
        'question': question,
        'paper': paper,
        'quiz': quiz,
        'error_message': error_message,
        'test_cases': test_cases,
        'files': files,
        'notification': notification,
        'last_attempt': question.snippet.encode('unicode-escape'),
        'course': course,
        'module': module,
        'can_skip': can_skip,
        'delay_time': delay_time,
        'quiz_type': quiz_type,
        'all_modules': all_modules,
        'assignment_files': assignment_files,
        'qrcode': qrcode,
    }
    answers = paper.get_previous_answers(question)
    if answers:
        last_attempt = answers[0].answer
        if last_attempt:
            context['last_attempt'] = last_attempt.encode('unicode-escape')
    return my_render_to_response(request, 'yaksh/question.html', context)


@login_required
@email_verified
def skip(request, q_id, next_q=None, attempt_num=None, questionpaper_id=None,
         course_id=None, module_id=None):
    paper = get_object_or_404(
        AnswerPaper, user=request.user, attempt_number=attempt_num,
        question_paper=questionpaper_id, course_id=course_id
    )
    question = get_object_or_404(Question, pk=q_id)

    if paper.question_paper.quiz.is_exercise:
        paper.start_time = timezone.now()
        paper.save()

    if request.method == 'POST' and question.type == 'code':
        if not paper.answers.filter(question=question, correct=True).exists():
            user_code = request.POST.get('answer')
            new_answer = Answer(
                question=question, answer=user_code,
                correct=False, skipped=True,
                error=json.dumps([])
            )
            new_answer.save()
            paper.answers.add(new_answer)
    if next_q is not None:
        next_q = get_object_or_404(Question, pk=next_q)
    else:
        next_q = paper.next_question(q_id)
    return show_question(request, next_q, paper, course_id=course_id,
                         module_id=module_id)


@login_required
@email_verified
def check(request, q_id, attempt_num=None, questionpaper_id=None,
          course_id=None, module_id=None):
    """Checks the answers of the user for particular question"""
    user = request.user
    paper = get_object_or_404(
        AnswerPaper,
        user=request.user,
        attempt_number=attempt_num,
        question_paper=questionpaper_id,
        course_id=course_id
    )
    current_question = get_object_or_404(Question, pk=q_id)
    def is_valid_answer(answer):
        status = True
        if ((current_question.type == "mcc" or
                current_question.type == "arrange") and not answer):
            status = False
        elif answer is None or not str(answer):
            status = False
        return status

    if request.method == 'POST':
        # Add the answer submitted, regardless of it being correct or not.
        if (paper.time_left() <= -10 or paper.status == "completed"):
            reason = 'Your time is up!'
            return complete(
                request, reason, paper.attempt_number, paper.question_paper.id,
                course_id, module_id=module_id
            )
        if current_question.type == 'mcq':
            user_answer = request.POST.get('answer')
        elif current_question.type == 'integer':
            try:
                user_answer = int(request.POST.get('answer'))
            except ValueError:
                msg = "Please enter an Integer Value"
                return show_question(
                    request, current_question, paper, notification=msg,
                    course_id=course_id, module_id=module_id,
                    previous_question=current_question
                )
        elif current_question.type == 'float':
            try:
                user_answer = float(request.POST.get('answer'))
            except ValueError:
                msg = "Please enter a Float Value"
                return show_question(request, current_question,
                                     paper, notification=msg,
                                     course_id=course_id, module_id=module_id,
                                     previous_question=current_question)
        elif current_question.type == 'string':
            user_answer = str(request.POST.get('answer'))

        elif current_question.type == 'mcc':
            user_answer = request.POST.getlist('answer')
        elif current_question.type == 'arrange':
            user_answer_ids = request.POST.get('answer').split(',')
            user_answer = [int(ids) for ids in user_answer_ids]
        elif current_question.type == 'upload':
            # if time-up at upload question then the form is submitted without
            # validation
            assign_files = []
            assignments = request.FILES
            for i in range(len(assignments)):
                assign_files.append(assignments[f"assignment[{i}]"])
            if not assign_files:
                msg = "Please upload assignment file"
                return show_question(
                    request, current_question, paper, notification=msg,
                    course_id=course_id, module_id=module_id,
                    previous_question=current_question
                )
            uploaded_files = []
            AssignmentUpload.objects.filter(
                assignmentQuestion_id=current_question.id,
                answer_paper_id=paper.id
                ).delete()
            for fname in assign_files:
                fname._name = fname._name.replace(" ", "_")
                uploaded_files.append(AssignmentUpload(
                                    assignmentQuestion_id=current_question.id,
                                    assignmentFile=fname,
                                    answer_paper_id=paper.id
                                ))
            AssignmentUpload.objects.bulk_create(uploaded_files)
            user_answer = 'ASSIGNMENT UPLOADED'
            new_answer = Answer(
                question=current_question, answer=user_answer,
                correct=False, error=json.dumps([])
            )
            new_answer.save()
            paper.answers.add(new_answer)
            next_q = paper.add_completed_question(current_question.id)
            return show_question(request, next_q, paper,
                                 course_id=course_id, module_id=module_id,
                                 previous_question=current_question)
        else:
            user_answer = request.POST.get('answer')
        if not is_valid_answer(user_answer):
            msg = "Please submit a valid answer."
            return show_question(
                request, current_question, paper, notification=msg,
                course_id=course_id, module_id=module_id,
                previous_question=current_question
            )
        if current_question in paper.get_questions_answered()\
                and current_question.type not in ['code', 'upload']:
            new_answer = paper.get_latest_answer(current_question.id)
            new_answer.answer = user_answer
            new_answer.correct = False
        else:
            new_answer = Answer(
                question=current_question, answer=user_answer,
                correct=False, error=json.dumps([])
            )
        new_answer.save()
        uid = new_answer.id
        paper.answers.add(new_answer)
        # If we were not skipped, we were asked to check.  For any non-mcq
        # questions, we obtain the results via XML-RPC with the code executed
        # safely in a separate process (the code_server.py) running as nobody.
        json_data = current_question.consolidate_answer_data(
            user_answer, user) if current_question.type == 'code' else None
        result = paper.validate_answer(
            user_answer, current_question, json_data, uid
        )
        if current_question.type == 'code':
            if (paper.time_left() <= 0 and not
                    paper.question_paper.quiz.is_exercise):
                url = '{0}:{1}'.format(SERVER_HOST_NAME, SERVER_POOL_PORT)
                result_details = get_result_from_code_server(url, uid,
                                                             block=True)
                result = json.loads(result_details.get('result'))
                next_question, error_message, paper = _update_paper(
                    request, uid, result)
                return show_question(request, next_question, paper,
                                     error_message, course_id=course_id,
                                     module_id=module_id,
                                     previous_question=current_question)
            else:
                return JsonResponse(result)
        else:
            next_question, error_message, paper = _update_paper(
                request, uid, result)
            return show_question(request, next_question, paper, error_message,
                                 course_id=course_id, module_id=module_id,
                                 previous_question=current_question)
    else:
        return show_question(request, current_question, paper,
                             course_id=course_id, module_id=module_id,
                             previous_question=current_question)


@csrf_exempt
def get_result(request, uid, course_id, module_id):
    result = {}
    url = '{0}:{1}'.format(SERVER_HOST_NAME, SERVER_POOL_PORT)
    result_state = get_result_from_code_server(url, uid)
    result['status'] = result_state.get('status')
    if result['status'] == 'done':
        result = json.loads(result_state.get('result'))
        template_path = os.path.join(*[os.path.dirname(__file__),
                                       'templates', 'yaksh',
                                       'error_template.html'
                                       ]
                                     )
        next_question, error_message, paper = _update_paper(request, uid,
                                                            result
                                                            )
        answer = Answer.objects.get(id=uid)
        current_question = answer.question
        if result.get('success'):
            return show_question(request, next_question, paper, error_message,
                                 course_id=course_id, module_id=module_id,
                                 previous_question=current_question)
        else:
            with open(template_path) as f:
                template_data = f.read()
                template = Template(template_data)
                context = Context({"error_message": result.get('error')})
                render_error = template.render(context)
                result["error"] = render_error
    return JsonResponse(result)


def _update_paper(request, uid, result):
    new_answer = Answer.objects.get(id=uid)
    current_question = new_answer.question
    paper = new_answer.answerpaper_set.first()

    if result.get('success'):
        new_answer.marks = (current_question.points * result['weight'] /
                            current_question.get_maximum_test_case_weight()) \
            if current_question.partial_grading and \
            current_question.type == 'code' or \
            current_question.type == 'upload' else current_question.points
        new_answer.correct = result.get('success')
        error_message = None
        new_answer.error = json.dumps(result.get('error'))
        next_question = paper.add_completed_question(current_question.id)
    else:
        new_answer.marks = (current_question.points * result['weight'] /
                            current_question.get_maximum_test_case_weight()) \
            if current_question.partial_grading and \
            current_question.type == 'code' or \
            current_question.type == 'upload' \
            else 0
        error_message = result.get('error') \
            if current_question.type == 'code' or \
            current_question.type == 'upload' \
            else None
        new_answer.error = json.dumps(result.get('error'))
        next_question = current_question if current_question.type == 'code' \
            or current_question.type == 'upload' \
            else paper.add_completed_question(current_question.id)
    new_answer.save()
    paper.update_marks('inprogress')
    paper.set_end_time(timezone.now())
    return next_question, error_message, paper


@login_required
@email_verified
def quit(request, reason=None, attempt_num=None, questionpaper_id=None,
         course_id=None, module_id=None):
    """Show the quit page when the user logs out."""
    paper = AnswerPaper.objects.get(user=request.user,
                                    attempt_number=attempt_num,
                                    question_paper=questionpaper_id,
                                    course_id=course_id)
    context = {'paper': paper, 'message': reason, 'course_id': course_id,
               'module_id': module_id}
    return my_render_to_response(request, 'yaksh/quit.html', context)


@login_required
@email_verified
def complete(request, reason=None, attempt_num=None, questionpaper_id=None,
             course_id=None, module_id=None):
    """Show a page to inform user that the quiz has been completed."""
    user = request.user
    if questionpaper_id is None:
        message = reason or ("An Unexpected Error occurred. Please "
                             "contact your instructor/administrator."
                             )
        context = {'message': message}
        return my_render_to_response(request, 'yaksh/complete.html', context)
    else:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(
            user=user, question_paper=q_paper,
            attempt_number=attempt_num,
            course_id=course_id
        )
        course = Course.objects.get(id=course_id)
        learning_module = course.learning_module.get(id=module_id)
        learning_unit = learning_module.learning_unit.get(quiz=q_paper.quiz)

        paper.update_marks()
        paper.set_end_time(timezone.now())
        message = reason or "Quiz has been submitted"
        context = {'message': message, 'paper': paper,
                   'module_id': learning_module.id,
                   'course_id': course_id, 'learning_unit': learning_unit}
        if is_moderator(user):
            context['user'] = "moderator"
        return my_render_to_response(request, 'yaksh/complete.html', context)


@login_required
@email_verified
def add_course(request, course_id=None):
    user = request.user
    if course_id:
        course = Course.objects.get(id=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404("You are not allowed to view this course")
    else:
        course = None
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    if request.method == 'POST':
        form = CourseForm(user, request.POST, instance=course)
        if form.is_valid():
            new_course = form.save(commit=False)
            if course_id is None:
                new_course.creator = user
            new_course.save()
            messages.success(
                request, "Saved {0} successfully".format(new_course.name)
                )
            return my_redirect('/exam/manage/courses')
        else:
            return my_render_to_response(
                request, 'yaksh/add_course.html', {'form': form}
            )
    else:
        form = CourseForm(user, instance=course)
        return my_render_to_response(
            request, 'yaksh/add_course.html', {'form': form}
        )


@login_required
@email_verified
def enroll_request(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_active_enrollment() and course.hidden:
        msg = (
            'Unable to add enrollments for this course, please contact your '
            'instructor/administrator.'
        )
        messages.warning(request, msg)
    else:
        course.request(user)
        messages.success(
            request,
            "Enrollment request sent for {0} by {1}".format(
                course.name, course.creator.get_full_name()
            )
        )
    if is_moderator(user):
        return my_redirect('/exam/manage/courses')
    else:
        return my_redirect('/exam/quizzes/')


@login_required
@email_verified
def self_enroll(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if course.is_self_enroll():
        was_rejected = False
        course.enroll(was_rejected, user)
    messages.success(
        request,
        "Enrolled in {0} by {1}".format(
            course.name, course.creator.get_full_name()
        )
    )
    if is_moderator(user):
        return my_redirect('/exam/manage/')
    else:
        return my_redirect('/exam/quizzes/')


@login_required
@email_verified
def courses(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    courses = Course.objects.filter(
        Q(creator=user) | Q(teachers=user),
        is_trial=False).order_by('-active').distinct()

    tags = request.GET.get('search_tags')
    status = request.GET.get('search_status')

    form = SearchFilterForm(tags=tags, status=status)

    if status == 'select' and tags:
        courses = courses.filter(
            name__icontains=tags)
    elif status == 'active':
        courses = courses.filter(
            name__icontains=tags, active=True)
    elif status == 'closed':
        courses = courses.filter(
            name__icontains=tags, active=False)

    paginator = Paginator(courses, 30)
    page = request.GET.get('page')
    courses = paginator.get_page(page)
    courses_found = courses.object_list.count()
    context = {'objects': courses, 'created': True,
               'form': form, 'courses_found': courses_found}
    return my_render_to_response(request, 'yaksh/courses.html', context)


@login_required
@email_verified
def course_detail(request, course_id):
    user = request.user

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    return my_render_to_response(
        request, 'yaksh/course_detail.html', {'course': course}
    )


@login_required
@email_verified
def enroll_user(request, course_id, user_id=None, was_rejected=False):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, id=course_id)
    if not course.is_active_enrollment():
        msg = (
            'Enrollment for this course has been closed,'
            ' please contact your '
            'instructor/administrator.'
        )
        messages.warning(request, msg)
        return redirect('yaksh:course_students', course_id=course_id)

    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    user = User.objects.get(id=user_id)
    course.enroll(was_rejected, user)
    messages.success(request, 'Enrolled student successfully')
    return redirect('yaksh:course_students', course_id=course_id)


@login_required
@email_verified
def reject_user(request, course_id, user_id=None, was_enrolled=False):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    course = get_object_or_404(Course, id=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    user = User.objects.get(id=user_id)
    course.reject(was_enrolled, user)
    messages.success(request, "Rejected students successfully")
    return redirect('yaksh:course_students', course_id=course_id)


@login_required
@email_verified
def enroll_reject_user(request,
                       course_id, was_enrolled=False, was_rejected=False):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    course = get_object_or_404(Course, id=course_id)

    if not course.is_active_enrollment():
        msg = (
            'Enrollment for this course has been closed,'
            ' please contact your '
            'instructor/administrator.'
        )
        messages.warning(request, msg)
        return redirect('yaksh:course_students', course_id=course_id)

    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    if request.method == 'POST':
        if 'enroll' in request.POST:
            enroll_ids = request.POST.getlist('check')
            if not enroll_ids:
                messages.warning(request, "Please select atleast one student")
                return redirect('yaksh:course_students', course_id=course_id)
            users = User.objects.filter(id__in=enroll_ids)
            course.enroll(was_rejected, *users)
            messages.success(request, "Enrolled student(s) successfully")
            return redirect('yaksh:course_students', course_id=course_id)
        if 'reject' in request.POST:
            reject_ids = request.POST.getlist('check')
            if not reject_ids:
                messages.warning(request, "Please select atleast one student")
                return redirect('yaksh:course_students', course_id=course_id)
            users = User.objects.filter(id__in=reject_ids)
            course.reject(was_enrolled, *users)
            messages.success(request, "Rejected students successfully")
            return redirect('yaksh:course_students', course_id=course_id)
    return redirect('yaksh:course_students', course_id=course_id)


@login_required
@email_verified
def send_mail(request, course_id, user_id=None):
    user = request.user
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
            messages.info(request, message)
    context = {
        'course': course, 'message': message,
        'enrolled': course.get_enrolled(), 'is_mail': True
    }
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


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
        message = '{0} deactivated successfully'.format(course.name)
    else:
        course.activate()
        message = '{0} activated successfully'.format(course.name)
    course.save()
    messages.info(request, message)
    return my_redirect("/exam/manage/courses")


@login_required
@email_verified
def show_statistics(request, questionpaper_id, attempt_number=None,
                    course_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    attempt_numbers = AnswerPaper.objects.get_attempt_numbers(
        questionpaper_id, course_id)
    quiz = get_object_or_404(QuestionPaper, pk=questionpaper_id).quiz
    context = {'quiz': quiz, 'attempts': attempt_numbers,
               'questionpaper_id': questionpaper_id,
               'course_id': course_id}
    if attempt_number is None:
        return my_render_to_response(
            request, 'yaksh/statistics_question.html', context
        )
    total_attempt = AnswerPaper.objects.get_count(questionpaper_id,
                                                  attempt_number,
                                                  course_id)
    if not AnswerPaper.objects.has_attempt(questionpaper_id, attempt_number,
                                           course_id):
        messages.warning(request, "No answerpapers found")
        return my_render_to_response(
            request, 'yaksh/statistics_question.html', context
        )
    question_stats = AnswerPaper.objects.get_question_statistics(
        questionpaper_id, attempt_number, course_id
    )
    context = {'question_stats': question_stats, 'quiz': quiz,
               'questionpaper_id': questionpaper_id,
               'attempts': attempt_numbers, 'total': total_attempt,
               'course_id': course_id}
    return my_render_to_response(
        request, 'yaksh/statistics_question.html', context
    )


@login_required
@email_verified
def monitor(request, quiz_id=None, course_id=None, attempt_number=1):
    """Monitor the progress of the papers taken so far."""

    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    course = get_object_or_404(Course, id=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    quiz = get_object_or_404(Quiz, id=quiz_id)
    q_paper = QuestionPaper.objects.filter(quiz__is_trial=False,
                                           quiz_id=quiz_id).distinct().last()
    attempt_numbers = AnswerPaper.objects.get_attempt_numbers(
        q_paper.id, course.id
    )
    questions_count = 0
    questions_attempted = {}
    completed_papers = 0
    inprogress_papers = 0
    papers = AnswerPaper.objects.filter(
        question_paper_id=q_paper.id, attempt_number=attempt_number,
        course_id=course_id
        ).order_by('user__first_name')
    papers = papers.filter(attempt_number=attempt_number)
    if not papers.exists():
        messages.warning(request, "No AnswerPapers found")
    else:
        questions_count = q_paper.get_questions_count()
        questions_attempted = AnswerPaper.objects.get_questions_attempted(
            papers.values_list("id", flat=True)
        )
        completed_papers = papers.filter(status="completed").count()
        inprogress_papers = papers.filter(status="inprogress").count()
    context = {
        "papers": papers, "quiz": quiz,
        "inprogress_papers": inprogress_papers,
        "attempt_numbers": attempt_numbers,
        "course": course, "total_papers": papers.count(),
        "completed_papers": completed_papers,
        "questions_attempted": questions_attempted,
        "questions_count": questions_count
    }
    return my_render_to_response(request, 'yaksh/monitor.html', context)


def _get_questions(user, question_type, marks):
    questions = None
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


def _get_questions_from_tags(question_tags, user, active=True, questions=None):
    search_tags = []
    search = None
    for tags in question_tags:
        search_tags.extend(re.split('[; |, |\*|\n]', tags))
    if questions:
        search = questions.filter(tags__name__in=search_tags)
    else:
        search = Question.objects.get_queryset().filter(
            tags__name__in=search_tags, user=user, active=active).distinct()
    return search


@login_required
@email_verified
def design_questionpaper(request, course_id, quiz_id, questionpaper_id=None):
    user = request.user
    que_tags = Question.objects.filter(
        active=True, user=user).values_list('tags', flat=True).distinct()
    all_tags = Tag.objects.filter(id__in=que_tags)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    if quiz_id:
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if quiz.creator != user and not course_id:
            raise Http404('This quiz does not belong to you')
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This Course does not belong to you')

    filter_form = QuestionFilterForm(user=user)
    questions = None
    marks = None
    state = None
    if questionpaper_id is None:
        question_paper = QuestionPaper.objects.get_or_create(
            quiz_id=quiz_id)[0]
    else:
        question_paper = get_object_or_404(QuestionPaper, id=questionpaper_id,
                                           quiz_id=quiz_id)
    qpaper_form = QuestionPaperForm(instance=question_paper)

    if request.method == 'POST':
        filter_form = QuestionFilterForm(request.POST, user=user)
        qpaper_form = QuestionPaperForm(request.POST, instance=question_paper)
        question_type = request.POST.get('question_type', None)
        marks = request.POST.get('marks', None)
        state = request.POST.get('is_active', None)
        tags = request.POST.get('question_tags', None)
        if 'add-fixed' in request.POST:
            question_ids = request.POST.get('checked_ques', None)
            if question_ids:
                if question_paper.fixed_question_order:
                    ques_order = (
                        question_paper.fixed_question_order.split(",") +
                        question_ids.split(",")
                    )
                    questions_order = ",".join(ques_order)
                else:
                    questions_order = question_ids
                questions = Question.objects.filter(
                    id__in=question_ids.split(',')
                )
                question_paper.fixed_question_order = questions_order
                question_paper.save()
                question_paper.fixed_questions.add(*questions)
                messages.success(request, "Questions added successfully")
                return redirect(
                    'yaksh:designquestionpaper',
                    course_id=course_id,
                    quiz_id=quiz_id,
                    questionpaper_id=questionpaper_id
                )

            else:
                messages.warning(request, "Please select atleast one question")

        if 'remove-fixed' in request.POST:
            question_ids = request.POST.getlist('added-questions', None)
            if question_ids:
                if question_paper.fixed_question_order:
                    que_order = question_paper.fixed_question_order.split(",")
                    for qid in question_ids:
                        que_order.remove(qid)
                    if que_order:
                        question_paper.fixed_question_order = ",".join(
                            que_order)
                    else:
                        question_paper.fixed_question_order = ""
                    question_paper.save()
                question_paper.fixed_questions.remove(*question_ids)
                messages.success(request, "Questions removed successfully")
                return redirect(
                    'yaksh:designquestionpaper',
                    course_id=course_id,
                    quiz_id=quiz_id,
                    questionpaper_id=questionpaper_id
                )
            else:
                messages.warning(request, "Please select atleast one question")

        if 'add-random' in request.POST:
            question_ids = request.POST.getlist('random_questions', None)
            num_of_questions = request.POST.get('num_of_questions', 1)
            if question_ids and marks:
                random_set = QuestionSet(marks=marks,
                                         num_questions=num_of_questions)
                random_set.save()
                random_ques = Question.objects.filter(id__in=question_ids)
                random_set.questions.add(*random_ques)
                question_paper.random_questions.add(random_set)
                messages.success(request, "Questions removed successfully")
                return redirect(
                    'yaksh:designquestionpaper',
                    course_id=course_id,
                    quiz_id=quiz_id,
                    questionpaper_id=questionpaper_id
                )
            else:
                messages.warning(request, "Please select atleast one question")

        if 'remove-random' in request.POST:
            random_set_ids = request.POST.getlist('random_sets', None)
            if random_set_ids:
                question_paper.random_questions.remove(*random_set_ids)
                messages.success(request, "Questions removed successfully")
                return redirect(
                    'yaksh:designquestionpaper',
                    course_id=course_id,
                    quiz_id=quiz_id,
                    questionpaper_id=questionpaper_id
                )
            else:
                messages.warning(request, "Please select question set")

        if 'save' in request.POST or 'back' in request.POST:
            qpaper_form.save()
            messages.success(request, "Question Paper saved successfully")

        if marks:
            questions = _get_questions(user, question_type, marks)
        elif tags:
            que_tags = request.POST.getlist('question_tags', None)
            questions = _get_questions_from_tags(que_tags, user)

        if questions:
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
        'random_sets': random_sets,
        'course_id': course_id,
        'all_tags': all_tags
    }
    return my_render_to_response(
        request, 'yaksh/design_questionpaper.html', context
    )


@login_required
@email_verified
def show_all_questions(request):
    """Show a list of all the questions currently in the database."""

    user = request.user
    context = {}
    message = None
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    if request.method == 'POST':
        if request.POST.get('delete') == 'delete':
            data = request.POST.getlist('question')
            if data is not None:
                questions = Question.objects.filter(
                    id__in=data, user_id=user.id, active=True)
                for question in questions:
                    question.active = False
                    question.save()
            message = "Questions deleted successfully"

        if request.POST.get('upload') == 'upload':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                questions_file = request.FILES['file']
                file_extension = questions_file.name.split('.')[-1]
                ques = Question()
                if file_extension == "zip":
                    files, extract_path = extract_files(questions_file)
                    message = ques.read_yaml(extract_path, user, files)
                elif file_extension in ["yaml", "yml"]:
                    questions = questions_file.read()
                    message = ques.load_questions(questions, user)
                else:
                    message = "Please Upload a ZIP file or YAML file"

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
                message = "Please select atleast one question to download"

        if request.POST.get('test') == 'test':
            question_ids = request.POST.getlist("question")
            if question_ids:
                trial_paper, trial_course, trial_module = test_mode(
                    user, False, question_ids, None)
                trial_paper.update_total_marks()
                trial_paper.save()
                return my_redirect(
                    reverse("yaksh:start_quiz",
                            args=[1, trial_module.id, trial_paper.id,
                                  trial_course.id]
                        )
                    )
            else:
                message = "Please select atleast one question to test"

    questions = Question.objects.get_queryset().filter(
                user_id=user.id, active=True).order_by('-id')
    form = QuestionFilterForm(user=user)
    user_tags = questions.values_list('tags', flat=True).distinct()
    all_tags = Tag.objects.filter(id__in=user_tags)
    upload_form = UploadFileForm()
    paginator = Paginator(questions, 30)
    page = request.GET.get('page')
    questions = paginator.get_page(page)
    context['objects'] = questions
    context['all_tags'] = all_tags
    context['form'] = form
    context['upload_form'] = upload_form

    messages.info(request, message)
    return my_render_to_response(request, 'yaksh/showquestions.html', context)


@login_required
@email_verified
def questions_filter(request):
    """Filter questions by type, language or marks."""

    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    questions = Question.objects.get_queryset().filter(
            user_id=user.id, active=True).order_by('-id')
    user_tags = questions.values_list('tags', flat=True).distinct()
    all_tags = Tag.objects.filter(id__in=user_tags)
    upload_form = UploadFileForm()
    filter_dict = {}
    question_type = request.GET.get('question_type')
    marks = request.GET.get('marks')
    language = request.GET.get('language')
    form = QuestionFilterForm(
        user=user, language=language, marks=marks, type=question_type
    )
    if question_type:
        filter_dict['type'] = str(question_type)
    if marks:
        filter_dict['points'] = marks
    if language:
        filter_dict['language'] = str(language)
    questions = questions.filter(**filter_dict).order_by('-id')
    paginator = Paginator(questions, 30)
    page = request.GET.get('page')
    questions = paginator.get_page(page)
    context = {'form': form, 'upload_form': upload_form,
               'all_tags': all_tags, 'objects': questions}
    return my_render_to_response(
        request, 'yaksh/showquestions.html', context
    )


@login_required
@email_verified
def delete_question(request, question_id):
    user = request.user
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    question = get_object_or_404(Question, pk=question_id)
    question.active = False
    question.save()
    messages.success(request, "Deleted Question Successfully")

    return my_redirect(reverse("yaksh:show_questions"))


@login_required
@email_verified
def download_question(request, question_id):
    user = request.user
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    question = Question()
    zip_file = question.dump_questions([question_id], user)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = dedent(
        '''attachment; filename={0}_question.zip'''.format(user)
    )
    zip_file.seek(0)
    response.write(zip_file.read())
    return response


@login_required
@email_verified
def test_question(request, question_id):
    user = request.user
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    trial_paper, trial_course, trial_module = test_mode(
                    user, False, [question_id], None)
    trial_paper.update_total_marks()
    trial_paper.save()
    return my_redirect(
        reverse("yaksh:start_quiz",
                args=[1, trial_module.id, trial_paper.id, trial_course.id]
                )
            )


@login_required
@email_verified
def search_questions_by_tags(request):
    user = request.user
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    questions = Question.objects.get_queryset().filter(
            user_id=user.id, active=True).order_by('-id')
    form = QuestionFilterForm(user=user)
    user_tags = questions.values_list('tags', flat=True).distinct()
    all_tags = Tag.objects.filter(id__in=user_tags)
    form = QuestionFilterForm(user=user)
    upload_form = UploadFileForm()
    question_tags = request.GET.getlist("question_tags")
    questions = _get_questions_from_tags(
        question_tags, user, questions=questions
    )
    paginator = Paginator(questions, 30)
    page = request.GET.get('page')
    questions = paginator.get_page(page)
    context = {'form': form, 'upload_form': upload_form,
               'all_tags': all_tags, 'objects': questions}
    return my_render_to_response(request, 'yaksh/showquestions.html', context)


@login_required
@email_verified
def user_data(request, user_id, questionpaper_id=None, course_id=None):
    """Render user data."""
    current_user = request.user
    if not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    user = User.objects.get(id=user_id)
    data = AnswerPaper.objects.get_user_data(user, questionpaper_id, course_id)
    context = {'data': data, 'course_id': course_id}
    return my_render_to_response(request, 'yaksh/user_data.html', context)


@login_required
@email_verified
def download_quiz_csv(request, course_id, quiz_id):
    current_user = request.user
    if not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, id=course_id)
    if not course.is_creator(current_user) and \
            not course.is_teacher(current_user):
        raise Http404('The quiz does not belong to your course')
    quiz = get_object_or_404(Quiz, id=quiz_id)
    question_paper = quiz.questionpaper_set.last()
    if request.method == 'POST':
        attempt_number = request.POST.get('attempt_number')
        questions = question_paper.get_question_bank()
        answerpapers = AnswerPaper.objects.select_related(
            "user").select_related('question_paper').prefetch_related(
            'answers').filter(
            course_id=course_id, question_paper_id=question_paper.id,
            attempt_number=attempt_number
        ).order_by("user__first_name")
        que_summaries = [
            (f"Q-{que.id}-{que.summary}-{que.points}-marks", que.id,
                f"Q-{que.id}-{que.summary}-comments"
                )
            for que in questions
        ]
        user_data = list(answerpapers.values(
            "user__username", "user__first_name", "user__last_name",
            "user__profile__roll_number", "user__profile__institute",
            "user__profile__department", "marks_obtained",
            "question_paper__total_marks", "percent", "status"
        ))
        for idx, ap in enumerate(answerpapers):
            que_data = ap.get_per_question_score(que_summaries)
            user_data[idx].update(que_data)
        df = pd.DataFrame(user_data)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = \
            'attachment; filename="{0}-{1}-attempt-{2}.csv"'.format(
                course.name.replace(' ', '_'),
                quiz.description.replace(' ', '_'), attempt_number
            )
        df.to_csv(response, index=False)
        return response
    else:
        return monitor(request, quiz_id, course_id)


@login_required
@email_verified
def grade_user(request, quiz_id=None, user_id=None, attempt_number=None,
               course_id=None, extra_context=None):
    """Present an interface with which we can easily grade a user's papers
    and update all their marks and also give comments for each paper.
    """
    current_user = request.user
    papers = AnswerPaper.objects.filter(user=current_user)
    if not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    if not course_id:
        courses = Course.objects.filter(
            Q(creator=current_user) | Q(teachers=current_user), is_trial=False
            ).order_by("-active").distinct()
        paginator = Paginator(courses, 30)
        page = request.GET.get('page')
        courses = paginator.get_page(page)
        context = {"objects": courses, "msg": "grade"}

    if quiz_id is not None:
        questionpaper_id = QuestionPaper.objects.filter(
            quiz_id=quiz_id
        ).values("id")
        user_details = AnswerPaper.objects.get_users_for_questionpaper(
            questionpaper_id, course_id
        )
        quiz = get_object_or_404(Quiz, id=quiz_id)
        course = get_object_or_404(Course, id=course_id)
        if not course.is_creator(current_user) and not \
                course.is_teacher(current_user):
            raise Http404('This course does not belong to you')
        has_quiz_assignments = AssignmentUpload.objects.filter(
                answer_paper__course_id=course_id,
                answer_paper__question_paper_id__in=questionpaper_id
            ).exists()
        context = {
            "users": user_details,
            "quiz_id": quiz_id,
            "quiz": quiz,
            "has_quiz_assignments": has_quiz_assignments,
            "course_id": course_id,
            "status": "grade"
        }
        if user_id is not None:
            attempts = AnswerPaper.objects.get_user_all_attempts(
                questionpaper_id, user_id, course_id
            )
            try:
                if attempt_number is None:
                    attempt_number = attempts[0].attempt_number
            except IndexError:
                raise Http404('No attempts for paper')

            has_user_assignments = AssignmentUpload.objects.filter(
                answer_paper__course_id=course_id,
                answer_paper__question_paper_id__in=questionpaper_id,
                answer_paper__user_id=user_id
                ).exists()
            user = User.objects.get(id=user_id)
            data = AnswerPaper.objects.get_user_data(
                user, questionpaper_id, course_id, attempt_number
            )
            context = {
                "data": data,
                "quiz_id": quiz_id,
                "quiz": quiz,
                "users": user_details,
                "attempts": attempts,
                "user_id": user_id,
                "has_user_assignments": has_user_assignments,
                "has_quiz_assignments": has_quiz_assignments,
                "course_id": course_id,
                "status": "grade"
            }
    if request.method == "POST":
        papers = data['papers']
        for paper in papers:
            for question, answers in paper.get_question_answers().items():
                marks = float(request.POST.get('q%d_marks' % question.id, 0))
                answer = answers[0]['answer']
                answer.set_marks(marks)
                answer.save()
            paper.update_marks()
            paper.comments = request.POST.get(
                'comments_%d' % paper.question_paper.id, 'No comments')
            paper.save()
        messages.success(request, "Student data saved successfully")

        course_status = CourseStatus.objects.filter(
            course_id=course.id, user_id=user.id)
        if course_status.exists():
            course_status.first().set_grade()
    if extra_context:
        context.update(extra_context)
    return my_render_to_response(request, 'yaksh/grade_user.html', context)


@login_required
@has_profile
@email_verified
def view_profile(request):
    """ view moderators and users profile """
    user = request.user
    if is_moderator(user):
        template = 'manage.html'
    else:
        template = 'user.html'
    context = {'template': template, 'user': user}
    return my_render_to_response(request, 'yaksh/view_profile.html', context)


@login_required
@email_verified
def edit_profile(request):
    """ edit profile details facility for moderator and students """

    user = request.user
    if is_moderator(user):
        template = 'manage.html'
    else:
        template = 'user.html'
    context = {'template': template}
    try:
        profile = Profile.objects.get(user_id=user.id)
    except Profile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = ProfileForm(request.POST, user=user, instance=profile)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.user = user
            form_data.user.first_name = request.POST['first_name']
            form_data.user.last_name = request.POST['last_name']
            form_data.user.save()
            form_data.save()
            return my_render_to_response(request, 'yaksh/profile_updated.html')
        else:
            context['form'] = form
            return my_render_to_response(
                request, 'yaksh/editprofile.html', context
            )
    else:
        form = ProfileForm(user=user, instance=profile)
        context['form'] = form
        return my_render_to_response(
            request, 'yaksh/editprofile.html', context
        )


@login_required
@email_verified
def search_teacher(request, course_id):
    """ search teachers for the course """
    user = request.user

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
    context['is_add_teacher'] = True
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


@login_required
@email_verified
def toggle_moderator_role(request):
    """ Allow moderator to switch to student and back """

    user = request.user

    try:
        group = Group.objects.get(name='moderator')
    except Group.DoesNotExist:
        raise Http404('The Moderator group does not exist')

    if not user.profile.is_moderator:
        raise Http404('You are not allowed to view this page!')

    if user not in group.user_set.all():
        group.user_set.add(user)
    else:
        group.user_set.remove(user)

    return my_redirect('/exam/')


@login_required
@email_verified
def add_teacher(request, course_id):
    """ add teachers to the course """

    user = request.user

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    context = {}
    course = get_object_or_404(Course, pk=course_id)
    if course.is_creator(user) or course.is_teacher(user):
        context['course'] = course
    else:
        raise Http404('You are not allowed to view this page!')

    if request.method == 'POST':
        teacher_ids = request.POST.getlist('check')
        teachers = User.objects.filter(id__in=teacher_ids)
        add_as_moderator(teachers)
        course.add_teachers(*teachers)
        context['status'] = True
        context['teachers_added'] = teachers
        messages.success(request, "Added teachers successfully")
    context['is_add_teacher'] = True
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


@login_required
@email_verified
def remove_teachers(request, course_id):
    """ remove user from a course """

    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not is_moderator(user) and (not course.is_creator(user) and
                                   course.is_teacher(user)):
        raise Http404('You are not allowed to view this page!')

    if request.method == "POST":
        teacher_ids = request.POST.getlist('remove')
        if teacher_ids:
            teachers = User.objects.filter(id__in=teacher_ids)
            course.remove_teachers(*teachers)
            messages.success(request, "Removed teachers successfully")
        else:
            messages.warning(request, "Please select atleast one teacher")
    return course_teachers(request, course_id)


def test_mode(user, godmode=False, questions_list=None, quiz_id=None,
              course_id=None):
    """creates a trial question paper for the moderators"""

    if questions_list is not None:
        trial_course = Course.objects.create_trial_course(user)
        trial_quiz = Quiz.objects.create_trial_quiz(user)
        trial_questionpaper = QuestionPaper.objects. \
            create_trial_paper_to_test_questions(
                trial_quiz, questions_list
            )
        trial_unit, created = LearningUnit.objects.get_or_create(
            order=1, type="quiz", quiz=trial_quiz,
            check_prerequisite=False)
        module, created = LearningModule.objects.get_or_create(
            order=1, creator=user, check_prerequisite=False, is_trial=True,
            name="Trial for {0}".format(trial_course.name))
        module.learning_unit.add(trial_unit)
        trial_course.learning_module.add(module.id)
    else:
        trial_quiz, trial_course, module = Quiz.objects.create_trial_from_quiz(
            quiz_id, user, godmode, course_id
        )
        trial_questionpaper = QuestionPaper.objects. \
            create_trial_paper_to_test_quiz(
                trial_quiz, quiz_id
            )
    return trial_questionpaper, trial_course, module


@login_required
@email_verified
def test_quiz(request, mode, quiz_id, course_id=None):
    """creates a trial quiz for the moderators"""
    godmode = True if mode == "godmode" else False
    current_user = request.user
    quiz = Quiz.objects.get(id=quiz_id)
    if (quiz.is_expired() or not quiz.active) and not godmode:
        messages.warning(
            request,
            "{0} is either expired or inactive".format(quiz.description)
        )
        return my_redirect(reverse("yaksh:index"))

    trial_questionpaper, trial_course, trial_module = test_mode(
        current_user, godmode, None, quiz_id, course_id)
    return my_redirect(
        reverse(
            "yaksh:start_quiz",
            args=[trial_questionpaper.id, trial_module.id,  trial_course.id]
            )
        )


@login_required
@email_verified
def view_answerpaper(request, questionpaper_id, course_id):
    user = request.user
    quiz = get_object_or_404(QuestionPaper, pk=questionpaper_id).quiz
    course = get_object_or_404(Course, pk=course_id)
    if quiz.view_answerpaper and user in course.students.all():
        data = AnswerPaper.objects.get_user_data(user, questionpaper_id,
                                                 course_id)
        has_user_assignments = AssignmentUpload.objects.filter(
            answer_paper__user=user, answer_paper__course_id=course.id,
            answer_paper__question_paper_id=questionpaper_id
        ).exists()
        context = {'data': data, 'quiz': quiz, 'course_id': course.id,
                   "has_user_assignments": has_user_assignments}
        return my_render_to_response(
            request, 'yaksh/view_answerpaper.html', context
        )
    else:
        return my_redirect('/exam/quizzes/')


@login_required
@email_verified
def create_demo_course(request):
    """ creates a demo course for user """
    user = request.user
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page")
    demo_course = Course()
    success = demo_course.create_demo(user)
    if success:
        msg = "Created Demo course successfully"
    else:
        msg = "Demo course already created"
    return prof_manage(request, msg)


@login_required
@email_verified
def regrade(request, course_id, questionpaper_id, question_id=None,
            answerpaper_id=None):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not is_moderator(user) or (course.is_creator(user) and
                                  course.is_teacher(user)):
        raise Http404('You are not allowed to view this page!')
    questionpaper = get_object_or_404(QuestionPaper, pk=questionpaper_id)
    quiz = questionpaper.quiz
    data = {"user_id": user.id, "course_id": course_id,
            "questionpaper_id": questionpaper_id, "question_id": question_id,
            "answerpaper_id": answerpaper_id, "quiz_id": quiz.id,
            "quiz_name": quiz.description, "course_name": course.name
            }
    is_celery_alive = app.control.ping()
    if is_celery_alive:
        regrade_papers.delay(data)
        msg = dedent("""
                {0} is submitted for re-evaluation. You will receive a
                notification for the re-evaluation status
                """.format(quiz.description)
            )
        messages.info(request, msg)
    else:
        msg = "Unable to submit for regrade. Please contact admin"
        messages.warning(request, msg)
    return redirect(
        reverse("yaksh:grade_user", args=[quiz.id, course_id])
    )


@login_required
@email_verified
def download_course_csv(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(
        Course.objects.prefetch_related("learning_module"), id=course_id
    )
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('You are not allowed to view this course')
    students = list(course.get_only_students().annotate(
        roll_number=F('profile__roll_number'),
        institute=F('profile__institute')
    ).values(
        "id", "first_name", "last_name", "email", "institute", "roll_number"
    ))
    que_pprs = [
        quiz.questionpaper_set.values(
            "id", "quiz__description", "total_marks")[0]
        for quiz in course.get_quizzes()
    ]
    total_course_marks = sum([qp.get("total_marks", 0) for qp in que_pprs])
    qp_ids = [
        (qp.get("id"), qp.get("quiz__description"), qp.get("total_marks"))
        for qp in que_pprs
    ]
    for student in students:
        user_course_marks = 0.0
        AnswerPaper.objects.get_user_scores(qp_ids, student, course_id)
        student["out_of"] = total_course_marks
    df = pd.DataFrame(students)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{0}.csv"'.format(
                                      (course.name).lower().replace(' ', '_'))
    output_file = df.to_csv(response, index=False)
    return response


def activate_user(request, key):
    profile = get_object_or_404(Profile, activation_key=key)
    context = {}
    context['success'] = False
    if profile.is_email_verified:
        context['activation_msg'] = "Your account is already verified"
        return my_render_to_response(
            request, 'yaksh/activation_status.html', context
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
        request, 'yaksh/activation_status.html', context
    )


def new_activation(request, email=None):
    context = {}
    if request.method == "POST":
        email = request.POST.get('email')

    try:
        user = User.objects.get(email=email)
    except MultipleObjectsReturned:
        context['email_err_msg'] = "Multiple entries found for this email "\
                                    "Please change your email"
        return my_render_to_response(
            request, 'yaksh/activation_status.html', context
        )
    except ObjectDoesNotExist:
        context['success'] = False
        context['msg'] = "Your account is not verified. \
                            Please verify your account"
        return my_render_to_response(
            request, 'yaksh/activation_status.html', context
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
        request, 'yaksh/activation_status.html', context
    )


def update_email(request):
    context = {}
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
            request, 'yaksh/activation_status.html', context
        )


@login_required
@email_verified
def download_assignment_file(request, quiz_id, course_id,
                             question_id=None, user_id=None):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if (not course.is_creator(user) and not course.is_teacher(user) and
            not course.is_student(user)):
        raise Http404("You are not allowed to download files for {0}".format(
            course.name)
        )
    qp = get_object_or_404(QuestionPaper, quiz_id=quiz_id)
    assignment_files, file_name = AssignmentUpload.objects.get_assignments(
        qp, question_id, user_id, course_id
    )
    zipfile_name = string_io()
    zip_file = zipfile.ZipFile(zipfile_name, "w")
    for f_name in assignment_files:
        folder = f_name.answer_paper.user.get_full_name().replace(" ", "_")
        sub_folder = f_name.assignmentQuestion.summary.replace(" ", "_")
        folder_name = os.sep.join((folder, sub_folder))
        download_url = f_name.assignmentFile.url
        zip_file.writestr(
            os.path.join(folder_name, os.path.basename(download_url)),
            f_name.assignmentFile.read()
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
def upload_users(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    context = {'course': course}

    if not (course.is_teacher(user) or course.is_creator(user)):
        raise Http404('You are not allowed to view this page!')
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.warning(request, "Please upload a CSV file.")
            return my_redirect(reverse('yaksh:course_students',
                                       args=[course_id]))
        csv_file = request.FILES['csv_file']
        is_csv_file, dialect = is_csv(csv_file)
        if not is_csv_file:
            messages.warning(request, "The file uploaded is not a CSV file.")
            return my_redirect(reverse('yaksh:course_students',
                                       args=[course_id]))
        required_fields = ['firstname', 'lastname', 'email']
        try:
            reader = csv.DictReader(
                csv_file.read().decode('utf-8').splitlines(),
                dialect=dialect)
        except TypeError:
            messages.warning(request, "Bad CSV file")
            return my_redirect(reverse('yaksh:course_students',
                                       args=[course_id]))
        stripped_fieldnames = [
            field.strip().lower() for field in reader.fieldnames]
        for field in required_fields:
            if field not in stripped_fieldnames:
                msg = "The CSV file does not contain the required headers"
                messages.warning(request, msg)
                return my_redirect(reverse('yaksh:course_students',
                                           args=[course_id]))
        reader.fieldnames = stripped_fieldnames
        _read_user_csv(request, reader, course)
    return my_redirect(reverse('yaksh:course_students', args=[course_id]))


def _read_user_csv(request, reader, course):
    fields = reader.fieldnames
    counter = 0
    for row in reader:
        counter += 1
        (username, email, first_name, last_name, password, roll_no, institute,
         department, remove) = _get_csv_values(row, fields)
        if not email or not first_name or not last_name:
            messages.info(request, "{0} -- Missing Values".format(counter))
            continue
        users = User.objects.filter(username=username)
        if not users.exists():
            users = User.objects.filter(email=email)
        if users.exists():
            user = users.last()
            if remove.strip().lower() == 'true':
                _remove_from_course(user, course)
                messages.info(request, "{0} -- {1} -- User rejected".format(
                              counter, user.username))
            else:
                _add_to_course(user, course)
                messages.info(
                    request,
                    "{0} -- {1} -- User Added Successfully".format(
                        counter, user.username))
            continue
        user_defaults = {'email': email, 'first_name': first_name,
                         'last_name': last_name}
        user, created = _create_or_update_user(username, password,
                                               user_defaults)
        profile_defaults = {'institute': institute, 'roll_number': roll_no,
                            'department': department,
                            'is_email_verified': True}
        _create_or_update_profile(user, profile_defaults)
        if created:
            state = "Added"
            course.students.add(user)
        else:
            state = "Updated"
        messages.info(request, "{0} -- {1} -- User {2} Successfully".format(
                      counter, user.username, state))
    if counter == 0:
        messages.warning(request, "No rows in the CSV file")


def _get_csv_values(row, fields):
    roll_no, institute, department = "", "", ""
    remove = "false"
    email, first_name, last_name = map(str.strip, [row['email'],
                                       row['firstname'],
                                       row['lastname']])
    password = email
    username = email
    if 'password' in fields and row['password']:
        password = row['password'].strip()
    if 'roll_no' in fields:
        roll_no = row['roll_no'].strip()
    if 'institute' in fields:
        institute = row['institute'].strip()
    if 'department' in fields:
        department = row['department'].strip()
    if 'remove' in fields:
        remove = row['remove'].strip()
    if 'username' in fields and row['username']:
        username = row['username'].strip()
    if 'remove' in fields:
        remove = row['remove']
    return (username, email, first_name, last_name, password,
            roll_no, institute, department, remove)


def _remove_from_course(user, course):
    if user in course.get_enrolled():
        course.reject(True, user)
    else:
        course.rejected.add(user)


def _add_to_course(user, course):
    if user in course.get_rejected():
        course.enroll(True, user)
    else:
        course.students.add(user)


def _create_or_update_user(username, password, defaults):
    user, created = User.objects.update_or_create(username=username,
                                                  defaults=defaults)
    user.set_password(password)
    user.save()
    return user, created


def _create_or_update_profile(user, defaults):
    Profile.objects.update_or_create(user=user, defaults=defaults)


@login_required
@email_verified
def download_sample_csv(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                 "sample_user_upload.csv")
    with open(csv_file_path, 'rb') as csv_file:
        response = HttpResponse(csv_file.read(), content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="sample_user_upload.csv"'
        )
        return response


@login_required
@email_verified
def download_sample_toc(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    csv_file_path = os.path.join(FIXTURES_DIR_PATH,
                                 "sample_lesson_toc.yaml")
    with open(csv_file_path, 'rb') as csv_file:
        response = HttpResponse(csv_file.read(), content_type='text/yaml')
        response['Content-Disposition'] = (
            'attachment; filename="sample_lesson_toc.yaml"'
        )
        return response


@login_required
@email_verified
def download_toc(request, course_id, lesson_id):
    user = request.user
    tmp_file_path = tempfile.mkdtemp()
    yaml_path = os.path.join(tmp_file_path, "lesson_toc.yaml")
    TableOfContents.objects.get_all_tocs_as_yaml(course_id, lesson_id, yaml_path)

    with open(yaml_path, 'r') as yml_file:
        response = HttpResponse(yml_file.read(), content_type='text/yaml')
        response['Content-Disposition'] = (
            'attachment; filename="lesson_toc.yaml"'
        )
        return response



@login_required
@email_verified
def duplicate_course(request, course_id):
    user = request.user
    course = Course.objects.get(id=course_id)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if course.is_teacher(user) or course.is_creator(user):
        # Create new entries of modules, lessons/quizzes
        # from current course to copied course
        duplicate_course = course.create_duplicate_course(user)
        msg = dedent(
            '''\
            Course duplication successful with the name {0}'''.format(
                duplicate_course.name
            )
        )
        messages.success(request, msg)
    else:
        msg = dedent(
            '''\
            You do not have permissions to clone {0} course, please contact
            your instructor/administrator.'''.format(course.name)
        )
        messages.warning(request, msg)
    return my_redirect(reverse('yaksh:courses'))


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
    response['Content-Disposition'] = (
        'attachment; filename="questions_dump.yaml"'
    )
    return response


@login_required
@email_verified
def edit_lesson(request, course_id=None, module_id=None, lesson_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    if lesson_id:
        lesson = Lesson.objects.get(id=lesson_id)
        if not lesson.creator == user and not course_id:
            raise Http404('This Lesson does not belong to you')
    else:
        lesson = None
    if module_id:
        module = get_object_or_404(LearningModule, id=module_id)
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This Lesson does not belong to you')

    context = {}
    lesson_form = LessonForm(instance=lesson)
    lesson_files_form = LessonFileForm()
    if request.method == "POST":
        if "Save" in request.POST:
            lesson_form = LessonForm(request.POST, request.FILES,
                                     instance=lesson)
            lesson_file_form = LessonFileForm(request.POST, request.FILES)
            lessonfiles = request.FILES.getlist('Lesson_files')
            clear = request.POST.get("video_file-clear")
            video_file = request.FILES.get("video_file")
            if (clear or video_file) and lesson:
                # Remove previous video file if new file is uploaded or
                # if clear is selected
                lesson.remove_file()
            if lesson_form.is_valid():
                if lesson is None:
                    last_unit = module.get_learning_units().last()
                    order = last_unit.order + 1 if last_unit else 1
                    lesson_form.instance.creator = user
                else:
                    order = module.get_unit_order("lesson", lesson)
                lesson = lesson_form.save()
                lesson.html_data = get_html_text(lesson.description)
                lesson.save()
                if lessonfiles:
                    for les_file in lessonfiles:
                        LessonFile.objects.get_or_create(
                            lesson=lesson, file=les_file
                        )
                unit, created = LearningUnit.objects.get_or_create(
                    type="lesson", lesson=lesson, order=order
                )
                if created:
                    module.learning_unit.add(unit.id)
                messages.success(
                    request, "Saved {0} successfully".format(lesson.name)
                )
                return redirect(
                    reverse("yaksh:edit_lesson",
                            args=[course_id, module_id, lesson.id])
                    )

        if 'Delete' in request.POST:
            remove_files_id = request.POST.getlist('delete_files')
            if remove_files_id:
                LessonFile.objects.filter(id__in=remove_files_id).delete()
                messages.success(
                    request, "Deleted files successfully"
                )
            else:
                messages.warning(
                    request, "Please select atleast one file to delete"
                )

        if 'upload_toc' in request.POST:
            toc_file = request.FILES.get('toc')
            file_extension = os.path.splitext(toc_file.name)[1][1:]
            if file_extension not in ['yaml', 'yml']:
                messages.warning(
                    request, "Please upload yaml or yml type file"
                )
            else:
                try:
                    toc_data = ruamel.yaml.safe_load_all(toc_file.read())
                    results = TableOfContents.objects.add_contents(
                        course_id, lesson_id, user, toc_data)
                    for status, msg in results:
                        if status == True:
                            messages.success(request, msg)
                        else:
                            messages.warning(request, msg)
                except Exception as e:
                    messages.warning(request, f"Error parsing yaml: {e}")

    data = get_toc_contents(request, course_id, lesson_id)
    context['toc'] = data
    lesson_files = LessonFile.objects.filter(lesson=lesson)
    context['lesson_form'] = lesson_form
    context['lesson_file_form'] = lesson_files_form
    context['lesson_files'] = lesson_files
    context['course_id'] = course_id
    return my_render_to_response(request, 'yaksh/add_lesson.html', context)


@login_required
@email_verified
def show_lesson(request, lesson_id, module_id, course_id):
    user = request.user
    course = Course.objects.get(id=course_id)
    if user not in course.students.all():
        raise Http404('This course does not belong to you')
    if not course.active or not course.is_active_enrollment():
        msg = "{0} is either expired or not active".format(course.name)
        return quizlist_user(request, msg=msg)
    learn_module = course.learning_module.get(id=module_id)
    learn_unit = learn_module.learning_unit.get(lesson_id=lesson_id)
    learning_units = learn_module.get_learning_units()

    if not learn_module.active:
        return view_module(request, module_id, course_id)

    if not learn_unit.lesson.active:
        msg = "{0} is not active".format(learn_unit.lesson.name)
        return view_module(request, module_id, course_id, msg)
    if learn_module.has_prerequisite():
        if not learn_module.is_prerequisite_complete(user, course):
            msg = "You have not completed the module previous to {0}".format(
                learn_module.name)
            return view_module(request, module_id, course_id, msg)
    if learn_module.check_prerequisite_passes:
        if not learn_module.is_prerequisite_passed(user, course):
            msg = (
                "You have not successfully passed the module"
                " previous to {0}".format(learn_module.name)
            )
            return view_module(request, module_id, course_id, msg)

    # update course status with current unit
    _update_unit_status(course_id, user, learn_unit)
    toc = TableOfContents.objects.filter(
        course_id=course_id, lesson_id=lesson_id
    ).order_by("time")
    contents_by_time = json.dumps(
        list(toc.values("id", "content", "time"))
    )
    all_modules = course.get_learning_modules()
    if learn_unit.has_prerequisite():
        if not learn_unit.is_prerequisite_complete(user, learn_module, course):
            msg = "You have not completed previous Lesson/Quiz/Exercise"
            return view_module(request, learn_module.id, course_id, msg=msg)
    track, created = TrackLesson.objects.get_or_create(
        user_id=user.id, course_id=course_id, lesson_id=lesson_id
        )

    lesson_ct = ContentType.objects.get_for_model(learn_unit.lesson)
    title = learn_unit.lesson.name
    try:
        post = Post.objects.get(
            target_ct=lesson_ct, target_id=learn_unit.lesson.id,
            active=True, title=title
        )
    except Post.DoesNotExist:
        post = Post.objects.create(
            target_ct=lesson_ct, target_id=learn_unit.lesson.id,
            active=True, title=title, creator=user,
            description=f'Discussion on {title} lesson',
        )
    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.creator = request.user
            new_comment.post_field = post
            new_comment.anonymous = request.POST.get('anonymous', '') == 'on'
            new_comment.save()
            return redirect(request.path_info)
        else:
            raise Http404(f'Post does not exist for lesson {title}')
    else:
        form = CommentForm()
        comments = post.comment.filter(active=True)
    context = {'lesson': learn_unit.lesson, 'user': user,
               'course': course, 'state': "lesson", "all_modules": all_modules,
               'learning_units': learning_units, "current_unit": learn_unit,
               'learning_module': learn_module, 'toc': toc,
               'contents_by_time': contents_by_time, 'track_id': track.id,
               'comments': comments, 'form': form, 'post': post}
    return my_render_to_response(request, 'yaksh/show_video.html', context)


@login_required
@email_verified
def design_module(request, module_id, course_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    context = {}
    if course_id:
        course = Course.objects.get(id=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This course does not belong to you')
    learning_module = LearningModule.objects.get(id=module_id)
    if request.method == "POST":
        if "Add" in request.POST:
            add_values = request.POST.get("chosen_list")
            to_add_list = []
            if add_values:
                add_values = add_values.split(',')
                ordered_units = learning_module.get_learning_units()
                if ordered_units.exists():
                    start_val = ordered_units.last().order + 1
                else:
                    start_val = 1
                for order, value in enumerate(add_values, start_val):
                    learning_id, type = value.split(":")
                    if type == "quiz":
                        unit, status = LearningUnit.objects.get_or_create(
                            order=order, quiz_id=learning_id,
                            type=type)
                    else:
                        unit, status = LearningUnit.objects.get_or_create(
                            order=order, lesson_id=learning_id,
                            type=type)
                    to_add_list.append(unit)
                learning_module.learning_unit.add(*to_add_list)
                messages.success(request, "Lesson/Quiz added successfully")
            else:
                messages.warning(request, "Please select a lesson/quiz to add")

        if "Change" in request.POST:
            order_list = request.POST.get("ordered_list")
            if order_list:
                order_list = order_list.split(",")
                for order in order_list:
                    learning_unit, learning_order = order.split(":")
                    if learning_order:
                        learning_unit = learning_module.learning_unit.get(
                            id=learning_unit)
                        learning_unit.order = learning_order
                        learning_unit.save()
                messages.success(request, "Order changed successfully")
            else:
                messages.warning(
                    request, "Please select a lesson/quiz to change"
                )

        if "Remove" in request.POST:
            remove_values = request.POST.getlist("delete_list")
            if remove_values:
                learning_module.learning_unit.remove(*remove_values)
                LearningUnit.objects.filter(id__in=remove_values).delete()
                messages.success(
                    request, "Lessons/quizzes deleted successfully"
                )
            else:
                messages.warning(
                    request, "Please select a lesson/quiz to remove"
                )

        if "Change_prerequisite" in request.POST:
            unit_list = request.POST.getlist("check_prereq")
            if unit_list:
                for unit in unit_list:
                    learning_unit = learning_module.learning_unit.get(id=unit)
                    learning_unit.toggle_check_prerequisite()
                    learning_unit.save()
                messages.success(
                    request, "Changed prerequisite status successfully"
                )
            else:
                messages.warning(
                    request,
                    "Please select a lesson/quiz to change prerequisite"
                )

    added_quiz_lesson = learning_module.get_added_quiz_lesson()
    quizzes = [("quiz", quiz) for quiz in Quiz.objects.filter(
               creator=user, is_trial=False)]
    lessons = [("lesson", lesson)
               for lesson in Lesson.objects.filter(creator=user)]
    quiz_les_list = set(quizzes + lessons) - set(added_quiz_lesson)
    context['quiz_les_list'] = quiz_les_list
    context['learning_units'] = learning_module.get_learning_units()
    context['status'] = 'design'
    context['module_id'] = module_id
    context['course_id'] = course_id
    context['module'] = learning_module
    return my_render_to_response(request, 'yaksh/add_module.html', context)


@login_required
@email_verified
def add_module(request, course_id=None, module_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    if course_id:
        course = Course.objects.get(id=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This course does not belong to you')
    if module_id:
        module = LearningModule.objects.get(id=module_id)
        if not module.creator == user and not course_id:
            raise Http404('This Learning Module does not belong to you')
    else:
        module = None
    context = {}
    if request.method == "POST":
        if "Save" in request.POST:
            module_form = LearningModuleForm(request.POST, instance=module)
            if module_form.is_valid():
                if module is None:
                    last_module = course.get_learning_modules().last()
                    module_form.instance.creator = user
                    if last_module:
                        module_form.instance.order = last_module.order + 1
                module = module_form.save()
                module.html_data = get_html_text(module.description)
                module.save()
                course.learning_module.add(module.id)
                messages.success(
                    request,
                    "Saved {0} successfully".format(module.name)
                )
            else:
                context['module_form'] = module_form

    module_form = LearningModuleForm(instance=module)
    context['module_form'] = module_form
    context['course_id'] = course_id
    context['status'] = "add"
    return my_render_to_response(request, "yaksh/add_module.html", context)


@login_required
@email_verified
def get_next_unit(request, course_id, module_id, current_unit_id=None,
                  first_unit=None):
    user = request.user
    course = Course.objects.prefetch_related("learning_module").get(
        id=course_id)
    if not course.students.filter(id=user.id).exists():
        raise Http404('You are not enrolled for this course!')
    learning_module = course.learning_module.prefetch_related(
        "learning_unit").get(id=module_id)

    if current_unit_id:
        current_learning_unit = learning_module.learning_unit.get(
            id=current_unit_id)
    else:
        next_module = course.next_module(learning_module.id)
        return my_redirect("/exam/quizzes/view_module/{0}/{1}".format(
            next_module.id, course_id))

    if first_unit:
        next_unit = current_learning_unit
    else:
        next_unit = learning_module.get_next_unit(current_learning_unit.id)

    course_status, created = CourseStatus.objects.get_or_create(
        user=user, course_id=course_id,
    )

    # Add learning unit to completed units list
    if not first_unit:
        course_status.completed_units.add(current_learning_unit.id)

        # Update course completion percentage
        _update_course_percent(course, user)

        # if last unit of current module go to next module
        is_last_unit = course.is_last_unit(learning_module,
                                           current_learning_unit.id)
        if is_last_unit:
            next_module = course.next_module(learning_module.id)
            return my_redirect("/exam/quizzes/view_module/{0}/{1}/".format(
                next_module.id, course.id))

    if next_unit.type == "quiz":
        return my_redirect("/exam/start/{0}/{1}/{2}".format(
            next_unit.quiz.questionpaper_set.get().id, module_id, course_id))
    else:
        return my_redirect("/exam/show_lesson/{0}/{1}/{2}".format(
            next_unit.lesson.id, module_id, course_id))


@login_required
@email_verified
def design_course(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = Course.objects.get(id=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    context = {}
    if request.method == "POST":
        if "Add" in request.POST:
            add_values = request.POST.getlist("module_list")
            to_add_list = []
            if add_values:
                ordered_modules = course.get_learning_modules()
                if ordered_modules.exists():
                    start_val = ordered_modules.last().order + 1
                else:
                    start_val = 1
                for order, value in enumerate(add_values, start_val):
                    module, created = LearningModule.objects.get_or_create(
                        id=int(value)
                    )
                    module.order = order
                    module.save()
                    to_add_list.append(module)
                course.learning_module.add(*to_add_list)
                messages.success(request, "Modules added successfully")
            else:
                messages.warning(request, "Please select atleast one module")

        if "Change" in request.POST:
            order_list = request.POST.get("ordered_list")
            if order_list:
                order_list = order_list.split(",")
                for order in order_list:
                    learning_unit, learning_order = order.split(":")
                    if learning_order:
                        learning_module = course.learning_module.get(
                            id=learning_unit)
                        learning_module.order = learning_order
                        learning_module.save()
                messages.success(request, "Changed order successfully")
            else:
                messages.warning(request, "Please select atleast one module")

        if "Remove" in request.POST:
            remove_values = request.POST.getlist("delete_list")
            if remove_values:
                course.learning_module.remove(*remove_values)
                messages.success(request, "Modules removed successfully")
            else:
                messages.warning(request, "Please select atleast one module")

        if "change_prerequisite_completion" in request.POST:
            unit_list = request.POST.getlist("check_prereq")
            if unit_list:
                for unit in unit_list:
                    learning_module = course.learning_module.get(id=unit)
                    learning_module.toggle_check_prerequisite()
                    learning_module.save()
                messages.success(
                    request, "Changed prerequisite check successfully"
                )
            else:
                messages.warning(request, "Please select atleast one module")

        if "change_prerequisite_passing" in request.POST:
            unit_list = request.POST.getlist("check_prereq_passes")
            if unit_list:
                for unit in unit_list:
                    learning_module = course.learning_module.get(id=unit)
                    learning_module.toggle_check_prerequisite_passes()
                    learning_module.save()
                messages.success(
                    request, "Changed prerequisite check successfully"
                )
            else:
                messages.warning(request, "Please select atleast one module")

    added_learning_modules = course.get_learning_modules()
    all_learning_modules = LearningModule.objects.filter(
        creator=user, is_trial=False)

    learning_modules = set(all_learning_modules) - set(added_learning_modules)
    context['added_learning_modules'] = added_learning_modules
    context['learning_modules'] = learning_modules
    context['course'] = course
    context['is_design_course'] = True
    return my_render_to_response(
        request, 'yaksh/course_detail.html', context
    )


@login_required
@email_verified
def view_module(request, module_id, course_id, msg=None):
    user = request.user
    course = Course.objects.get(id=course_id)
    if user not in course.students.all():
        raise Http404('You are not enrolled for this course!')
    context = {}
    if not course.active or not course.is_active_enrollment():
        msg = "{0} is either expired or not active".format(course.name)
        return course_modules(request, course_id, msg)
    learning_module = course.learning_module.get(id=module_id)

    if not learning_module.active:
        msg = "{0} is not active".format(learning_module.name)
        return course_modules(request, course_id, msg)
    all_modules = course.get_learning_modules()
    if learning_module.has_prerequisite():
        if not learning_module.is_prerequisite_complete(user, course):
            msg = "You have not completed the module previous to {0}".format(
                learning_module.name)
            return course_modules(request, course_id, msg)

    if learning_module.check_prerequisite_passes:
        if not learning_module.is_prerequisite_passed(user, course):
            msg = (
                "You have not successfully passed the module"
                " previous to {0}".format(learning_module.name)
            )
            return course_modules(request, course_id, msg)

    learning_units = learning_module.get_learning_units()
    context['learning_units'] = learning_units
    context['learning_module'] = learning_module
    context['first_unit'] = learning_units.first()
    context['all_modules'] = all_modules
    context['user'] = user
    context['course'] = course
    context['state'] = "module"
    context['msg'] = msg
    return my_render_to_response(request, 'yaksh/show_video.html', context)


@login_required
@email_verified
def course_modules(request, course_id, msg=None):
    user = request.user
    course = Course.objects.get(id=course_id)
    if user not in course.students.all():
        msg = 'You are not enrolled for this course!'
        return quizlist_user(request, msg=msg)

    if not course.active or not course.is_active_enrollment():
        msg = "{0} is either expired or not active".format(course.name)
        return quizlist_user(request, msg=msg)
    learning_modules = course.get_learning_modules()
    context = {"course": course, "user": user, "msg": msg}
    course_status = CourseStatus.objects.filter(course=course, user=user)
    context['course_percentage'] = course.get_completion_percent(user)
    context['modules'] = [
        (module, module.get_module_complete_percent(course, user))
        for module in learning_modules
        ]
    if course_status.exists():
        course_status = course_status.first()
        if not course_status.grade:
            course_status.set_grade()
        context['grade'] = course_status.get_grade()
    return my_render_to_response(request, 'yaksh/course_modules.html', context)


@login_required
@email_verified
def course_status(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    students = course.students.order_by("-id")
    students_no = students.count()
    paginator = Paginator(students, 100)
    page = request.GET.get('page')
    students = paginator.get_page(page)

    stud_details = [(student, course.get_grade(student),
                     course.get_completion_percent(student),
                     course.get_current_unit(student.id))
                    for student in students.object_list]
    context = {
        'course': course, 'objects': students, 'is_progress': True,
        'student_details': stud_details, 'students_no': students_no
    }
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


def _update_unit_status(course_id, user, unit):
    """ Update course status with current unit """
    course_status, created = CourseStatus.objects.get_or_create(
        user=user, course_id=course_id,
    )
    # make next available unit as current unit
    course_status.set_current_unit(unit)


def _update_course_percent(course, user):
    course_status, created = CourseStatus.objects.get_or_create(
        user=user, course=course,
    )
    # Update course completion percent
    modules = course.get_learning_modules()
    course_status.percent_completed = course.percent_completed(user, modules)
    course_status.save()


@login_required
@email_verified
def preview_questionpaper(request, questionpaper_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    paper = QuestionPaper.objects.get(id=questionpaper_id)
    context = {
        'questions': paper._get_questions_for_answerpaper(),
        'paper': paper,
    }

    return my_render_to_response(
        request, 'yaksh/preview_questionpaper.html', context
    )


@login_required
@email_verified
def get_user_data(request, course_id, student_id):
    user = request.user
    data = {}
    response_kwargs = {}
    response_kwargs['content_type'] = 'application/json'
    course = Course.objects.get(id=course_id)
    if not is_moderator(user):
        data['msg'] = 'You are not a moderator'
        data['status'] = False
    elif not course.is_creator(user) and not course.is_teacher(user):
        msg = dedent(
            """\
            You are neither course creator nor course teacher for {0}
            """.format(course.name)
            )
        data['msg'] = msg
        data['status'] = False
    else:
        student = User.objects.get(id=student_id)
        data['status'] = True
        modules = course.get_learning_modules()
        module_percent = [
            (module, module.get_module_complete_percent(course, student))
            for module in modules
            ]
        data['modules'] = module_percent
        _update_course_percent(course, student)
        data['course_percentage'] = course.get_completion_percent(student)
        data['student'] = student
    template_path = os.path.join(
        os.path.dirname(__file__), "templates", "yaksh", "user_status.html"
        )
    with open(template_path) as f:
        template_data = f.read()
        template = Template(template_data)
        context = Context(data)
        data = template.render(context)
    return HttpResponse(json.dumps({"user_data": data}), **response_kwargs)


@login_required
@email_verified
def download_course(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if (not course.is_creator(user) and not course.is_teacher(user) and not
            course.is_student(user)):
        raise Http404("You are not allowed to download {0} course".format(
            course.name))
    if not course.has_lessons():
        raise Http404("{0} course does not have any lessons".format(
            course.name))
    current_dir = os.path.dirname(__file__)
    course_name = course.name.replace(" ", "_")

    # Static files required for styling in html template
    static_files = {"js": ["bootstrap.min.js",
                           "jquery-3.3.1.min.js", "video.js"],
                    "css": ["bootstrap.min.css",
                            "video-js.css", "offline.css",
                            "yakshcustom.css"],
                    "images": ["yaksh_banner.png"]}
    zip_file = course.create_zip(current_dir, static_files)
    zip_file.seek(0)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename={0}.zip'.format(
                                            course_name
                                            )
    response.write(zip_file.read())
    return response


@login_required
@email_verified
def course_students(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404("You are not allowed to view {0}".format(
            course.name))
    enrolled_users = course.get_enrolled()
    requested_users = course.get_requests()
    rejected_users = course.get_rejected()
    context = {
        "enrolled_users": enrolled_users,
        "requested_users": requested_users,
        "course": course,
        "rejected_users": rejected_users,
        "is_students": True
    }
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


@login_required
@email_verified
def course_teachers(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404("You are not allowed to view {0}".format(
            course.name))
    teachers = course.get_teachers()
    context = {"teachers": teachers, "is_teachers": True, "course": course}
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


@login_required
@email_verified
def get_course_modules(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404("You are not allowed to view {0}".format(
            course.name))
    modules = course.get_learning_modules()
    context = {"modules": modules, "is_modules": True, "course": course}
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


@login_required
@email_verified
def download_course_progress(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    students = course.students.order_by("-id").values_list("id")
    stud_details = list(CourseStatus.objects.filter(
        course_id=course_id, user_id__in=students
    ).values(
        "user_id", "user__first_name", "user__last_name",
        "grade", "percent_completed"
    ))
    for student in stud_details:
        student["current_unit"] = course.get_current_unit(
            student.pop("user_id")
        )
    df = pd.DataFrame(stud_details)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{0}.csv"'.format(
                                      (course.name).lower().replace(' ', '_'))
    df.to_csv(response, index=False)
    return response


@login_required
@email_verified
def view_notifications(request):
    user = request.user
    notifcations = Notification.objects.get_unread_receiver_notifications(
        user.id
    )
    if is_moderator(user):
        template = "manage.html"
    else:
        template = "user.html"
    context = {"template": template, "notifications": notifcations,
               "current_date_time": timezone.now()}
    return my_render_to_response(
        request, 'yaksh/view_notifications.html', context
    )


@login_required
@email_verified
def mark_notification(request, message_uid=None):
    user = request.user
    if message_uid:
        Notification.objects.mark_single_notification(
            user.id, message_uid, True
        )
    else:
        if request.method == 'POST':
            msg_uuids = request.POST.getlist("uid")
            Notification.objects.mark_bulk_msg_notifications(
                user.id, msg_uuids, True)
    messages.success(request, "Marked notifcation(s) as read")
    return redirect(reverse("yaksh:view_notifications"))


@login_required
@email_verified
def course_forum(request, course_id):
    user = request.user
    base_template = 'user.html'
    moderator = False
    if is_moderator(user):
        base_template = 'manage.html'
        moderator = True
    course = get_object_or_404(Course, id=course_id)
    course_ct = ContentType.objects.get_for_model(course)
    if (not course.is_creator(user) and not course.is_teacher(user)
            and not course.is_student(user)):
        raise Http404('You are not enrolled in {0} course'.format(course.name))
    search_term = request.GET.get('search_post')
    if search_term:
        posts = Post.objects.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term),
                target_ct=course_ct, target_id=course.id, active=True
            )
    else:
        posts = Post.objects.filter(
            target_ct=course_ct, target_id=course.id, active=True
        ).order_by('-modified_at')
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.creator = user
            new_post.target = course
            new_post.anonymous = request.POST.get('anonymous', '') == 'on'
            new_post.save()
            messages.success(request, "Added post successfully")
            return redirect('yaksh:post_comments',
                            course_id=course.id, uuid=new_post.uid)
    else:
        form = PostForm()
    return render(request, 'yaksh/course_forum.html', {
        'user': user,
        'course': course,
        'base_template': base_template,
        'moderator': moderator,
        'objects': posts,
        'form': form,
        'user': user
        })


@login_required
@email_verified
def lessons_forum(request, course_id):
    user = request.user
    base_template = 'user.html'
    moderator = False
    if is_moderator(user):
        base_template = 'manage.html'
        moderator = True
    course = get_object_or_404(Course, id=course_id)
    course_ct = ContentType.objects.get_for_model(course)
    lesson_posts = course.get_lesson_posts()
    return render(request, 'yaksh/lessons_forum.html', {
        'user': user,
        'base_template': base_template,
        'moderator': moderator,
        'course': course,
        'posts': lesson_posts,
    })


@login_required
@email_verified
def post_comments(request, course_id, uuid):
    user = request.user
    base_template = 'user.html'
    if is_moderator(user):
        base_template = 'manage.html'
    post = get_object_or_404(Post, uid=uuid)
    comments = post.comment.filter(active=True)
    course = get_object_or_404(Course, id=course_id)
    if (not course.is_creator(user) and not course.is_teacher(user)
            and not course.is_student(user)):
        raise Http404('You are not enrolled in {0} course'.format(course.name))
    form = CommentForm()
    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.creator = request.user
            new_comment.post_field = post
            new_comment.anonymous = request.POST.get('anonymous', '') == 'on'
            new_comment.save()
            messages.success(request, "Added comment successfully")
            return redirect(request.path_info)
    return render(request, 'yaksh/post_comments.html', {
        'post': post,
        'comments': comments,
        'base_template': base_template,
        'form': form,
        'user': user,
        'course': course
        })


@login_required
@email_verified
def hide_post(request, course_id, uuid):
    user = request.user
    course = get_object_or_404(Course, id=course_id)
    if (not course.is_creator(user) and not course.is_teacher(user)):
        raise Http404(
            'Only a course creator or a teacher can delete the post.'
        )
    post = get_object_or_404(Post, uid=uuid)
    post.comment.active = False
    post.active = False
    post.save()
    messages.success(request, "Post deleted successfully")
    return redirect('yaksh:course_forum', course_id)


@login_required
@email_verified
def hide_comment(request, course_id, uuid):
    user = request.user
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        if (not course.is_creator(user) and not course.is_teacher(user)):
            raise Http404(
                'Only a course creator or a teacher can delete the comments'
            )
    comment = get_object_or_404(Comment, uid=uuid)
    post_uid = comment.post_field.uid
    comment.active = False
    comment.save()
    messages.success(request, "Post comment deleted successfully")
    return redirect('yaksh:post_comments', course_id, post_uid)


@login_required
@email_verified
def add_marker(request, course_id, lesson_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    content_type = request.POST.get("content")
    question_type = request.POST.get("type")
    if content_type == '1':
        form = TopicForm()
        template_name = 'yaksh/add_topic.html'
        status = 1
        formset = None
        tc_class = None
    else:
        if not question_type:
            question_type = "mcq"
        form = VideoQuizForm(question_type=question_type)
        formset, tc_class = get_tc_formset(question_type)
        template_name = 'yaksh/add_video_quiz.html'
        status = 2
    context = {'form': form, 'course_id': course.id, 'lesson_id': lesson_id,
               'formset': formset, 'tc_class': tc_class,
               'content_type': content_type}
    data = loader.render_to_string(
        template_name, context=context, request=request
    )
    return JsonResponse(
        {'success': True, 'data': data, 'content_type': content_type,
         'status': status}
    )


def get_tc_formset(question_type, post=None, question=None):
    tc, tc_class = McqTestCase, 'mcqtestcase'
    if question_type == 'mcq' or question_type == 'mcc':
        tc, tc_class = McqTestCase, 'mcqtestcase'
    elif question_type == 'integer':
        tc, tc_class = IntegerTestCase, 'integertestcase'
    elif question_type == 'float':
        tc, tc_class = FloatTestCase, 'floattestcase'
    elif question_type == 'string':
        tc, tc_class = StringTestCase, 'stringtestcase'
    TestcaseFormset = inlineformset_factory(
        Question, tc, form=TestcaseForm, extra=1, fields="__all__",
    )
    formset = TestcaseFormset(
        post, initial=[{'type': tc_class}], instance=question
    )
    return formset, tc_class


def get_toc_contents(request, course_id, lesson_id):
    contents = TableOfContents.objects.filter(
        course_id=course_id, lesson_id=lesson_id
    ).order_by("time")
    data = loader.render_to_string(
        "yaksh/show_toc.html", context={
            'contents': contents, 'lesson_id': lesson_id
        },
        request=request
    )
    return data


@login_required
@email_verified
def allow_special_attempt(request, user_id, course_id, quiz_id):
    user = request.user

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    quiz = get_object_or_404(Quiz, pk=quiz_id)
    student = get_object_or_404(User, pk=user_id)

    if not course.is_enrolled(student):
        raise Http404('The student is not enrolled for this course')

    micromanager, created = MicroManager.objects.get_or_create(
        course=course, student=student, quiz=quiz
    )
    micromanager.manager = user
    micromanager.save()

    if (not micromanager.is_special_attempt_required() or
            micromanager.is_last_attempt_inprogress()):
        name = student.get_full_name()
        msg = '{} can attempt normally. No special attempt required!'.format(
            name)
    elif micromanager.can_student_attempt():
        msg = '{} already has a special attempt!'.format(
            student.get_full_name())
    else:
        micromanager.allow_special_attempt()
        msg = 'A special attempt is provided to {}!'.format(
            student.get_full_name())

    messages.info(request, msg)
    return redirect('yaksh:monitor', quiz_id, course_id)


@login_required
@email_verified
def add_topic(request, content_type, course_id, lesson_id, toc_id=None,
              topic_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    if topic_id:
        topic = get_object_or_404(Topic, pk=topic_id)
    else:
        topic = None
    if toc_id:
        toc = get_object_or_404(TableOfContents, pk=toc_id)
    else:
        toc = None
    context = {}
    if request.method == "POST":
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            time = request.POST.get("timer")
            if not topic:
                TableOfContents.objects.create(
                    content_object=form.instance, course_id=course_id,
                    lesson_id=lesson_id, content=content_type,
                    time=time
                )
            context['toc'] = get_toc_contents(request, course_id, lesson_id)
            if toc:
                toc.time = time
                toc.save()
            status_code = 200
            context['success'] = True
            context['message'] = 'Saved topic successfully'
        else:
            status_code = 400
            context['success'] = False
            context['message'] = form.errors.as_json()
    else:
        form = TopicForm(instance=topic, time=toc.time)
        template_context = {'form': form, 'course_id': course.id,
                   'lesson_id': lesson_id, 'content_type': content_type,
                   'topic_id': topic_id, 'toc_id': toc_id}
        data = loader.render_to_string(
            "yaksh/add_topic.html", context=template_context, request=request
        )
        context['success'] = True
        context['data'] = data
        context['content_type'] = content_type
        context['status'] = 1
        status_code = 200
    return JsonResponse(context, status=status_code)


@login_required
@email_verified
def add_marker_quiz(request, content_type, course_id, lesson_id,
                    toc_id=None, question_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    if question_id:
        question = get_object_or_404(Question, pk=question_id)
    else:
        question = None
    if toc_id:
        toc = get_object_or_404(TableOfContents, pk=toc_id)
    else:
        toc = None
    context = {}
    if request.method == "POST":
        qform = VideoQuizForm(request.POST, instance=question)
        if qform.is_valid():
            if not question_id:
                qform.save(commit=False)
                qform.instance.user = user
            qform.save()
            formset, tc_class = get_tc_formset(
                qform.instance.type, request.POST, qform.instance
            )
            if formset.is_valid():
                formset.save()
                time = request.POST.get("timer")
                if not question:
                    TableOfContents.objects.create(
                        content_object=qform.instance, course_id=course_id,
                        lesson_id=lesson_id, content=content_type,
                        time=time
                    )
                context['toc'] = get_toc_contents(request, course_id, lesson_id)
                if toc:
                    toc.time = time
                    toc.save()
                status_code = 200
                context['success'] = True
                context['message'] = 'Saved question successfully'
                context['content_type'] = content_type
            else:
                status_code = 200
                context['success'] = False
                context['message'] = "Error in saving."\
                                     " Please check the question test cases"
        else:
            status_code = 400
            context['success'] = False
            context['message'] = qform.errors.as_json()
    else:
        form = VideoQuizForm(instance=question, time=toc.time)
        formset, tc_class = get_tc_formset(question.type, question=question)
        template_context = {
            'form': form, 'course_id': course.id, 'lesson_id': lesson_id,
            'formset': formset, 'tc_class': tc_class, 'toc_id': toc_id,
            'content_type': content_type, 'question_id': question_id
        }
        data = loader.render_to_string(
            "yaksh/add_video_quiz.html", context=template_context,
            request=request
        )
        context['success'] = True
        context['data'] = data
        context['content_type'] = content_type
        context['status'] = 2
        status_code = 200
    return JsonResponse(context, status=status_code)


@login_required
@email_verified
def revoke_special_attempt(request, micromanager_id):
    user = request.user

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    micromanager = get_object_or_404(MicroManager, pk=micromanager_id)
    course = micromanager.course
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    micromanager.revoke_special_attempt()
    msg = 'Revoked special attempt for {}'.format(
        micromanager.student.get_full_name())
    messages.info(request, msg)
    return redirect(
        'yaksh:monitor', micromanager.quiz.id, course.id)


@login_required
@email_verified
def delete_toc(request, course_id, toc_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    toc = get_object_or_404(TableOfContents, pk=toc_id)
    redirect_url = request.POST.get("redirect_url")
    if toc.content == 1:
        get_object_or_404(Topic, pk=toc.object_id).delete()
    else:
        get_object_or_404(Question, id=toc.object_id).delete()
    messages.success(request, "Content deleted successfully")
    return redirect(redirect_url)


@login_required
@email_verified
def extend_time(request, paper_id):
    user = request.user

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    anspaper = get_object_or_404(AnswerPaper, pk=paper_id)
    course = anspaper.course
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    if request.method == "POST":
        extra_time = float(request.POST.get('extra_time', 0))
        if extra_time is None:
            msg = 'Please provide time'
        else:
            anspaper.set_extra_time(extra_time)
            msg = 'Extra {0} minutes given to {1}'.format(
                extra_time, anspaper.user.get_full_name())
    else:
        msg = 'Bad Request'
    messages.info(request, msg)
    return redirect(
        'yaksh:monitor', anspaper.question_paper.quiz.id, course.id
    )


@login_required
@email_verified
def get_marker_quiz(request, course_id, toc_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_student(user):
        raise Http404("You are not allowed to view this page")
    toc = get_object_or_404(TableOfContents, pk=toc_id)
    question = toc.content_object
    template_context = {
        "question": question, "course_id": course_id, "toc": toc,
        "test_cases": question.get_test_cases()
    }
    data = loader.render_to_string(
        "yaksh/show_lesson_quiz.html", context=template_context,
        request=request
    )
    context = {"data": data, "success": True}
    return JsonResponse(context)


@login_required
@email_verified
def submit_marker_quiz(request, course_id, toc_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_student(user):
        raise Http404("You are not allowed to view this page")
    toc = get_object_or_404(TableOfContents, pk=toc_id)
    current_question = toc.content_object
    if current_question.type == 'mcq':
        user_answer = request.POST.get('answer')
    elif current_question.type == 'integer':
        try:
            user_answer = int(request.POST.get('answer'))
        except ValueError:
            user_answer = None
    elif current_question.type == 'float':
        try:
            user_answer = float(request.POST.get('answer'))
        except ValueError:
            user_answer = None
    elif current_question.type == 'string':
        user_answer = str(request.POST.get('answer'))
    elif current_question.type == 'mcc':
        user_answer = request.POST.getlist('answer')
    elif current_question.type == 'arrange':
        user_answer_ids = request.POST.get('answer').split(',')
        user_answer = [int(ids) for ids in user_answer_ids]

    def is_valid_answer(answer):
        status = True
        if ((current_question.type == "mcc" or
                current_question.type == "arrange") and not answer):
            status = False
        elif answer is None or not str(answer):
            status = False
        return status

    if is_valid_answer(user_answer):
        success = True
        # check if graded quiz and already attempted
        has_attempts =  LessonQuizAnswer.objects.filter(
            toc_id=toc_id, student_id=user.id).exists()
        if ((toc.content == 2 and not has_attempts) or
                toc.content == 3 or toc.content == 4):
            answer = Answer.objects.create(
                question_id=current_question.id, answer=user_answer,
                correct=False, error=json.dumps([])
            )
            lesson_ans = LessonQuizAnswer.objects.create(
                toc_id=toc_id, student=user, answer=answer
            )
            msg = "Answer saved successfully"
            # call check answer only for graded quiz and exercise
            if toc.content == 3 or toc.content == 2:
                result = lesson_ans.check_answer(user_answer)
                # if exercise then show custom message
                if toc.content == 3:
                    if result.get("success"):
                        msg = "You answered the question correctly"
                    else:
                        success = False
                        msg = "You have answered the question incorrectly. "\
                              "Please refer the lesson again"
        else:
            msg = "You have already submitted the answer"
    else:
        success = False
        msg = "Please submit a valid answer"
    context = {"success": success, "message": msg}
    return JsonResponse(context)


@login_required
@email_verified
def lesson_statistics(request, course_id, lesson_id, toc_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    context = {}
    lesson = get_object_or_404(Lesson, id=lesson_id)
    data = TableOfContents.objects.get_data(course_id, lesson_id)
    context['data'] = data
    context['lesson'] = lesson
    context['course_id'] = course_id
    if toc_id:
        per_que_data = TableOfContents.objects.get_question_stats(toc_id)
        question = per_que_data[0]
        answers = per_que_data[1]
        is_percent_reqd = (
            True if question.type == "mcq" or question.type == "mcc"
                else False
            )
        per_tc_ans, total_count = TableOfContents.objects.get_per_tc_ans(
            toc_id, question.type, is_percent_reqd
        )
        context['per_tc_ans'] = per_tc_ans
        context['total_count'] = total_count
        paginator = Paginator(answers, 50)
        context['question'] = question
        page = request.GET.get('page')
        per_que_data = paginator.get_page(page)
        context['is_que_data'] = True
        context['objects'] = per_que_data
    return render(request, 'yaksh/show_lesson_statistics.html', context)


@login_required
@email_verified
def upload_marks(request, course_id, questionpaper_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    question_paper = get_object_or_404(QuestionPaper, pk=questionpaper_id)
    quiz = question_paper.quiz

    if not (course.is_teacher(user) or course.is_creator(user)):
        raise Http404('You are not allowed to view this page!')
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.warning(request, "Please upload a CSV file.")
            return redirect('yaksh:monitor', quiz.id, course_id)
        csv_file = request.FILES['csv_file']
        is_csv_file, dialect = is_csv(csv_file)
        if not is_csv_file:
            messages.warning(request, "The file uploaded is not a CSV file.")
            return redirect('yaksh:monitor', quiz.id, course_id)
        data = {
            "course_id": course_id, "questionpaper_id": questionpaper_id,
            "csv_data": csv_file.read().decode('utf-8').splitlines(),
            "user_id": request.user.id
        }
        is_celery_alive = app.control.ping()
        if is_celery_alive:
            update_user_marks.delay(data)
            msg = dedent("""
                {0} is submitted for marks update. You will receive a
                notification for the update status
                """.format(quiz.description)
            )
            messages.info(request, msg)
        else:
            msg = "Unable to submit for marks update. Please check with admin"
            messages.warning(request, msg)
    return redirect('yaksh:monitor', quiz.id, course_id)


def _get_header_info(reader):
    user_ids, question_ids = [], []
    fields = reader.fieldnames
    for field in fields:
        if field.startswith('Q') and field.count('-') > 0:
            qid = int(field.split('-')[1])
            if qid not in question_ids:
                question_ids.append(qid)
    return question_ids


def _read_marks_csv(request, reader, course, question_paper, question_ids):
    messages.info(request, 'Marks Uploaded!')
    for row in reader:
        username = row['username']
        user = User.objects.filter(username=username).first()
        if user:
            answerpapers = question_paper.answerpaper_set.filter(
                course=course, user_id=user.id)
        else:
            messages.info(request, '{0} user not found!'.format(username))
            continue
        answerpaper = answerpapers.last()
        if not answerpaper:
            messages.info(request, '{0} has no answerpaper!'.format(username))
            continue
        answers = answerpaper.answers.all()
        questions = answerpaper.questions.all().values_list('id', flat=True)
        for qid in question_ids:
            question = Question.objects.filter(id=qid).first()
            if not question:
                messages.info(request,
                              '{0} is an invalid question id!'.format(qid))
                continue
            if qid in questions:
                answer = answers.filter(question_id=qid).last()
                if not answer:
                    answer = Answer(question_id=qid, marks=0, correct=False,
                                    answer='Created During Marks Update!',
                                    error=json.dumps([]))
                    answer.save()
                    answerpaper.answers.add(answer)
                key1 = 'Q-{0}-{1}-{2}-marks'.format(qid, question.summary,
                                                    question.points)
                key2 = 'Q-{0}-{1}-comments'.format(qid, question.summary,
                                                   question.points)
                if key1 in reader.fieldnames:
                    try:
                        answer.set_marks(float(row[key1]))
                    except ValueError:
                        messages.info(request,
                                      '{0} invalid marks!'.format(row[key1]))
                if key2 in reader.fieldnames:
                    answer.set_comment(row[key2])
                answer.save()
        answerpaper.update_marks(state='completed')
        answerpaper.save()
        messages.info(
            request,
            'Updated successfully for user: {0}, question: {1}'.format(
            username, question.summary))


@login_required
@email_verified
def generate_qrcode(request, answerpaper_id, question_id, module_id):
    user = request.user
    answerpaper = get_object_or_404(AnswerPaper, pk=answerpaper_id)
    question = get_object_or_404(Question, pk=question_id)

    if not answerpaper.is_attempt_inprogress():
        pass
    handler = QRcodeHandler.objects.get_or_create(user=user, question=question,
                                                  answerpaper=answerpaper)[0]
    qrcode = handler.get_qrcode()
    if not qrcode.is_qrcode_available():
        content = request.build_absolute_uri(
            reverse("yaksh:upload_file", args=[qrcode.short_key])
        )
        qrcode.generate_image(content)
    return redirect(
        reverse(
            'yaksh:skip_question',
            kwargs={'q_id': question_id, 'next_q': question_id,
                    'attempt_num': answerpaper.attempt_number,
                    'module_id': module_id,
                    'questionpaper_id': answerpaper.question_paper.id,
                    'course_id': answerpaper.course_id}
        )
    )


def upload_file(request, key):
    qrcode = get_object_or_404(QRcode, short_key=key, active=True, used=False)
    handler = qrcode.handler
    context = {'question': handler.question, 'key': qrcode.short_key}
    if not handler.can_use():
        context['success'] = True
        context['msg'] = 'Sorry, test time up!'
        return render(request, 'yaksh/upload_file.html', context)
    if request.method == 'POST':
        assign_files = []
        assignments = request.FILES
        for i in range(len(assignments)):
            assign_files.append(assignments[f"assignment[{i}]"])
        if not assign_files:
            msg = 'Please upload assignment file'
            context['msg'] = msg
            return render(request, 'yaksh/upload_file.html', context)
        AssignmentUpload.objects.filter(
            assignmentQuestion_id=handler.question_id,
            answer_paper_id=handler.answerpaper_id
            ).delete()
        uploaded_files = []
        for fname in assign_files:
            fname._name = fname._name.replace(" ", "_")
            uploaded_files.append(
                AssignmentUpload(
                    assignmentQuestion_id=handler.question_id,
                    assignmentFile=fname,
                    answer_paper_id=handler.answerpaper_id)
                )
        AssignmentUpload.objects.bulk_create(uploaded_files)
        user_answer = 'ASSIGNMENT UPLOADED'
        new_answer = Answer(
            question=handler.question, answer=user_answer,
            correct=False, error=json.dumps([])
        )
        new_answer.save()
        paper = handler.answerpaper
        paper.answers.add(new_answer)
        next_q = paper.add_completed_question(handler.question_id)
        qrcode.set_used()
        qrcode.deactivate()
        qrcode.save()
        context['success'] = True
        msg = "File Uploaded Successfully! Reload the (test)question "\
              "page to see the uploaded file"
        context['msg'] = msg
        return render(request, 'yaksh/upload_file.html', context)
    return render(request, 'yaksh/upload_file.html', context)


@login_required
@email_verified
def upload_download_course_md(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == "POST":
        from upload.views import upload_course_md
        status, msg = upload_course_md(request)
        if status:
            messages.success(request, "MD File Successfully uploaded to course")
        else:
            messages.warning(request, "{0}".format(msg))
        return redirect(
            'yaksh:course_detail', course.id
        )
    else:
        context = {
            'course': course,
            'is_upload_download_md': True,
        }
        return my_render_to_response(request, 'yaksh/course_detail.html', context)
