import os
import csv
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Context, Template
from django.http import Http404
from django.db.models import Max, Q, F
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.forms.models import inlineformset_factory
from django.utils import timezone
from django.core.exceptions import (
    MultipleObjectsReturned, ObjectDoesNotExist
)
from taggit.models import Tag
import json
import six
from textwrap import dedent
import zipfile
from markdown import Markdown
try:
    from StringIO import StringIO as string_io
except ImportError:
    from io import BytesIO as string_io
import re
# Local imports.
from yaksh.code_server import get_result as get_result_from_code_server
from yaksh.models import (
    Answer, AnswerPaper, AssignmentUpload, Course, FileUpload, FloatTestCase,
    HookTestCase, IntegerTestCase, McqTestCase, Profile,
    QuestionPaper, QuestionSet, Quiz, Question, StandardTestCase,
    StdIOBasedTestCase, StringTestCase, TestCase, User,
    get_model_class, FIXTURES_DIR_PATH, MOD_GROUP_NAME, Lesson, LessonFile,
    LearningUnit, LearningModule, CourseStatus, question_types
)
from yaksh.forms import (
    UserRegisterForm, UserLoginForm, QuizForm, QuestionForm,
    QuestionFilterForm, CourseForm, ProfileForm,
    UploadFileForm, FileForm, QuestionPaperForm, LessonForm,
    LessonFileForm, LearningModuleForm, ExerciseForm
)
from yaksh.settings import SERVER_POOL_PORT, SERVER_HOST_NAME
from .settings import URL_ROOT
from .file_utils import extract_files, is_csv
from .send_emails import (send_user_mail,
                          generate_activation_key, send_bulk_mail)
from .decorators import email_verified, has_profile

from permissions.utils import check_permission


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
        return user.profile.is_moderator and user in group.user_set.all()
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


CSV_FIELDS = ['name', 'username', 'roll_number', 'institute', 'department',
              'questions', 'marks_obtained', 'out_of', 'percentage', 'status']


def get_html_text(md_text):
    """Takes markdown text and converts it to html"""
    return Markdown().convert(md_text)


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
    if user.is_authenticated():
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
        courses = hidden_courses if hidden_courses else None
        title = 'Search'

    elif enrolled is not None:
        courses = user.students.all().order_by('-id')
        title = 'Enrolled Courses'
    else:
        courses = Course.objects.filter(
            active=True, is_trial=False
        ).exclude(
            ~Q(requests=user), ~Q(rejected=user), hidden=True
        ).order_by('-id')
        title = 'All Courses'

    for course in courses:
        if user in course.students.all():
            _percent = course.get_completion_percent(user)
        else:
            _percent = None
        courses_data.append(
            {
                'data': course,
                'completion_percentage': _percent,
            }
        )

    context = {
        'user': user, 'courses': courses_data,
        'title': title, 'msg': msg
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
                request, "yaksh/add_question.html", context
            )

    qform = QuestionForm(instance=question)
    fileform = FileForm()
    uploaded_files = FileUpload.objects.filter(question_id=question.id)
    formsets = []
    for testcase in TestCase.__subclasses__():
        if test_case_type == testcase.__name__.lower():
            formset = inlineformset_factory(
                Question, testcase, extra=1, fields='__all__'
            )
        else:
            formset = inlineformset_factory(
                Question, testcase, extra=0, fields='__all__'
            )
        formsets.append(
            formset(
                instance=question,
                initial=[{'type': test_case_type}]
            )
        )
    context = {'qform': qform, 'fileform': fileform, 'question': question,
               'formsets': formsets, 'uploaded_files': uploaded_files}
    return my_render_to_response(
        request, "yaksh/add_question.html", context
    )


@login_required
@email_verified
def add_quiz(request, quiz_id=None, course_id=None):
    """To add a new quiz in the database.
    Create a new quiz and store it."""

    user = request.user
    context = {}
    permission = None
    # if not is_moderator(user):
    #     raise Http404('You are not allowed to view this course !')
    if quiz_id:
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        # if quiz.creator != user and not course_id:
        #     raise Http404('This quiz does not belong to you')
    else:
        quiz = None
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
        # if not course.is_creator(user) and not course.is_teacher(user):
        #     raise Http404('This quiz does not belong to you')

        # Get team which are related to course
        if quiz.creator != user:

            permission = check_permission(course, quiz, user)

            if permission:
                context["perm_type"] = permission.perm_type
            else:
                raise Http404("Insufficient permissions")

    if request.method == "POST":

        if quiz is None or (
                quiz.creator == user or permission.perm_type == "write"):
            form = QuizForm(request.POST, instance=quiz)
            if form.is_valid():
                if quiz is None:
                    form.instance.creator = user
                form.save()
                if not course_id:
                    return my_redirect("/exam/manage/courses/all_quizzes/")
                else:
                    return my_redirect("/exam/manage/courses/")
        else:
            raise Http404("You don't have write access")

    else:
        form = QuizForm(instance=quiz)
        context["course_id"] = course_id
        context["quiz"] = quiz
    context["form"] = form
    return my_render_to_response(request, 'yaksh/add_quiz.html', context)


@login_required
@email_verified
def add_exercise(request, quiz_id=None, course_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this course !')
    if quiz_id:
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if quiz.creator != user and not course_id:
            raise Http404('This quiz does not belong to you')
    else:
        quiz = None
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This Course does not belong to you')

    context = {}
    if request.method == "POST":
        form = ExerciseForm(request.POST, instance=quiz)
        if form.is_valid():
            if quiz is None:
                form.instance.creator = user
            quiz = form.save(commit=False)
            quiz.is_exercise = True
            quiz.time_between_attempts = 0
            quiz.weightage = 0
            quiz.allow_skip = False
            quiz.attempts_allowed = -1
            quiz.duration = 1000
            quiz.pass_criteria = 0
            quiz.save()

            if not course_id:
                return my_redirect("/exam/manage/courses/all_quizzes/")
            else:
                return my_redirect("/exam/manage/courses/")

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
    if not user.is_authenticated():
        return my_redirect('/exam/login')
    if not is_moderator(user):
        return my_redirect('/exam/')
    courses = Course.objects.filter(Q(creator=user) | Q(teachers=user),
                                    is_trial=False).distinct()
    trial_paper = AnswerPaper.objects.filter(
        user=user, question_paper__quiz__is_trial=True,
        course__is_trial=True
    )
    if request.method == "POST":
        delete_paper = request.POST.getlist('delete_paper')
        for answerpaper_id in delete_paper:
            answerpaper = AnswerPaper.objects.get(id=answerpaper_id)
            qpaper = answerpaper.question_paper
            answerpaper.course.remove_trial_modules()
            answerpaper.course.delete()
            if qpaper.quiz.is_trial:
                qpaper.quiz.delete()
            else:
                if qpaper.answerpaper_set.count() == 1:
                    qpaper.quiz.delete()
                else:
                    answerpaper.delete()

    context = {'user': user, 'courses': courses,
               'trial_paper': trial_paper, 'msg': msg
               }
    return my_render_to_response(
        request, 'yaksh/moderator_dashboard.html', context
    )


def user_login(request):
    """Take the credentials of the user and log the user in."""

    user = request.user
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

    return my_render_to_response(request, 'yaksh/login.html', context)


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
        if is_moderator(user):
            return prof_manage(request, msg=msg)
        return quizlist_user(request, msg=msg)

    # if course is active and is not expired
    if not course.active or not course.is_active_enrollment():
        msg = "{0} is either expired or not active".format(course.name)
        if is_moderator(user):
            return prof_manage(request, msg=msg)
        return quizlist_user(request, msg=msg)

    # is quiz is active and is not expired
    if quest_paper.quiz.is_expired() or not quest_paper.quiz.active:
        msg = "{0} is either expired or not active".format(
            quest_paper.quiz.description)
        if is_moderator(user):
            return prof_manage(request, msg=msg)
        return view_module(request, module_id=module_id, course_id=course_id,
                           msg=msg)

    # prerequisite check and passing criteria for quiz
    if learning_unit.has_prerequisite():
        if not learning_unit.is_prerequisite_complete(
                user, learning_module, course):
            msg = "You have not completed the previous Lesson/Quiz/Exercise"
            if is_moderator(user):
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
    if previous_question:
        delay_time = paper.time_left_on_question(previous_question)
    else:
        delay_time = paper.time_left_on_question(question)

    if previous_question and quiz.is_exercise:
        if (delay_time <= 0 or previous_question in
                paper.questions_answered.all()):
            can_skip = True
        question = previous_question
    if not question:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(
            request, msg, paper.attempt_number, paper.question_paper.id,
            course_id=course_id, module_id=module_id
        )
    if not quiz.active:
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
    if question in paper.questions_answered.all():
        notification = (
            'You have already attempted this question successfully'
            if question.type == "code" else
            'You have already attempted this question'
        )
    if question.type in ['mcc', 'mcq', 'arrange']:
        test_cases = question.get_ordered_test_cases(paper)
    else:
        test_cases = question.get_test_cases()
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

    if request.method == 'POST':
        # Add the answer submitted, regardless of it being correct or not.
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
            assignment_filename = request.FILES.getlist('assignment')
            if not assignment_filename:
                msg = "Please upload assignment file"
                return show_question(
                    request, current_question, paper, notification=msg,
                    course_id=course_id, module_id=module_id,
                    previous_question=current_question
                )
            for fname in assignment_filename:
                fname._name = fname._name.replace(" ", "_")
                assignment_files = AssignmentUpload.objects.filter(
                    assignmentQuestion=current_question, course_id=course_id,
                    assignmentFile__icontains=fname, user=user,
                    question_paper=questionpaper_id)
                if assignment_files.exists():
                    assign_file = assignment_files.first()
                    if os.path.exists(assign_file.assignmentFile.path):
                        os.remove(assign_file.assignmentFile.path)
                    assign_file.delete()
                AssignmentUpload.objects.create(
                    user=user, assignmentQuestion=current_question,
                    course_id=course_id,
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
                return show_question(request, next_q, paper,
                                     course_id=course_id, module_id=module_id,
                                     previous_question=current_question)
        else:
            user_answer = request.POST.get('answer')
        if not user_answer:
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
            user_answer, user) if current_question.type == 'code' or \
            current_question.type == 'upload' else None
        result = paper.validate_answer(
            user_answer, current_question, json_data, uid
        )
        if current_question.type in ['code', 'upload']:
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
        message = (
            reason or "An Unexpected Error occurred."
            " Please contact your instructor/administrator."
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
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            new_course = form.save(commit=False)
            if course_id is None:
                new_course.creator = user
            new_course.save()
            return my_redirect('/exam/manage/courses')
        else:
            return my_render_to_response(
                request, 'yaksh/add_course.html', {'form': form}
            )
    else:
        form = CourseForm(instance=course)
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
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    courses = Course.objects.filter(
        creator=user, is_trial=False).order_by('-active', '-id')
    allotted_courses = Course.objects.filter(
        teachers=user, is_trial=False).order_by('-active', '-id')
    context = {'courses': courses, "allotted_courses": allotted_courses,
               "type": "courses"}
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
def enroll(request, course_id, user_id=None, was_rejected=False):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_active_enrollment():
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
            request, 'yaksh/course_detail.html', {'course': course}
        )
    users = User.objects.filter(id__in=enroll_ids)
    course.enroll(was_rejected, *users)
    return course_detail(request, course_id)


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
    context = {
        'course': course, 'message': message,
        'state': 'mail'
    }
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


@login_required
@email_verified
def reject(request, course_id, user_id=None, was_enrolled=False):
    user = request.user
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
            request, 'yaksh/course_detail.html',
            {'course': course, 'message': message},
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
    if attempt_number is None:
        context = {'quiz': quiz, 'attempts': attempt_numbers,
                   'questionpaper_id': questionpaper_id,
                   'course_id': course_id}
        return my_render_to_response(
            request, 'yaksh/statistics_question.html', context
        )
    total_attempt = AnswerPaper.objects.get_count(questionpaper_id,
                                                  attempt_number,
                                                  course_id)
    if not AnswerPaper.objects.has_attempt(questionpaper_id, attempt_number,
                                           course_id):
        return my_redirect('/exam/manage/')
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
def monitor(request, quiz_id=None, course_id=None):
    """Monitor the progress of the papers taken so far."""

    user = request.user
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
        return my_render_to_response(request, 'yaksh/monitor.html', context)
    # quiz_id is not None.
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id)
        course = get_object_or_404(Course, id=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This course does not belong to you')
        q_paper = QuestionPaper.objects.filter(quiz__is_trial=False,
                                               quiz_id=quiz_id).distinct()
    except (QuestionPaper.DoesNotExist, Course.DoesNotExist):
        papers = []
        q_paper = None
        latest_attempts = []
        attempt_numbers = []
    else:
        if q_paper:
            attempt_numbers = AnswerPaper.objects.get_attempt_numbers(
                q_paper.last().id, course.id)
        else:
            attempt_numbers = []
        latest_attempts = []
        papers = AnswerPaper.objects.filter(question_paper=q_paper,
                                            course_id=course_id).order_by(
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
    csv_fields = CSV_FIELDS
    context = {
        "papers": papers,
        "quiz": quiz,
        "msg": "Quiz Results",
        "latest_attempts": latest_attempts,
        "csv_fields": csv_fields,
        "attempt_numbers": attempt_numbers,
        "course": course
    }
    return my_render_to_response(request, 'yaksh/monitor.html', context)


@csrf_exempt
def ajax_questions_filter(request):
    """Ajax call made when filtering displayed questions."""

    user = request.user
    filter_dict = {"user_id": user.id, "active": True}
    question_type = request.POST.get('question_type')
    marks = request.POST.get('marks')
    language = request.POST.get('language')
    if question_type:
        filter_dict['type'] = str(question_type)

    if marks:
        filter_dict['points'] = marks

    if language:
        filter_dict['language'] = str(language)
    questions = Question.objects.filter(**filter_dict)

    return my_render_to_response(
        request, 'yaksh/ajax_question_filter.html', {'questions': questions}
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


def _get_questions_from_tags(question_tags, user):
    search_tags = []
    for tags in question_tags:
        search_tags.extend(re.split(r'[; |, |\*|\n]', tags))
    return Question.objects.filter(tags__name__in=search_tags,
                                   user=user).distinct()


@login_required
@email_verified
def design_questionpaper(request, quiz_id, questionpaper_id=None,
                         course_id=None):
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
                random_set = QuestionSet(marks=marks,
                                         num_questions=num_of_questions)
                random_set.save()
                random_ques = Question.objects.filter(id__in=question_ids)
                random_set.questions.add(*random_ques)
                question_paper.random_questions.add(random_set)

        if 'remove-random' in request.POST:
            random_set_ids = request.POST.getlist('random_sets', None)
            question_paper.random_questions.remove(*random_set_ids)

        if 'save' in request.POST or 'back' in request.POST:
            qpaper_form.save()
            return my_redirect('/exam/manage/courses/all_quizzes/')

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
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    questions = Question.objects.filter(user_id=user.id, active=True)
    form = QuestionFilterForm(user=user)
    user_tags = questions.values_list('tags', flat=True).distinct()
    all_tags = Tag.objects.filter(id__in=user_tags)
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
                questions = Question.objects.filter(
                    id__in=data, user_id=user.id, active=True)
                for question in questions:
                    question.active = False
                    question.save()

        if request.POST.get('upload') == 'upload':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                questions_file = request.FILES['file']
                file_extension = questions_file.name.split('.')[-1]
                ques = Question()
                if file_extension == "zip":
                    files, extract_path = extract_files(questions_file)
                    context['message'] = ques.read_yaml(extract_path, user,
                                                        files)
                elif file_extension in ["yaml", "yml"]:
                    questions = questions_file.read()
                    context['message'] = ques.load_questions(questions, user)
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
                context['msg'] = ("Please select atleast" +
                                  "one question to download")

        if request.POST.get('test') == 'test':
            question_ids = request.POST.getlist("question")
            if question_ids:
                trial_paper, trial_course, trial_module = test_mode(
                    user, False, question_ids, None)
                trial_paper.update_total_marks()
                trial_paper.save()
                return my_redirect("/exam/start/1/{0}/{1}/{2}".format(
                    trial_module.id, trial_paper.id, trial_course.id))
            else:
                context["msg"] = "Please select atleast one question to test"

        if request.POST.get('question_tags'):
            question_tags = request.POST.getlist("question_tags")
            search_result = _get_questions_from_tags(question_tags, user)
            context['questions'] = search_result

    return my_render_to_response(request, 'yaksh/showquestions.html', context)


@login_required
@email_verified
def user_data(request, user_id, questionpaper_id=None, course_id=None):
    """Render user data."""
    current_user = request.user
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    user = User.objects.get(id=user_id)
    data = AnswerPaper.objects.get_user_data(user, questionpaper_id, course_id)

    context = {'data': data, 'course_id': course_id}
    return my_render_to_response(request, 'yaksh/user_data.html', context)


def _expand_questions(questions, field_list):
    i = field_list.index('questions')
    field_list.remove('questions')
    for question in questions:
        field_list.insert(
            i, '{0}-{1}'.format(question.summary, question.points))
    return field_list


@login_required
@email_verified
def download_quiz_csv(request, course_id, quiz_id):
    current_user = request.user
    if not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    course = get_object_or_404(Course, id=course_id)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if not course.is_creator(current_user) and \
            not course.is_teacher(current_user):
        raise Http404('The quiz does not belong to your course')
    users = course.get_enrolled().order_by('first_name')
    if not users:
        return monitor(request, quiz_id)
    csv_fields = []
    attempt_number = None
    question_paper = quiz.questionpaper_set.last()
    last_attempt_number = AnswerPaper.objects.get_attempt_numbers(
        question_paper.id, course.id).last()
    if request.method == 'POST':
        csv_fields = request.POST.getlist('csv_fields')
        attempt_number = request.POST.get('attempt_number',
                                          last_attempt_number)
    if not csv_fields:
        csv_fields = CSV_FIELDS
    if not attempt_number:
        attempt_number = last_attempt_number

    questions = question_paper.get_question_bank()
    answerpapers = AnswerPaper.objects.filter(
        question_paper=question_paper,
        attempt_number=attempt_number, course_id=course_id)
    if not answerpapers:
        return monitor(request, quiz_id, course_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename="{0}-{1}-attempt{2}.csv"'.format(
            course.name.replace('.', ''), quiz.description.replace('.', ''),
            attempt_number)
    writer = csv.writer(response)
    if 'questions' in csv_fields:
        csv_fields = _expand_questions(questions, csv_fields)
    writer.writerow(csv_fields)

    csv_fields_values = {
        'name': 'user.get_full_name().title()',
        'roll_number': 'user.profile.roll_number',
        'institute': 'user.profile.institute',
        'department': 'user.profile.department',
        'username': 'user.username',
        'marks_obtained': 'answerpaper.marks_obtained',
        'out_of': 'question_paper.total_marks',
        'percentage': 'answerpaper.percent',
        'status': 'answerpaper.status'}
    questions_scores = {}
    for question in questions:
        questions_scores['{0}-{1}'.format(question.summary, question.points)] \
            = 'answerpaper.get_per_question_score({0})'.format(question.id)
    csv_fields_values.update(questions_scores)

    users = users.exclude(id=course.creator.id).exclude(
        id__in=course.teachers.all())
    for user in users:
        row = []
        answerpaper = None
        papers = answerpapers.filter(user=user)
        if papers:
            answerpaper = papers.first()
        for field in csv_fields:
            try:
                row.append(eval(csv_fields_values[field]))
            except AttributeError:
                row.append('-')
        writer.writerow(row)
    return response


@login_required
@email_verified
def grade_user(request, quiz_id=None, user_id=None, attempt_number=None,
               course_id=None):
    """Present an interface with which we can easily grade a user's papers
    and update all their marks and also give comments for each paper.
    """
    current_user = request.user
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
            questionpaper_id, course_id
        )
        quiz = get_object_or_404(Quiz, id=quiz_id)
        course = get_object_or_404(Course, id=course_id)
        if not course.is_creator(current_user) and not \
                course.is_teacher(current_user):
            raise Http404('This course does not belong to you')

        has_quiz_assignments = AssignmentUpload.objects.filter(
            question_paper_id=questionpaper_id
        ).exists()
        context = {
            "users": user_details,
            "quiz_id": quiz_id,
            "quiz": quiz,
            "has_quiz_assignments": has_quiz_assignments,
            "course_id": course_id
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
                question_paper_id=questionpaper_id,
                user_id=user_id
            ).exists()
            user = User.objects.get(id=user_id)
            data = AnswerPaper.objects.get_user_data(
                user, questionpaper_id, course_id, attempt_number
            )
            context = {
                "data": data,
                "quiz_id": quiz_id,
                "users": user_details,
                "attempts": attempts,
                "user_id": user_id,
                "has_user_assignments": has_user_assignments,
                "has_quiz_assignments": has_quiz_assignments,
                "course_id": course_id
            }
    if request.method == "POST":
        papers = data['papers']
        for paper in papers:
            for question, answers in six.iteritems(
                    paper.get_question_answers()):
                marks = float(request.POST.get('q%d_marks' % question.id, 0))
                answer = answers[-1]['answer']
                answer.set_marks(marks)
                answer.save()
            paper.update_marks()
            paper.comments = request.POST.get(
                'comments_%d' % paper.question_paper.id, 'No comments')
            paper.save()

        course_status = CourseStatus.objects.filter(course=course, user=user)
        if course_status.exists():
            course_status.first().set_grade()

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
    return my_render_to_response(request, 'yaksh/addteacher.html', context)


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
    return my_render_to_response(request, 'yaksh/addteacher.html', context)


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
        teachers = User.objects.filter(id__in=teacher_ids)
        course.remove_teachers(*teachers)
    return my_redirect('/exam/manage/courses')


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
            order=1, creator=user, check_prerequisite=False,
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
        return my_redirect('/exam/manage')

    trial_questionpaper, trial_course, trial_module = test_mode(
        current_user, godmode, None, quiz_id, course_id)
    return my_redirect("/exam/start/{0}/{1}/{2}".format(
        trial_questionpaper.id, trial_module.id, trial_course.id))


@login_required
@email_verified
def view_answerpaper(request, questionpaper_id, course_id):
    user = request.user
    quiz = get_object_or_404(QuestionPaper, pk=questionpaper_id).quiz
    course = get_object_or_404(Course, pk=course_id)
    if quiz.view_answerpaper and user in course.students.all():
        data = AnswerPaper.objects.get_user_data(user, questionpaper_id,
                                                 course_id)
        has_user_assignment = AssignmentUpload.objects.filter(
            user=user, course_id=course.id,
            question_paper_id=questionpaper_id
        ).exists()
        context = {'data': data, 'quiz': quiz, 'course_id': course.id,
                   "has_user_assignment": has_user_assignment}
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
def grader(request, extra_context=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    courses = Course.objects.filter(is_trial=False)
    user_courses = list(courses.filter(creator=user)) + \
        list(courses.filter(teachers=user))
    context = {'courses': user_courses}
    if extra_context:
        context.update(extra_context)
    return my_render_to_response(request, 'yaksh/regrade.html', context)


@login_required
@email_verified
def regrade(request, course_id, question_id=None, answerpaper_id=None,
            questionpaper_id=None):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not is_moderator(user) or (course.is_creator(user) and
                                  course.is_teacher(user)):
        raise Http404('You are not allowed to view this page!')
    details = []
    if answerpaper_id is not None and question_id is None:
        answerpaper = get_object_or_404(AnswerPaper, pk=answerpaper_id)
        for question in answerpaper.questions.all():
            details.append(answerpaper.regrade(question.id))
            course_status = CourseStatus.objects.filter(
                user=answerpaper.user, course=answerpaper.course)
            if course_status.exists():
                course_status.first().set_grade()
    if questionpaper_id is not None and question_id is not None:
        answerpapers = AnswerPaper.objects.filter(
            questions=question_id,
            question_paper_id=questionpaper_id, course_id=course_id)
        for answerpaper in answerpapers:
            details.append(answerpaper.regrade(question_id))
            course_status = CourseStatus.objects.filter(
                user=answerpaper.user, course=answerpaper.course)
            if course_status.exists():
                course_status.first().set_grade()
    if answerpaper_id is not None and question_id is not None:
        answerpaper = get_object_or_404(AnswerPaper, pk=answerpaper_id)
        details.append(answerpaper.regrade(question_id))
        course_status = CourseStatus.objects.filter(user=answerpaper.user,
                                                    course=answerpaper.course)
        if course_status.exists():
            course_status.first().set_grade()

    return grader(request, extra_context={'details': details})


@login_required
@email_verified
def download_course_csv(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    course = Course.objects.prefetch_related("learning_module").get(
        id=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('The question paper does not belong to your course')
    students = course.get_only_students().annotate(
        roll_number=F('profile__roll_number'),
        institute=F('profile__institute')
    ).values(
        "id", "first_name", "last_name",
        "email", "institute", "roll_number"
    )
    quizzes = course.get_quizzes()

    for student in students:
        total_course_marks = 0.0
        user_course_marks = 0.0
        for quiz in quizzes:
            quiz_best_marks = AnswerPaper.objects. \
                get_user_best_of_attempts_marks(quiz, student["id"], course_id)
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
        context['email_err_msg'] = "Multiple entries found for this email"\
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
def upload_users(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    context = {'course': course}

    if not (course.is_teacher(user) or course.is_creator(user)):
        msg = 'You do not have permissions to this course.'
        return complete(request, reason=msg)
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            context['message'] = "Please upload a CSV file."
            return my_render_to_response(
                request, 'yaksh/course_detail.html', context
            )
        csv_file = request.FILES['csv_file']
        is_csv_file, dialect = is_csv(csv_file)
        if not is_csv_file:
            context['message'] = "The file uploaded is not a CSV file."
            return my_render_to_response(
                request, 'yaksh/course_detail.html', context
            )
        required_fields = ['firstname', 'lastname', 'email']
        try:
            reader = csv.DictReader(
                csv_file.read().decode('utf-8').splitlines(),
                dialect=dialect)
        except TypeError:
            context['message'] = "Bad CSV file"
            return my_render_to_response(
                request, 'yaksh/course_detail.html', context
            )
        stripped_fieldnames = [
            field.strip().lower() for field in reader.fieldnames]
        for field in required_fields:
            if field not in stripped_fieldnames:
                context['message'] = "The CSV file does not contain the"\
                    " required headers"
                return my_render_to_response(
                    request, 'yaksh/course_detail.html', context
                )
        reader.fieldnames = stripped_fieldnames
        context['upload_details'] = _read_user_csv(reader, course)
    return my_render_to_response(request, 'yaksh/course_detail.html', context)


def _read_user_csv(reader, course):
    fields = reader.fieldnames
    upload_details = ["Upload Summary:"]
    counter = 0
    for row in reader:
        counter += 1
        (username, email, first_name, last_name, password, roll_no, institute,
         department, remove) = _get_csv_values(row, fields)
        if not email or not first_name or not last_name:
            upload_details.append("{0} -- Missing Values".format(counter))
            continue
        users = User.objects.filter(username=username)
        if users.exists():
            user = users[0]
            if remove.strip().lower() == 'true':
                _remove_from_course(user, course)
                upload_details.append("{0} -- {1} -- User rejected".format(
                                      counter, user.username))
            else:
                _add_to_course(user, course)
                upload_details.append(
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
        upload_details.append("{0} -- {1} -- User {2} Successfully".format(
                              counter, user.username, state))
    if counter == 0:
        upload_details.append("No rows in the CSV file")
    return upload_details


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
            'attachment; filename="sample_user_upload"'
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
        course.create_duplicate_course(user)
    else:
        msg = dedent(
            '''\
            You do not have permissions to clone {0} course, please contact
            your instructor/administrator.'''.format(course.name)
        )
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
    response['Content-Disposition'] = (
        'attachment; filename="questions_dump.yaml"'
    )
    return response


@login_required
@email_verified
def edit_lesson(request, lesson_id=None, course_id=None):
    user = request.user
    permission = None
    course = None

    if lesson_id:
        lesson = Lesson.objects.get(id=lesson_id)

    if course_id:
        course = Course.objects.get(id=course_id)
        redirect_url = "/exam/manage/courses/"
    else:
        redirect_url = "/exam/manage/courses/all_lessons/"

    # if not is_moderator(user):
    #     raise Http404('You are not allowed to view this page!')
    # if lesson_id:
    #     lesson = Lesson.objects.get(id=lesson_id)
    #     if not lesson.creator == user and not course_id:
    #         raise Http404('This Lesson does not belong to you')
    # else:
    #     lesson = None
    # if course_id:
    #     course = get_object_or_404(Course, id=course_id)
    #     if not course.is_creator(user) and not course.is_teacher(user):
    #         raise Http404('This Lesson does not belong to you')
    #     redirect_url = "/exam/manage/courses/"
    # else:
    #     redirect_url = "/exam/manage/courses/all_lessons/"

    context = {}

    if lesson and course:
        if lesson.creator != user:

            permission = check_permission(course, lesson, user)

            if permission:
                context["perm_type"] = permission.perm_type
            else:
                raise Http404("Insufficient permissions")

    if request.method == "POST":
        if lesson is None or lesson.creator == user or \
                permission.perm_type == "write":
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
                        lesson_form.instance.creator = user
                    lesson = lesson_form.save()
                    lesson.html_data = get_html_text(lesson.description)
                    lesson.save()
                    if lessonfiles:
                        for les_file in lessonfiles:
                            LessonFile.objects.get_or_create(
                                lesson=lesson, file=les_file
                            )
                    return my_redirect(redirect_url)
                else:
                    context['lesson_form'] = lesson_form
                    context['error'] = lesson_form["video_file"].errors
                    context['lesson_file_form'] = lesson_file_form

            if 'Delete' in request.POST:
                remove_files_id = request.POST.getlist('delete_files')
                if remove_files_id:
                    files = LessonFile.objects.filter(id__in=remove_files_id)
                    for file in files:
                        file.remove()
                return my_redirect(redirect_url)
        else:
            raise Http404("You don't have write access")

    lesson_files = LessonFile.objects.filter(lesson=lesson)
    lesson_files_form = LessonFileForm()
    lesson_form = LessonForm(instance=lesson)
    context['lesson_form'] = lesson_form
    context['lesson_file_form'] = lesson_files_form
    context['lesson_files'] = lesson_files
    context['course_id'] = course_id
    if lesson:
        context['lesson_creator'] = lesson.creator
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

    all_modules = course.get_learning_modules()
    if learn_unit.has_prerequisite():
        if not learn_unit.is_prerequisite_complete(user, learn_module, course):
            msg = "You have not completed previous Lesson/Quiz/Exercise"
            return view_module(request, learn_module.id, course_id, msg=msg)
    context = {'lesson': learn_unit.lesson, 'user': user,
               'course': course, 'state': "lesson", "all_modules": all_modules,
               'learning_units': learning_units, "current_unit": learn_unit,
               'learning_module': learn_module}
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
            add_values = request.POST.get("chosen_list").split(',')
            to_add_list = []
            if add_values:
                ordered_units = learning_module.get_learning_units()
                if ordered_units.exists():
                    start_val = ordered_units.last().order + 1
                else:
                    start_val = 1
                for order, value in enumerate(add_values, start_val):
                    learning_id, type = value.split(":")
                    if type == "quiz":
                        learning_unit = LearningUnit.objects.create(
                            order=order, quiz_id=learning_id,
                            type=type)
                    else:
                        learning_unit = LearningUnit.objects.create(
                            order=order, lesson_id=learning_id,
                            type=type)
                    to_add_list.append(learning_unit)
                learning_module.learning_unit.add(*to_add_list)

        if "Change" in request.POST:
            order_list = request.POST.get("ordered_list").split(",")
            for order in order_list:
                learning_unit, learning_order = order.split(":")
                if learning_order:
                    learning_unit = learning_module.learning_unit.get(
                        id=learning_unit)
                    learning_unit.order = learning_order
                    learning_unit.save()

        if "Remove" in request.POST:
            remove_values = request.POST.getlist("delete_list")
            if remove_values:
                learning_module.learning_unit.remove(*remove_values)
                LearningUnit.objects.filter(id__in=remove_values).delete()

        if "Change_prerequisite" in request.POST:
            unit_list = request.POST.getlist("check_prereq")
            for unit in unit_list:
                learning_unit = learning_module.learning_unit.get(id=unit)
                learning_unit.toggle_check_prerequisite()
                learning_unit.save()

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
    return my_render_to_response(request, 'yaksh/add_module.html', context)


@login_required
@email_verified
def add_module(request, module_id=None, course_id=None):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    redirect_url = "/exam/manage/courses/all_learning_module/"
    if course_id:
        course = Course.objects.get(id=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            raise Http404('This course does not belong to you')
        redirect_url = "/exam/manage/courses/"
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
                    module_form.instance.creator = user
                module = module_form.save()
                module.html_data = get_html_text(module.description)
                module.save()
                return my_redirect(redirect_url)
            else:
                context['module_form'] = module_form

    module_form = LearningModuleForm(instance=module)
    context['module_form'] = module_form
    context['course_id'] = course_id
    context['status'] = "add"
    return my_render_to_response(request, "yaksh/add_module.html", context)


@login_required
@email_verified
def show_all_quizzes(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    quizzes = Quiz.objects.filter(creator=user, is_trial=False)
    context = {"quizzes": quizzes, "type": "quiz"}
    return my_render_to_response(request, 'yaksh/courses.html', context)


@login_required
@email_verified
def show_all_lessons(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    lessons = Lesson.objects.filter(creator=user)
    context = {"lessons": lessons, "type": "lesson"}
    return my_render_to_response(request, 'yaksh/courses.html', context)


@login_required
@email_verified
def show_all_modules(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    learning_modules = LearningModule.objects.filter(
        creator=user, is_trial=False)
    context = {"learning_modules": learning_modules, "type": "learning_module"}
    return my_render_to_response(request, 'yaksh/courses.html', context)


@login_required
@email_verified
def preview_html_text(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    response_kwargs = {}
    response_kwargs['content_type'] = 'application/json'
    request_data = json.loads(request.body.decode("utf-8"))
    html_text = get_html_text(request_data['description'])
    return HttpResponse(json.dumps({"data": html_text}), **response_kwargs)


@login_required
@email_verified
def get_next_unit(request, course_id, module_id, current_unit_id=None,
                  first_unit=None):
    user = request.user
    course = Course.objects.prefetch_related("learning_module").get(
        id=course_id)
    if user not in course.students.all():
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
                    learning_module = LearningModule.objects.get(id=int(value))
                    learning_module.order = order
                    learning_module.save()
                    to_add_list.append(learning_module)
                course.learning_module.add(*to_add_list)

        if "Change" in request.POST:
            order_list = request.POST.get("ordered_list").split(",")
            for order in order_list:
                learning_unit, learning_order = order.split(":")
                if learning_order:
                    learning_module = course.learning_module.get(
                        id=learning_unit)
                    learning_module.order = learning_order
                    learning_module.save()

        if "Remove" in request.POST:
            remove_values = request.POST.getlist("delete_list")
            if remove_values:
                course.learning_module.remove(*remove_values)

        if "change_prerequisite_completion" in request.POST:
            unit_list = request.POST.getlist("check_prereq")
            for unit in unit_list:
                learning_module = course.learning_module.get(id=unit)
                learning_module.toggle_check_prerequisite()
                learning_module.save()

        if "change_prerequisite_passing" in request.POST:
            unit_list = request.POST.getlist("check_prereq_passes")
            for unit in unit_list:
                learning_module = course.learning_module.get(id=unit)
                learning_module.toggle_check_prerequisite_passes()
                learning_module.save()

    added_learning_modules = course.get_learning_modules()
    all_learning_modules = LearningModule.objects.filter(
        creator=user, is_trial=False)

    learning_modules = set(all_learning_modules) - set(added_learning_modules)
    context['added_learning_modules'] = added_learning_modules
    context['learning_modules'] = learning_modules
    context['course_id'] = course_id
    return my_render_to_response(
        request, 'yaksh/design_course_session.html', context
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
    students = course.get_only_students()
    stud_details = [(student, course.get_grade(student),
                     course.get_completion_percent(student),
                     course.get_current_unit(student)) for student in students]
    context = {
        'course': course, 'student_details': stud_details,
        'state': 'course_status'
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
                            "video-js.css", "offline.css"],
                    "images": ["yaksh_banner.png"]}
    zip_file = course.create_zip(current_dir, static_files)
    zip_file.seek(0)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename={0}.zip'.format(
        course_name
    )
    response.write(zip_file.read())
    return response
