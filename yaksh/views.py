import random
import string
import os
import stat
from os.path import dirname, pardir, abspath, join, exists
from datetime import datetime
import collections
import csv
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import Http404
from django.db.models import Sum, Max, Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.forms.models import inlineformset_factory
from taggit.models import Tag
from itertools import chain
import json
# Local imports.
from yaksh.models import get_model_class, Quiz, Question, QuestionPaper, QuestionSet, Course
from yaksh.models import Profile, Answer, AnswerPaper, User, TestCase
from yaksh.forms import UserRegisterForm, UserLoginForm, QuizForm,\
                QuestionForm, RandomQuestionForm,\
                QuestionFilterForm, CourseForm, ProfileForm, UploadFileForm,\
                get_object_form
from yaksh.xmlrpc_clients import code_server
from settings import URL_ROOT
from yaksh.models import AssignmentUpload

# The directory where user data can be saved.
OUTPUT_DIR = abspath(join(dirname(__file__), 'output'))


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


def get_user_dir(user):
    """Return the output directory for the user."""

    user_dir = join(OUTPUT_DIR, str(user.username))
    if not exists(user_dir):
        os.mkdir(user_dir)
        # Make it rwx by others.
        os.chmod(user_dir, stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
                 | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                 | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)
    return user_dir


def is_moderator(user):
    """Check if the user is having moderator rights"""
    if user.groups.filter(name='moderator').count() == 1:
        return True

def has_profile(user):
    """ check if user has profile """
    return True if hasattr(user, 'profile') else False

def add_to_group(users):
    """ add users to moderator group """
    group = Group.objects.get(name="moderator")
    for user in users:
        if not is_moderator(user):
            user.groups.add(group)

def index(request):
    """The start page.
    """
    user = request.user
    if user.is_authenticated():
        if user.groups.filter(name='moderator').count() > 0:
            return my_redirect('/exam/manage/')
        return my_redirect("/exam/quizzes/")

    return my_redirect("/exam/login/")


def user_register(request):
    """ Register a new user.
    Create a user and corresponding profile and store roll_number also."""

    user = request.user
    ci = RequestContext(request)
    if user.is_authenticated():
        return my_redirect("/exam/quizzes/")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            u_name, pwd = form.save()
            new_user = authenticate(username=u_name, password=pwd)
            login(request, new_user)
            return my_redirect("/exam/quizzes/")
        else:
            return my_render_to_response('yaksh/register.html', {'form': form},
                                         context_instance=ci)
    else:
        form = UserRegisterForm()
        return my_render_to_response('yaksh/register.html', {'form': form},
                                      context_instance=ci)


@login_required
def quizlist_user(request):
    """Show All Quizzes that is available to logged-in user."""
    user = request.user
    avail_quizzes = Quiz.objects.get_active_quizzes()
    user_answerpapers = AnswerPaper.objects.filter(user=user)
    courses = Course.objects.filter(active=True, is_trial=False)

    context = { 'quizzes': avail_quizzes,
                'user': user,
                'courses': courses,
                'quizzes_taken': user_answerpapers,
            }

    return my_render_to_response("yaksh/quizzes_user.html", context)


@login_required
def results_user(request):
    """Show list of Results of Quizzes that is taken by logged-in user."""
    user = request.user
    papers = AnswerPaper.objects.get_user_answerpapers(user)
    context = {'papers': papers}
    return my_render_to_response("yaksh/results_user.html", context)


@login_required
def add_question(request):
    """To add a new question in the database.
    Create a new question and store it."""
    user = request.user
    ci = RequestContext(request)

    if request.method == "POST" and 'save_question' in request.POST:
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            new_question = question_form.save(commit=False)
            new_question.user = user
            new_question.save()
            return my_redirect("/exam/manage/addquestion/{0}".format(new_question.id))
        else:
            return my_render_to_response('yaksh/add_question.html',
                                         {'form': question_form},
                                         context_instance=ci)
    else:
        question_form = QuestionForm()
        return my_render_to_response('yaksh/add_question.html',
                                     {'form': question_form},
                                     context_instance=ci)

@login_required
def edit_question(request, question_id=None):
    """To add a new question in the database.
    Create a new question and store it."""
    user = request.user
    ci = RequestContext(request)
    if not question_id:
        raise Http404('No Question Found')

    question_instance = Question.objects.get(id=question_id)

    if request.method == "POST" and 'save_question' in request.POST:
        question_form = QuestionForm(request.POST, instance=question_instance)
        if question_form.is_valid():
            new_question = question_form.save(commit=False)
            test_case_type = question_form.cleaned_data.get('test_case_type')
            test_case_form_class = get_object_form(model=test_case_type, exclude_fields=['question'])
            test_case_model_class = get_model_class(test_case_type)
            TestCaseInlineFormSet = inlineformset_factory(Question, test_case_model_class, form=test_case_form_class, extra=1)
            test_case_formset = TestCaseInlineFormSet(request.POST, request.FILES, instance=new_question)
            if test_case_formset.is_valid():
                new_question.save()
                test_case_formset.save()
            return my_redirect("/exam/manage/addquestion/{0}".format(new_question.id))
        else:
            test_case_type = question_form.cleaned_data.get('test_case_type')
            test_case_form_class = get_object_form(model=test_case_type, exclude_fields=['question'])
            test_case_model_class = get_model_class(test_case_type)
            TestCaseInlineFormSet = inlineformset_factory(Question, test_case_model_class, form=test_case_form_class, extra=1)
            test_case_formset = TestCaseInlineFormSet(request.POST, request.FILES, instance=question_instance)
            return my_render_to_response('yaksh/add_question.html',
                                         {'form': question_form,
                                         'test_case_formset': test_case_formset,
                                         'question_id': question_id},
                                         context_instance=ci)
    else:
        question_form = QuestionForm(instance=question_instance)
        test_case_type = question_instance.test_case_type
        test_case_form_class = get_object_form(model=test_case_type, exclude_fields=['question'])
        test_case_model_class = get_model_class(test_case_type)
        TestCaseInlineFormSet = inlineformset_factory(Question, test_case_model_class, form=test_case_form_class, extra=1)
        test_case_formset = TestCaseInlineFormSet(instance=question_instance)

        return my_render_to_response('yaksh/add_question.html',
                                     {'form': question_form,
                                     'test_case_formset': test_case_formset,
                                     'question_id': question_id},
                                     context_instance=ci)

@login_required
def add_quiz(request, quiz_id=None):
    """To add a new quiz in the database.
    Create a new quiz and store it."""

    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    context = {}
    if request.method == "POST":
        if quiz_id is None:
            form = QuizForm(request.POST, user=user)
            if form.is_valid():
                form.save()
                return my_redirect("/exam/manage/designquestionpaper")
        else:
            quiz = Quiz.objects.get(id=quiz_id)
            form = QuizForm(request.POST, user=user, instance=quiz)
            if form.is_valid():
                form.save()
                context["quiz_id"]=quiz_id
                return my_redirect("/exam/manage/")
        
        context["form"] = form
        return my_render_to_response('yaksh/add_quiz.html', context,
                             context_instance=ci)
    else:
        if quiz_id is None:
            form = QuizForm(user=user)
        else:
            quiz = Quiz.objects.get(id=quiz_id)
            form = QuizForm(user=user, instance=quiz)
            context["quiz_id"]=quiz_id
        context["form"] = form
        return my_render_to_response('yaksh/add_quiz.html',
                                     context,
                                     context_instance=ci)


@login_required
def show_all_questionpapers(request, questionpaper_id=None):
    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if questionpaper_id is None:
        qu_papers = QuestionPaper.objects.filter(is_trial=False)
        context = {'papers': qu_papers}
        return my_render_to_response('yaksh/showquestionpapers.html', context,
                                     context_instance=ci)
    else:
        qu_papers = QuestionPaper.objects.get(id=questionpaper_id,is_trial=False)
        quiz = qu_papers.quiz
        fixed_questions = qu_papers.fixed_questions.all()
        random_questions = qu_papers.random_questions.all()
        context = {'quiz': quiz, 'fixed_questions': fixed_questions,
                   'random_questions': random_questions}
        return my_render_to_response('yaksh/editquestionpaper.html', context,
                                     context_instance=ci)


@login_required
def prof_manage(request):
    """Take credentials of the user with professor/moderator
rights/permissions and log in."""
    user = request.user
    if user.is_authenticated() and is_moderator(user):
        question_papers = QuestionPaper.objects.filter(quiz__course__creator=user,
                                                        quiz__is_trial=False
                                                        )
        trial_course = Course.objects.delete_trial_course(user)
        trial_quiz = Quiz.objects.delete_trial_quiz(user)
        users_per_paper = []
        for paper in question_papers:
            answer_papers = AnswerPaper.objects.filter(question_paper=paper)
            users_passed = AnswerPaper.objects.filter(question_paper=paper,
                    passed=True).count()
            users_failed = AnswerPaper.objects.filter(question_paper=paper,
                    passed=False).count()
            temp = paper, answer_papers, users_passed, users_failed
            users_per_paper.append(temp)
        context = {'user': user, 'users_per_paper': users_per_paper}
        return my_render_to_response('manage.html', context)
    return my_redirect('/exam/login/')


def user_login(request):
    """Take the credentials of the user and log the user in."""

    user = request.user
    ci = RequestContext(request)
    if user.is_authenticated():
        if user.groups.filter(name='moderator').count() > 0:
            return my_redirect('/exam/manage/')
        return my_redirect("/exam/quizzes/")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data
            login(request, user)
            if user.groups.filter(name='moderator').count() > 0:
                return my_redirect('/exam/manage/')
            return my_redirect('/exam/login/')
        else:
            context = {"form": form}
            return my_render_to_response('yaksh/login.html', context,
                                         context_instance=ci)
    else:
        form = UserLoginForm()
        context = {"form": form}
        return my_render_to_response('yaksh/login.html', context,
                                     context_instance=ci)



@login_required
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
            'instructor/administrator. Please login again thereafter.'
        return complete(request, msg, attempt_num, questionpaper_id=None)
    if not quest_paper.quiz.course.is_enrolled(user) :
        raise Http404('You are not allowed to view this page!')
    # prerequisite check and passing criteria
    if quest_paper.quiz.has_prerequisite() and  not quest_paper.is_prerequisite_passed(user):
        return quizlist_user(request)
    # if any previous attempt
    last_attempt = AnswerPaper.objects.get_user_last_attempt(
            questionpaper=quest_paper, user=user)
    if last_attempt and last_attempt.is_attempt_inprogress():
        return show_question(request, last_attempt.current_question(), last_attempt)
    # allowed to start
    if not quest_paper.can_attempt_now(user):
        return quizlist_user(request)
    if attempt_num is None:
        attempt_number = 1 if not last_attempt else last_attempt.attempt_number +1
        context = {'user': user, 'questionpaper': quest_paper,
                   'attempt_num': attempt_number}
        return my_render_to_response('yaksh/intro.html', context,
                                     context_instance=ci)
    else:
        ip = request.META['REMOTE_ADDR']
        if not hasattr(user, 'profile'):
            msg = 'You do not have a profile and cannot take the quiz!'
            raise Http404(msg)
        new_paper = quest_paper.make_answerpaper(user, ip, attempt_num)
        # Make user directory.
        user_dir = get_user_dir(user)
        return show_question(request, new_paper.current_question(), new_paper)


@login_required
def show_question(request, question, paper, error_message=None):
    """Show a question if possible."""
    user = request.user
    if not question:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(request, msg, paper.attempt_number, paper.question_paper.id)
    if not paper.question_paper.quiz.active:
        reason = 'The quiz has been deactivated!'
        return complete(request, reason, paper.attempt_number, paper.question_paper.id)
    if paper.time_left() <= 0:
        reason='Your time is up!'
        return complete(request, reason, paper.attempt_number, paper.question_paper.id)
    test_cases = question.get_test_cases()
    context = {'question': question, 'paper': paper, 'error_message': error_message,
                'test_cases': test_cases}
    answers = paper.get_previous_answers(question)
    if answers:
        context['last_attempt'] = answers[0]
    ci = RequestContext(request)
    return my_render_to_response('yaksh/question.html', context,
                                 context_instance=ci)


@login_required
def skip(request, q_id, next_q=None, attempt_num=None, questionpaper_id=None):
    user = request.user
    paper = get_object_or_404(AnswerPaper, user=request.user, attempt_number=attempt_num,
            question_paper=questionpaper_id)
    question = get_object_or_404(Question, pk=q_id)
    if request.method == 'POST' and question.type == 'code':
        user_code = request.POST.get('answer')
        new_answer = Answer(question=question, answer=user_code,
                            correct=False, skipped=True)
        new_answer.save()
        paper.answers.add(new_answer)
    if next_q is None:
        next_q = paper.skip(q_id) if paper.skip(q_id) else question
    else:
        next_q = get_object_or_404(Question, pk=next_q)
    return show_question(request, next_q, paper)


@login_required
def check(request, q_id, attempt_num=None, questionpaper_id=None):
    """Checks the answers of the user for particular question"""
    user = request.user
    paper = get_object_or_404(AnswerPaper, user=request.user, attempt_number=attempt_num,
            question_paper=questionpaper_id)
    question = get_object_or_404(Question, pk=q_id)
    if question in paper.questions_answered.all():
        next_q = paper.skip(q_id)
        return show_question(request, next_q, paper)

    if request.method == 'POST':
        snippet_code = request.POST.get('snippet')
        # Add the answer submitted, regardless of it being correct or not.
        if question.type == 'mcq':
            user_answer = request.POST.get('answer')
        elif question.type == 'mcc':
            user_answer = request.POST.getlist('answer')
        elif question.type == 'upload':
            assign = AssignmentUpload()
            assign.user = user.profile
            assign.assignmentQuestion = question
            # if time-up at upload question then the form is submitted without
            # validation
            if 'assignment' in request.FILES:
                assign.assignmentFile = request.FILES['assignment']
            assign.save()
            user_answer = 'ASSIGNMENT UPLOADED'
            next_q = paper.completed_question(question.id)
            return show_question(request, next_q, paper)
        else:
            user_code = request.POST.get('answer')
            user_answer = snippet_code + "\n" + user_code if snippet_code else user_code
        new_answer = Answer(question=question, answer=user_answer,
                            correct=False)
        new_answer.save()
        paper.answers.add(new_answer)

        # If we were not skipped, we were asked to check.  For any non-mcq
        # questions, we obtain the results via XML-RPC with the code executed
        # safely in a separate process (the code_server.py) running as nobody.
        json_data = question.consolidate_answer_data(user_answer) \
                        if question.type == 'code' else None
        correct, result = validate_answer(user, user_answer, question, json_data)
        if correct:
            new_answer.correct = correct
            new_answer.marks = question.points
            new_answer.error = result.get('error')
        else:
            new_answer.error = result.get('error')
        new_answer.save()
        paper.update_marks('inprogress')
        paper.set_end_time(datetime.now())
        if not result.get('success'):  # Should only happen for non-mcq questions.
            new_answer.answer = user_code
            new_answer.save()
            return show_question(request, question, paper, result.get('error'))
        else:
            # Display the same question if user_answer is None
            if not user_answer:
                msg = "Please submit a valid option or code"
                return show_question(request, question, paper, msg)
            elif question.type == 'code' and user_answer:
                msg = "Correct Output"
                paper.completed_question(question.id)
                return show_question(request, question, paper, msg)
            else:
                next_q = paper.completed_question(question.id)
                return show_question(request, next_q, paper)
    else:
        return show_question(request, question, paper)


def validate_answer(user, user_answer, question, json_data=None):
    """
        Checks whether the answer submitted by the user is right or wrong.
        If right then returns correct = True, success and
        message = Correct answer.
        success is True for MCQ's and multiple correct choices because
        only one attempt are allowed for them.
        For code questions success is True only if the answer is correct.
    """

    result = {'success': True, 'error': 'Incorrect answer'}
    correct = False

    if user_answer is not None:
        if question.type == 'mcq':
            expected_answer = question.get_test_case(correct=True).options
            if user_answer.strip() == expected_answer.strip():
                correct = True
        elif question.type == 'mcc':
            expected_answers = []
            for opt in question.get_test_cases(correct=True):
                expected_answers.append(opt.options)
            if set(user_answer) == set(expected_answers):
                correct = True
        elif question.type == 'code':
            user_dir = get_user_dir(user)
            json_result = code_server.run_code(question.language, question.test_case_type, json_data, user_dir)
            result = json.loads(json_result)
            if result.get('success'):
                correct = True
    return correct, result


def quit(request, reason=None, attempt_num=None, questionpaper_id=None):
    """Show the quit page when the user logs out."""
    paper = AnswerPaper.objects.get(user=request.user,
                                    attempt_number=attempt_num,
                                    question_paper=questionpaper_id)
    context = {'paper': paper, 'message': reason}
    return my_render_to_response('yaksh/quit.html', context,
                                 context_instance=RequestContext(request))


@login_required
def complete(request, reason=None, attempt_num=None, questionpaper_id=None):
    """Show a page to inform user that the quiz has been compeleted."""
    user = request.user
    if questionpaper_id is None:
        logout(request)
        message = reason or "You are successfully logged out."
        context = {'message': message}
        return my_render_to_response('yaksh/complete.html', context)
    else:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(user=user, question_paper=q_paper,
                attempt_number=attempt_num)
        paper.update_marks()
        paper.set_end_time(datetime.now())
        if paper.percent == 100:
            message = "You answered all the questions correctly.\
                       You have been logged out successfully,\
                       Thank You !"
        else:
            message = reason or "You are successfully logged out"
        context = {'message':  message, 'paper': paper}
        return my_render_to_response('yaksh/complete.html', context)


@login_required
def add_course(request):
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            new_course = form.save(commit=False)
            new_course.creator = user
            new_course.save()
            return my_render_to_response('manage.html', {'course': new_course})
        else:
            return my_render_to_response('yaksh/add_course.html',
                                         {'form': form},
                                         context_instance=ci)
    else:
        form = CourseForm()
        return my_render_to_response('yaksh/add_course.html', {'form': form},
                                     context_instance=ci)


@login_required
def enroll_request(request, course_id):
    user = request.user
    ci = RequestContext(request)
    course = get_object_or_404(Course, pk=course_id, is_trial=False)
    course.request(user)
    return my_redirect('/exam/manage/')


@login_required
def self_enroll(request, course_id):
    user = request.user
    ci = RequestContext(request)
    course = get_object_or_404(Course, pk=course_id, is_trial=False)
    if course.is_self_enroll():
        was_rejected = False
        course.enroll(was_rejected, user)
    return my_redirect('/exam/manage/')


@login_required
def courses(request):
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    courses = Course.objects.filter(creator=user, is_trial=False)
    return my_render_to_response('yaksh/courses.html', {'courses': courses},
                                context_instance=ci)


@login_required
def course_detail(request, course_id):
    user = request.user
    ci = RequestContext(request)

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id, is_trial=False)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    return my_render_to_response('yaksh/course_detail.html', {'course': course},
                                context_instance=ci)


@login_required
def enroll(request, course_id, user_id=None, was_rejected=False):
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id, is_trial=False)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    if request.method == 'POST':
        enroll_ids = request.POST.getlist('check')
    else:
        enroll_ids = user_id
    if not enroll_ids:
        return my_render_to_response('yaksh/course_detail.html', {'course': course},
                                            context_instance=ci)
    users = User.objects.filter(id__in=enroll_ids)
    course.enroll(was_rejected, *users)
    return course_detail(request, course_id)


@login_required
def reject(request, course_id, user_id=None, was_enrolled=False):
    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id, is_trial=False)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    if request.method == 'POST':
        reject_ids = request.POST.getlist('check')
    else:
        reject_ids = user_id
    if not reject_ids:
        return my_render_to_response('yaksh/course_detail.html', {'course': course},
                                            context_instance=ci)
    users = User.objects.filter(id__in=reject_ids)
    course.reject(was_enrolled, *users)
    return course_detail(request, course_id)


@login_required
def toggle_course_status(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')

    course = get_object_or_404(Course, pk=course_id, is_trial=False)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    if course.active:
        course.deactivate()
    else:
        course.activate()
    course.save()
    return course_detail(request, course_id)


@login_required
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
def monitor(request, questionpaper_id=None):
    """Monitor the progress of the papers taken so far."""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if questionpaper_id is None:
        q_paper = QuestionPaper.objects.filter(Q(quiz__course__creator=user)
                                                | Q(quiz__course__teachers=user),
                                            quiz__course__is_trial=False
                                            ).distinct()
        context = {'papers': [],
                   'quiz': None,
                   'quizzes': q_paper}
        return my_render_to_response('yaksh/monitor.html', context,
                                     context_instance=ci)
    # quiz_id is not None.
    try:
        q_paper = QuestionPaper.objects.filter(Q(quiz__course__creator=user)|
                                        Q(quiz__course__teachers=user), quiz__course__is_trial=False,
                                        id=questionpaper_id).distinct()
    except QuestionPaper.DoesNotExist:
        papers = []
        q_paper = None
        latest_attempts = []
    else:
        latest_attempts = []
        papers = AnswerPaper.objects.filter(question_paper=q_paper).order_by(
                'user__profile__roll_number')
        users = papers.values_list('user').distinct()
        for auser in users:
            last_attempt = papers.filter(user__in=auser).aggregate(
                    last_attempt_num=Max('attempt_number'))
            latest_attempts.append(papers.get(user__in=auser,
                attempt_number=last_attempt['last_attempt_num']))
    context = {'papers': papers, 'quiz': q_paper, 'quizzes': None,
            'latest_attempts': latest_attempts,}
    return my_render_to_response('yaksh/monitor.html', context,
                                 context_instance=ci)


@login_required
def show_all_users(request):
    """Shows all the users who have taken various exams/quiz."""

    user = request.user
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page !')
    user = User.objects.filter(username__contains="")
    questionpaper = AnswerPaper.objects.all()
    context = {'question': questionpaper}
    return my_render_to_response('yaksh/showusers.html', context,
                                 context_instance=RequestContext(request))


@csrf_exempt
def ajax_questions_filter(request):
    """Ajax call made when filtering displayed questions."""

    user = request.user
    filter_dict = {"user_id": user.id}
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

    return my_render_to_response('yaksh/ajax_question_filter.html',
                                  {'questions': questions})


@login_required
def show_all_questions(request):
    """Show a list of all the questions currently in the databse."""

    user = request.user
    ci = RequestContext(request)
    context = {}
    if not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    if request.method == 'POST':
        if request.POST.get('delete') == 'delete':
            data = request.POST.getlist('question')
            if data is not None:
                question = Question.objects.filter(id__in=data, user_id=user.id).delete()

        if request.POST.get('upload') == 'upload':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                questions_file = request.FILES['file']
                if questions_file.name.split('.')[-1] == "json":
                    questions_list = questions_file.read()
                    question = Question()
                    question.load_from_json(questions_list, user)
                else:
                    message = "Please Upload a JSON file"
                    context['message'] = message

        if request.POST.get('download') == 'download':
            question_ids = request.POST.getlist('question')
            if question_ids:
                question = Question()
                questions = question.dump_into_json(question_ids, user)
                response = HttpResponse(questions, content_type='text/json')
                response['Content-Disposition'] = 'attachment; filename=\
                                            "{0}_questions.json"'.format(user)
                return response
            else:
                msg = "Please select atleast one question"
                context['msg'] = msg
        if request.POST.get('test') == 'test':
            question_ids = request.POST.getlist("question")
            trial_paper = test_mode(user, "test_questions", question_ids, None)
            trial_paper.update_total_marks()
            trial_paper.save()
            return my_redirect("/exam/start/{0}".format(trial_paper.id))


    questions = Question.objects.filter(user_id=user.id)
    form = QuestionFilterForm(user=user)
    upload_form = UploadFileForm()
    context['papers'] = []
    context['question'] = None
    context['questions'] = questions
    context['form'] = form
    context['upload_form'] = upload_form
    return my_render_to_response('yaksh/showquestions.html', context,
                                 context_instance=ci)


@login_required
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
def download_csv(request, questionpaper_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    quiz = Quiz.objects.get(questionpaper=questionpaper_id,is_trial=False)

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
def grade_user(request, quiz_id=None, user_id=None, attempt_number=None):
    """Present an interface with which we can easily grade a user's papers
    and update all their marks and also give comments for each paper.
    """
    current_user = request.user
    ci = RequestContext(request)
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    course_details = Course.objects.filter(Q(creator=current_user)|
                                            Q(teachers=current_user), is_trial=False).distinct()
    context = {"course_details": course_details}
    if quiz_id is not None:
        questionpaper_id = QuestionPaper.objects.filter(quiz_id=quiz_id)\
                                                        .values("id")
        user_details = AnswerPaper.objects.get_users_for_questionpaper\
                                            (questionpaper_id)
        context = {"users": user_details, "quiz_id": quiz_id}
        if user_id is not None:

            attempts = AnswerPaper.objects.get_user_all_attempts\
                                            (questionpaper_id, user_id)
            try:
                if attempt_number is None:
                    attempt_number = attempts[0].attempt_number
            except IndexError:
                raise Http404('No attempts for paper')

            user = User.objects.get(id=user_id)
            data = AnswerPaper.objects.get_user_data(user, questionpaper_id,
                                                     attempt_number
                                                     )

            context = {'data': data, "quiz_id": quiz_id, "users": user_details,
                    "attempts": attempts, "user_id": user_id
                    }
    if request.method == "POST":
        papers = data['papers']
        for paper in papers:
            for question, answers in paper.get_question_answers().iteritems():
                marks = float(request.POST.get('q%d_marks' % question.id, 0))
                answers = answers[-1]
                answers.set_marks(marks)
                answers.save()
            paper.update_marks()
            paper.comments = request.POST.get(
                'comments_%d' % paper.question_paper.id, 'No comments')
            paper.save()


    return my_render_to_response('yaksh/grade_user.html',
                                context, context_instance=ci
                                )


@csrf_exempt
def ajax_questionpaper(request, query):
    """
        During question paper creation, ajax call made to get question details.
    """

    user = request.user
    if query == 'marks':
        question_type = request.POST.get('question_type')
        questions = Question.objects.filter(type=question_type, user=user)
        marks = questions.values_list('points').distinct()
        return my_render_to_response('yaksh/ajax_marks.html', {'marks': marks})
    elif query == 'questions':
        question_type = request.POST['question_type']
        marks_selected = request.POST['marks']
        fixed_questions = request.POST.getlist('fixed_list[]')
        fixed_question_list = ",".join(fixed_questions).split(',')
        random_questions = request.POST.getlist('random_list[]')
        random_question_list = ",".join(random_questions).split(',')
        question_list = fixed_question_list + random_question_list
        questions = list(Question.objects.filter(type=question_type,
                                            points=marks_selected, user=user))
        questions = [question for question in questions \
                if not str(question.id) in question_list]
        return my_render_to_response('yaksh/ajax_questions.html',
                              {'questions': questions})


@login_required
def design_questionpaper(request):
    user = request.user
    ci = RequestContext(request)

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if request.method == 'POST':
        fixed_questions = request.POST.getlist('fixed')
        random_questions = request.POST.getlist('random')
        random_number = request.POST.getlist('number')
        is_shuffle = request.POST.get('shuffle_questions', False)
        if is_shuffle == 'on':
            is_shuffle = True

        question_paper = QuestionPaper(shuffle_questions=is_shuffle)
        quiz = Quiz.objects.order_by("-id")[0]
        tot_marks = 0
        question_paper.quiz = quiz
        question_paper.total_marks = tot_marks
        question_paper.save()
        if fixed_questions:
            fixed_questions_ids = ",".join(fixed_questions)
            fixed_questions_ids_list = fixed_questions_ids.split(',')
            for question_id in fixed_questions_ids_list:
                question_paper.fixed_questions.add(question_id)
        if random_questions:
            for random_question, num in zip(random_questions, random_number):
                qid = random_question.split(',')[0]
                question = Question.objects.get(id=int(qid))
                marks = question.points
                question_set = QuestionSet(marks=marks, num_questions=num)
                question_set.save()
                for question_id in random_question.split(','):
                    question_set.questions.add(question_id)
                    question_paper.random_questions.add(question_set)
        question_paper.update_total_marks()
        question_paper.save()
        return my_redirect('/exam/manage/courses')
    else:
        form = RandomQuestionForm()
        context = {'form': form, 'questionpaper':True}
        return my_render_to_response('yaksh/design_questionpaper.html',
                                     context, context_instance=ci)

@login_required
def view_profile(request):
    """ view moderators and users profile """
    user = request.user
    ci = RequestContext(request)

    context = {}
    if has_profile(user):
        return my_render_to_response('yaksh/view_profile.html', {'user':user})
    else:
        form = ProfileForm(user=user)
        msg = True
        context['form'] = form
        context['msg'] = msg
        return my_render_to_response('yaksh/editprofile.html', context,
                                    context_instance=ci)


@login_required
def edit_profile(request):
    """ edit profile details facility for moderator and students """

    context = {}
    user = request.user
    ci = RequestContext(request)

    if has_profile(user):
        profile = Profile.objects.get(user_id=user.id)
    else:
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
            return my_render_to_response('yaksh/profile_updated.html',
                                        context_instance=ci)
        else:
            context['form'] = form
            return my_render_to_response('yaksh/editprofile.html', context,
                                        context_instance=ci)
    else:
        form = ProfileForm(user=user, instance=profile)
        context['form'] = form
        return my_render_to_response('yaksh/editprofile.html', context,
                                    context_instance=ci)


@login_required
def search_teacher(request, course_id):
    """ search teachers for the course """
    user = request.user
    ci = RequestContext(request)

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    context = {}
    course = get_object_or_404(Course, creator=user, pk=course_id, is_trial=False)
    context['course'] = course

    if request.method == 'POST':
        u_name = request.POST.get('uname')
        if len(u_name) == 0:
            return my_render_to_response('yaksh/addteacher.html', context,
                                        context_instance=ci)
        else:
            teachers = User.objects.filter(Q(username__icontains=u_name)|
                Q(first_name__icontains=u_name)|Q(last_name__icontains=u_name)|
                Q(email__icontains=u_name)).exclude(Q(id=user.id)|Q(is_superuser=1))
            context['success'] = True
            context['teachers'] = teachers
            return my_render_to_response('yaksh/addteacher.html', context,
                                        context_instance=ci)
    else:
        return my_render_to_response('yaksh/addteacher.html', context,
                                    context_instance=ci)


@login_required
def add_teacher(request, course_id):
    """ add teachers to the course """

    user = request.user
    ci = RequestContext(request)

    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    context = {}
    course = get_object_or_404(Course, creator=user, pk=course_id, is_trial=False)
    context['course'] = course

    if request.method == 'POST':
        teacher_ids = request.POST.getlist('check')
        teachers = User.objects.filter(id__in=teacher_ids)
        add_to_group(teachers)
        course.add_teachers(*teachers)
        context['status'] = True
        context['teachers_added'] = teachers
        return my_render_to_response('yaksh/addteacher.html', context,
                                    context_instance=ci)
    else:
        return my_render_to_response('yaksh/addteacher.html', context,
                                    context_instance=ci)


@login_required
def allotted_courses(request):
    """  show courses allotted to a user """

    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    courses = Course.objects.filter(teachers=user, is_trial=False)
    return my_render_to_response('yaksh/courses.html', {'courses': courses},
                                        context_instance=ci)


@login_required
def remove_teachers(request, course_id):
    """  remove user from a course """

    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    course = get_object_or_404(Course, creator=user, pk=course_id, is_trial=False)
    if request.method == "POST":
        teacher_ids = request.POST.getlist('remove')
        teachers = User.objects.filter(id__in=teacher_ids)
        course.remove_teachers(*teachers)
    return my_redirect('/exam/manage/courses')

def test_mode(user, mode, questions_list=None, quiz_id=None): 
    if questions_list is not None and mode == "test_questions":
        trial_course = Course.objects.create_trial_course(user)
        trial_quiz = Quiz.objects.create_trial_quiz(trial_course,user)
        trial_questionpaper = QuestionPaper.objects.add_details_trial_questionpaper(trial_quiz,
                                                    None, questions_list
                                                    )
    else:
        trial_quiz = Quiz.objects.copy_original_quiz(quiz_id, user, mode)
        trial_questionpaper = QuestionPaper.objects.add_details_trial_questionpaper(trial_quiz,
                                                    quiz_id, None
                                                    )
    return trial_questionpaper

@login_required
def test_quiz(request, mode,quiz_id):
    current_user = request.user
    trial_questionpaper = test_mode(current_user, mode, None, quiz_id)
    return my_redirect("/exam/start/{0}".format(trial_questionpaper.id))