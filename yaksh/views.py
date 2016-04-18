import random
import string
import os
import stat
from os.path import dirname, pardir, abspath, join, exists
import datetime
import collections
import csv
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import Http404
from django.db.models import Sum, Max
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from taggit.models import Tag
from itertools import chain
import json
# Local imports.
from yaksh.models import Quiz, Question, QuestionPaper, QuestionSet, Course
from yaksh.models import Profile, Answer, AnswerPaper, User, TestCase
from yaksh.forms import UserRegisterForm, UserLoginForm, QuizForm,\
                QuestionForm, RandomQuestionForm, TestCaseFormSet,\
                QuestionFilterForm, CourseForm
from yaksh.xmlrpc_clients import code_server
from settings import URL_ROOT
from yaksh.models import AssignmentUpload
from django.db.models import Q

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
    courses = Course.objects.filter(active=True)

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
def add_question(request, question_id=None):
    """To add a new question in the database.
    Create a new question and store it."""

    def add_or_delete_test_form(post_request, instance):
        request_copy = post_request.copy()
        if 'add_test' in post_request:
            request_copy['test-TOTAL_FORMS'] = int(request_copy['test-TOTAL_FORMS']) + 1
        elif 'delete_test' in post_request:
            request_copy['test-TOTAL_FORMS'] = int(request_copy['test-TOTAL_FORMS']) - 1
        test_case_formset = TestCaseFormSet(request_copy, prefix='test', instance=instance)
        return test_case_formset

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            if question_id is None:
                test_case_formset = add_or_delete_test_form(request.POST, form.save(commit=False))
                if 'save_question' in request.POST:
                    qtn = form.save(commit=False)
                    test_case_formset = TestCaseFormSet(request.POST, prefix='test',  instance=qtn)
                    form.save()
                    question = Question.objects.order_by("-id")[0]
                    if test_case_formset.is_valid():
                        test_case_formset.save()
                    else:
                        return my_render_to_response('yaksh/add_question.html',
                                                     {'form': form,
                                                     'formset': test_case_formset},
                                                     context_instance=ci)

                    return my_redirect("/exam/manage/questions")

                return my_render_to_response('yaksh/add_question.html',
                                             {'form': form,
                                             'formset': test_case_formset},
                                             context_instance=ci)
                
            else:
                d = Question.objects.get(id=question_id)
                form = QuestionForm(request.POST, instance=d)
                test_case_formset = add_or_delete_test_form(request.POST, d)
                if 'save_question' in request.POST:
                    qtn = form.save(commit=False)
                    test_case_formset = TestCaseFormSet(request.POST, prefix='test',  instance=qtn)
                    form.save()
                    question = Question.objects.get(id=question_id)
                    if test_case_formset.is_valid():
                        test_case_formset.save()
                    return my_redirect("/exam/manage/questions")
                return my_render_to_response('yaksh/add_question.html',
                                             {'form': form,
                                             'formset': test_case_formset},
                                             context_instance=ci)

        else:
            test_case_formset = TestCaseFormSet(prefix='test', instance=Question())
            return my_render_to_response('yaksh/add_question.html',
                                         {'form': form,
                                         'formset': test_case_formset},
                                         context_instance=ci)
    else:
        if question_id is None:
            form = QuestionForm()
            test_case_formset = TestCaseFormSet(prefix='test', instance=Question())
            return my_render_to_response('yaksh/add_question.html',
                                         {'form': form,
                                         'formset': test_case_formset},
                                         context_instance=ci)
        else:
            d = Question.objects.get(id=question_id)
            form = QuestionForm(instance=d)
            test_case_formset = TestCaseFormSet(prefix='test', instance=d)

            return my_render_to_response('yaksh/add_question.html',
                                         {'form': form,
                                         'formset': test_case_formset},
                                         context_instance=ci)


@login_required
def add_quiz(request, quiz_id=None):
    """To add a new quiz in the database.
    Create a new quiz and store it."""

    user = request.user
    ci = RequestContext(request)
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

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
                return my_redirect("/exam/manage/")
        return my_render_to_response('yaksh/add_quiz.html',
                             {'form': form},
                             context_instance=ci)
    else:
        if quiz_id is None:
            form = QuizForm(user=user)
        else:
            quiz = Quiz.objects.get(id=quiz_id)
            form = QuizForm(user=user, instance=quiz)
        return my_render_to_response('yaksh/add_quiz.html',
                                     {'form': form},
                                     context_instance=ci)


@login_required
def show_all_questionpapers(request, questionpaper_id=None):
    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if questionpaper_id is None:
        qu_papers = QuestionPaper.objects.all()
        context = {'papers': qu_papers}
        return my_render_to_response('yaksh/showquestionpapers.html', context,
                                     context_instance=ci)
    else:
        qu_papers = QuestionPaper.objects.get(id=questionpaper_id)
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
        question_papers = QuestionPaper.objects.filter(quiz__course__creator=user)
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
    context = {'question': question, 'paper': paper, 'error_message': error_message}
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
        test_cases = TestCase.objects.filter(question=question)
        json_data = question.consolidate_answer_data(test_cases, user_answer) \
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
            if user_answer.strip() == question.test.strip():
                correct = True
                message = 'Correct answer'
        elif question.type == 'mcc':
            answers = set(question.test.splitlines())
            if set(user_answer) == answers:
                correct = True
                message = 'Correct answer'
        elif question.type == 'code':
            user_dir = get_user_dir(user)
            json_result = code_server.run_code(question.language, json_data, user_dir)
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
    course = get_object_or_404(Course, pk=course_id)
    course.request(user)
    return my_redirect('/exam/manage/')


@login_required
def self_enroll(request, course_id):
    user = request.user
    ci = RequestContext(request)
    course = get_object_or_404(Course, pk=course_id)
    if course.is_self_enroll():
        was_rejected = False
        course.enroll(was_rejected, user)
    return my_redirect('/exam/manage/')


@login_required
def courses(request):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    courses = Course.objects.filter(creator=user)
    return my_render_to_response('yaksh/courses.html', {'courses': courses})


@login_required
def course_detail(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    course = get_object_or_404(Course, creator=user, pk=course_id)
    return my_render_to_response('yaksh/course_detail.html', {'course': course})


@login_required
def enroll(request, course_id, user_id, was_rejected=False):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    course = get_object_or_404(Course, creator=user, pk=course_id)
    user = get_object_or_404(User, pk=user_id)
    course.enroll(was_rejected, user)
    return course_detail(request, course_id)


@login_required
def reject(request, course_id, user_id, was_enrolled=False):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    course = get_object_or_404(Course, creator=user, pk=course_id)
    user = get_object_or_404(User, pk=user_id)
    course.reject(was_enrolled, user)
    return course_detail(request, course_id)


@login_required
def toggle_course_status(request, course_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page')
    course = get_object_or_404(Course, creator=user, pk=course_id)
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
        q_paper = QuestionPaper.objects.filter(quiz__course__creator=user)
        context = {'papers': [],
                   'quiz': None,
                   'quizzes': q_paper}
        return my_render_to_response('yaksh/monitor.html', context,
                                     context_instance=ci)
    # quiz_id is not None.
    try:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id,
                                            quiz__course__creator=user)
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


def get_user_data(username, questionpaper_id=None, attempt_number = None):
    """For a given username, this returns a dictionary of important data
    related to the user including all the user's answers submitted.
    """
    user = User.objects.get(username=username)
    papers = AnswerPaper.objects.filter(user=user)
    if questionpaper_id and attempt_number is not None:
        papers = papers.filter(question_paper_id=questionpaper_id, attempt_number = attempt_number).order_by(
                '-attempt_number')
    if attempt_number == None:
        papers = papers.filter(question_paper_id=questionpaper_id).order_by("-attempt_number")

    data = {}
    profile = user.profile if hasattr(user, 'profile') else None
    data['user'] = user
    data['profile'] = profile
    data['papers'] = papers
    data['questionpaperid'] = questionpaper_id
    return data


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

    filter_dict = {}
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
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404("You are not allowed to view this page !")

    if request.method == 'POST' and request.POST.get('delete') == 'delete':
        data = request.POST.getlist('question')
        if data is not None:
            for i in data:
                question = Question.objects.get(id=i).delete()
    questions = Question.objects.all()
    form = QuestionFilterForm()
    context = {'papers': [],
               'question': None,
               'questions': questions,
               'form': form
               }
    return my_render_to_response('yaksh/showquestions.html', context,
                                 context_instance=ci)

@login_required
def user_data(request, username, questionpaper_id=None):
    """Render user data."""
    current_user = request.user
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    data = get_user_data(username, questionpaper_id)

    context = {'data': data}
    return my_render_to_response('yaksh/user_data.html', context,
                                 context_instance=RequestContext(request))


@login_required
def download_csv(request, questionpaper_id):
    user = request.user
    if not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    quiz = Quiz.objects.get(questionpaper=questionpaper_id)
    if quiz.course.creator != user:
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
def grade_user(request, quiz_id = None, user_id=None, attempt_number = None):

    """Present an interface with which we can easily grade a user's papers
    and update all their marks and also give comments for each paper.
    """
    current_user = request.user
    ci = RequestContext(request)
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')

    course_details =Course.objects.filter(creator = current_user)
    context = {"course_details": course_details}

    if quiz_id != None:
        questionpaper_id = QuestionPaper.objects.filter(quiz_id = quiz_id).values("id")

        answerpaper_details = AnswerPaper.objects.filter(question_paper_id = questionpaper_id)
        users_id = answerpaper_details.values_list("user_id").distinct()
        user_details = User.objects.filter(id__in = users_id)
        context = {"users": user_details, "quiz_id": quiz_id}
        if user_id !=None:
            attempts = answerpaper_details.filter(user_id= user_id).order_by("-attempt_number")
            username = User.objects.get(id = user_id)
            if attempt_number is None:
                attempt_number = attempts[0].attempt_number

            data = get_user_data(username.username, questionpaper_id, attempt_number)
            if request.method == "POST":
                papers = data['papers']
                for paper in papers:
                    for question, answers in paper.get_question_answers().iteritems():
                        marks = float(request.POST.get('q%d_marks' % question.id, 0))
                        last_ans = answers[-1]
                        last_ans.marks = marks
                        last_ans.save()
                    paper.comments = request.POST.get(
                        'comments_%d' % paper.question_paper.id, 'No comments')
                    paper.save()

            context = {'data': data,"quiz_id": quiz_id,  "users": user_details,
                            "attempts": attempts,"user_id":user_id
                            }


               
    return my_render_to_response('yaksh/grade_user.html', context, context_instance=ci)



@csrf_exempt
def ajax_questionpaper(request, query):
    """
        During question paper creation, ajax call made to get question details.
    """
    if query == 'marks':
        question_type = request.POST.get('question_type')
        questions = Question.objects.filter(type=question_type)
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
                                            points=marks_selected))
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





















