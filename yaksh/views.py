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
        return my_redirect("/exam/start/")

    return my_redirect("/exam/login/")


def user_register(request):
    """ Register a new user.
    Create a user and corresponding profile and store roll_number also."""

    user = request.user
    ci = RequestContext(request)
    if user.is_authenticated():
        return my_redirect("/exam/start/")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            u_name, pwd = form.save()
            new_user = authenticate(username=u_name, password=pwd)
            login(request, new_user)
            return my_redirect("/exam/start/")
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
def intro(request, questionpaper_id=None):
    """Show introduction page before quiz starts"""
    user = request.user
    ci = RequestContext(request)
    if questionpaper_id is None:
        return my_redirect('/exam/quizzes/')
    quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
    if not quest_paper.quiz.course.is_enrolled(user) :
        raise Http404('You are not allowed to view this page!')
    attempt_number = quest_paper.quiz.attempts_allowed
    if quest_paper.quiz.has_prerequisite():
        pre_quest = QuestionPaper.objects.get(quiz=quest_paper.quiz.prerequisite)
        if not pre_quest.is_questionpaper_passed(user):
            return quizlist_user(request)

    last_attempt = AnswerPaper.objects.get_user_last_attempt(
            questionpaper=quest_paper, user=user)
    if last_attempt and last_attempt.is_attempt_inprogress():
        return show_question(request, last_attempt.current_question().id,
                             last_attempt.attempt_number,
                             last_attempt.question_paper.id)

    attempt_number = 1 if not last_attempt else last_attempt.attempt_number +1
    if quest_paper.is_attempt_allowed(user) and quest_paper.can_attempt_now(user):
        context = {'user': user, 'questionpaper': quest_paper,
                   'attempt_num': attempt_number}
        return my_render_to_response('yaksh/intro.html', context,
                                     context_instance=ci)
    return my_redirect("/exam/quizzes/")


@login_required
def results_user(request):
    """Show list of Results of Quizzes that is taken by logged-in user."""
    user = request.user
    papers = AnswerPaper.objects.get_user_answerpapers(user)
    context = {'papers': papers}
    return my_render_to_response("yaksh/results_user.html", context)


@login_required
def edit_quiz(request):
    """Edit the list of quizzes seleted by the user for editing."""

    user = request.user
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    quiz_list = request.POST.getlist('quizzes')
    start_date = request.POST.getlist('start_date')
    start_time = request.POST.getlist('start_time')
    end_date = request.POST.getlist('end_date')
    end_time = request.POST.getlist('end_time')
    duration = request.POST.getlist('duration')
    active = request.POST.getlist('active')
    description = request.POST.getlist('description')
    pass_criteria = request.POST.getlist('pass_criteria')
    language = request.POST.getlist('language')
    prerequisite = request.POST.getlist('prerequisite')

    for j, quiz_id in enumerate(quiz_list):
        quiz = Quiz.objects.get(id=quiz_id)
        quiz.start_date_time = datetime.datetime.combine(start_date[j],
                                                    start_time[j])
        quiz.end_date_time = datetime.datetime.combine(end_date[j],
                                                    end_time[j])
        quiz.duration = duration[j]
        quiz.active = active[j]
        quiz.description = description[j]
        quiz.pass_criteria = pass_criteria[j]
        quiz.language = language[j]
        quiz.prerequisite_id = prerequisite[j]
        quiz.save()
    return my_redirect("/exam/manage/showquiz/")


@login_required
def edit_question(request):
    """Edit the list of questions selected by the user for editing."""
    user = request.user
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    question_list = request.POST.getlist('questions')
    summary = request.POST.getlist('summary')
    description = request.POST.getlist('description')
    points = request.POST.getlist('points')
    options = request.POST.getlist('options')
    test = request.POST.getlist('test')
    type = request.POST.getlist('type')
    active = request.POST.getlist('active')
    language = request.POST.getlist('language')
    snippet = request.POST.getlist('snippet')
    for j, question_id in enumerate(question_list):
        question = Question.objects.get(id=question_id)
        test_case_formset = TestCaseFormSet(request.POST, prefix='test', instance=question)
        if test_case_formset.is_valid():
            test_case_instance = test_case_formset.save(commit=False)
            for i in test_case_instance:
                i.save()

        question.summary = summary[j]
        question.description = description[j]
        question.points = points[j]
        question.options = options[j]
        question.active = active[j]
        question.language = language[j]
        question.snippet = snippet[j]
        question.ref_code_path = ref_code_path[j]
        question.test = test[j]
        question.type = type[j]
        question.save()
    return my_redirect("/exam/manage/questions")


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
                    tags = form['tags'].data.split(',')
                    for i in range(0, len(tags)-1):
                        tag = tags[i].strip()
                        question.tags.add(tag)
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
                test_case_formset = add_or_delete_test_form(request.POST, d)
                if 'save_question' in request.POST:
                    d.summary = form['summary'].data
                    d.description = form['description'].data
                    d.points = form['points'].data
                    d.options = form['options'].data
                    d.type = form['type'].data
                    d.active = form['active'].data
                    d.language = form['language'].data
                    d.snippet = form['snippet'].data
                    d.ref_code_path = form['ref_code_path'].data
                    d.test = form['test'].data
                    d.save()
                    question = Question.objects.get(id=question_id)
                    for tag in question.tags.all():
                        question.tags.remove(tag)
                    tags = form['tags'].data.split(',')
                    for i in range(0, len(tags)-1):
                        tag = tags[i].strip()
                        question.tags.add(tag)

                    test_case_formset = TestCaseFormSet(request.POST, prefix='test', instance=question)
                    if test_case_formset.is_valid():
                        test_case_instance = test_case_formset.save(commit=False)
                        for i in test_case_instance:
                            i.save()
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
            test_case_formset = add_or_delete_test_form(request.POST, form.save(commit=False))
            return my_render_to_response('yaksh/add_question.html',
                                         {'form': form,
                                         'formset': test_case_formset},
                                         context_instance=ci)
    else:
        form = QuestionForm()
        test_case_formset = TestCaseFormSet(prefix='test', instance=Question())
        if question_id is None:
            form = QuestionForm()
            test_case_formset = TestCaseFormSet(prefix='test', instance=Question())
            return my_render_to_response('yaksh/add_question.html',
                                         {'form': form,
                                         'formset': test_case_formset},
                                         context_instance=ci)
        else:
            d = Question.objects.get(id=question_id)
            form = QuestionForm()
            form.initial['summary'] = d.summary
            form.initial['description'] = d.description
            form.initial['points'] = d.points
            form.initial['options'] = d.options
            form.initial['type'] = d.type
            form.initial['active'] = d.active
            form.initial['language'] = d.language
            form.initial['snippet'] = d.snippet
            form.initial['ref_code_path'] = d.ref_code_path
            form.initial['test'] = d.test
            form_tags = d.tags.all()
            form_tags_split = form_tags.values('name')
            initial_tags = ""
            for tag in form_tags_split:
                initial_tags = initial_tags + str(tag['name']).strip() + ","
            if (initial_tags == ","):
                initial_tags = ""
            form.initial['tags'] = initial_tags

            test_case_formset = TestCaseFormSet(prefix='test', 
                                                    instance=d)

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
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    if request.method == "POST":
        form = QuizForm(request.POST, user=user)
        if form.is_valid():
            data = form.cleaned_data
            if quiz_id is None:
                form.save()
                quiz = Quiz.objects.order_by("-id")[0]
                return my_redirect("/exam/manage/designquestionpaper")
            else:
                d = Quiz.objects.get(id=quiz_id)
                sd = datetime.datetime.strptime(form['start_date'].data, '%Y-%m-%d').date()
                st = datetime.datetime.strptime(form['start_time'].data, "%H:%M:%S").time()
                ed = datetime.datetime.strptime(form['end_date'].data, '%Y-%m-%d').date()
                et = datetime.datetime.strptime(form['end_time'].data, "%H:%M:%S").time()
                d.start_date_time = datetime.datetime.combine(sd, st)
                d.end_date_time = datetime.datetime.combine(ed, et)
                d.duration = form['duration'].data
                d.active = form['active'].data
                d.description = form['description'].data
                d.pass_criteria = form['pass_criteria'].data
                d.language = form['language'].data
                d.prerequisite_id = form['prerequisite'].data
                d.attempts_allowed = form['attempts_allowed'].data
                d.time_between_attempts = form['time_between_attempts'].data
                d.save()
                quiz = Quiz.objects.get(id=quiz_id)
                return my_redirect("/exam/manage/showquiz")
        else:
            return my_render_to_response('yaksh/add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)
    else:
        if quiz_id is None:
            form = QuizForm(user=user)
            return my_render_to_response('yaksh/add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)
        else:
            d = Quiz.objects.get(id=quiz_id)
            form = QuizForm(user=user)
            form.initial['start_date'] = d.start_date_time.date()
            form.initial['start_time'] = d.start_date_time.time()
            form.initial['end_date'] = d.end_date_time.date()
            form.initial['end_time'] = d.end_date_time.time()
            form.initial['duration'] = d.duration
            form.initial['description'] = d.description
            form.initial['active'] = d.active
            form.initial['pass_criteria'] = d.pass_criteria
            form.initial['language'] = d.language
            form.initial['prerequisite'] = d.prerequisite_id
            form.initial['attempts_allowed'] = d.attempts_allowed
            form.initial['time_between_attempts'] = d.time_between_attempts
            return my_render_to_response('yaksh/add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)


@login_required
def show_all_questionpapers(request, questionpaper_id=None):
    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if request.method == "POST" and request.POST.get('add') == "add":
        return my_redirect("/exam/manage/designquestionpaper/" +
                           questionpaper_id)

    if request.method == "POST" and request.POST.get('delete') == "delete":
        data = request.POST.getlist('papers')
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        for i in data:
            q_paper.questions.remove(Question.objects.get(id=i))
        question_paper = QuestionPaper.objects.all()
        context = {'papers': question_paper}
        return my_render_to_response('yaksh/showquestionpapers.html', context,
                                     context_instance=ci)
    if questionpaper_id is None:
        qu_papers = QuestionPaper.objects.all()
        context = {'papers': qu_papers}
        return my_render_to_response('yaksh/showquestionpapers.html', context,
                                     context_instance=ci)
    else:
        qu_papers = QuestionPaper.objects.get(id=questionpaper_id)
        quiz = qu_papers.quiz
        questions = qu_papers.questions.all()
        context = {'papers': {'quiz': quiz, 'questions': questions}}
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
        return my_redirect("/exam/intro/")

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
def start(request, attempt_num=None, questionpaper_id=None):
    """Check the user cedentials and if any quiz is available,
    start the exam."""
    user = request.user
    if questionpaper_id is None or attempt_num is None:
        return my_redirect('/exam/quizzes/')
    try:
        questionpaper = QuestionPaper.objects.get(id=questionpaper_id)
    except QuestionPaper.DoesNotExist:
        msg = 'Quiz not found, please contact your '\
            'instructor/administrator. Please login again thereafter.'
        return complete(request, msg, attempt_num, questionpaper_id)

    if not questionpaper.quiz.course.is_enrolled(user):
        raise Http404('You are not allowed to view this page!')

    try:
        old_paper = AnswerPaper.objects.get(
            question_paper=questionpaper, user=user, attempt_number=attempt_num)
        q = old_paper.current_question().id
        return show_question(request, q, attempt_num, questionpaper_id)
    except AnswerPaper.DoesNotExist:
        ip = request.META['REMOTE_ADDR']
        try:
            profile = user.get_profile()
        except Profile.DoesNotExist:
            msg = 'You do not have a profile and cannot take the quiz!'
            raise Http404(msg)

        new_paper = questionpaper.make_answerpaper(user, ip, attempt_num)
        # Make user directory.
        user_dir = get_user_dir(user)
        return show_question(request, new_paper.current_question().id, attempt_num, questionpaper_id)


@login_required
def show_question(request, q_id, attempt_num, questionpaper_id, success_msg=None):
    """Show a question if possible."""
    user = request.user
    try:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(
            user=request.user, attempt_number=attempt_num, question_paper=q_paper)
    except AnswerPaper.DoesNotExist:
        return my_redirect('/exam/start/')
    if not q_id:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(request, msg, attempt_num, questionpaper_id)
    else:
        q = get_object_or_404(Question, pk=q_id)
        if not paper.question_paper.quiz.active:
            reason = 'The quiz has been deactivated!'
            return complete(request, reason, attempt_num, questionpaper_id)
        time_left = paper.time_left()
        if time_left == 0:
            reason='Your time is up!'
            return complete(request, reason, attempt_num, questionpaper_id)
        context = {'question': q, 'paper': paper}
        if q.type == 'code':
            skipped_answer = paper.answers.filter(question=q, skipped=True)
            if skipped_answer:
                context['last_attempt'] = skipped_answer[0].answer
        ci = RequestContext(request)
        return my_render_to_response('yaksh/question.html', context,
                                     context_instance=ci)


def _save_skipped_answer(old_skipped, user_answer, paper, question):
    """
        Saves the answer on skip. Only the code questions are saved.
        Snippet is not saved with the answer.
    """
    if old_skipped:
        skipped_answer = old_skipped[0]
        skipped_answer.answer=user_answer
        skipped_answer.save()
    else:
        skipped_answer = Answer(question=question, answer=user_answer,
            correct=False, skipped=True)
        skipped_answer.save()
        paper.answers.add(skipped_answer)

@login_required
def check(request, q_id, attempt_num=None, questionpaper_id=None):
    """Checks the answers of the user for particular question"""
    user = request.user
    q_paper = QuestionPaper.objects.get(id=questionpaper_id)
    paper = get_object_or_404(AnswerPaper, user=request.user, attempt_number=attempt_num,
            question_paper=q_paper)

    if q_id in paper.questions_answered.all():
        next_q = paper.skip(q_id).id
        return show_question(request, next_q, attempt_num, questionpaper_id)

    question = get_object_or_404(Question, pk=q_id)
    test_cases = TestCase.objects.filter(question=question)

    snippet_code = request.POST.get('snippet')
    user_code = request.POST.get('answer')
    skip = request.POST.get('skip', None)
    success_msg = False
    success = True
    if skip is not None:
        if  question.type == 'code':
            old_skipped = paper.answers.filter(question=question, skipped=True)
            _save_skipped_answer(old_skipped, user_code, paper, question)
        next_q = paper.skip(q_id).id if paper.skip(q_id) else q_id
        return show_question(request, next_q, attempt_num, questionpaper_id)

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
    if not question.type == 'upload':
        json_data = question.consolidate_answer_data(test_cases, user_answer) \
                        if question.type == 'code' else None
        correct, result = validate_answer(user, user_answer, question, json_data)
        if correct:
            new_answer.correct = correct
            new_answer.marks = question.points
            new_answer.error = result.get('error')
            success_msg = True
        else:
            new_answer.error = result.get('error')
        new_answer.save()

    paper.update_marks('inprogress')
    if paper.time_left() <= 0:
        reason = 'Your time is up!'
        return complete(request, reason, attempt_num, questionpaper_id)
    if not paper.question_paper.quiz.active:
        reason = 'The quiz has been deactivated!'
        return complete(request, reason, attempt_num, questionpaper_id)
    if not result.get('success'):  # Should only happen for non-mcq questions.
        old_answer = paper.answers.filter(question=question, skipped=True)
        if old_answer:
            old_answer[0].answer = user_code
            old_answer[0].save()
        context = {'question': question, 'error_message': result.get('error'),
                   'paper': paper}
        ci = RequestContext(request)

        return my_render_to_response('yaksh/question.html', context,
                                     context_instance=ci)
    else:
        # Display the same question if user_answer is None
        if not user_answer:
            msg = "Please submit a valid option or code"
        elif question.type == 'code' and user_answer:
            msg = "Correct Output"
            success = "True"
            paper.completed_question(question.id)
            context = {'question': question, 'paper': paper, 
                   'error_message': msg, 'success': success}
            ci = RequestContext(request)

            context = {'question': question, 'error_message': msg,
                       'paper': paper}
            ci = RequestContext(request)
            return my_render_to_response('yaksh/question.html', context,
                                         context_instance=ci)
        else:
            next_q = paper.completed_question(question.id)
            if next_q:
                next_q = next_q.id
            return show_question(request, next_q, attempt_num,
                                 questionpaper_id, success_msg)

        return my_render_to_response('yaksh/question.html', context,
                                         context_instance=ci)

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
            context = {'message': "Hurray ! You did an excellent job.\
                       you answered all the questions correctly.\
                       You have been logged out successfully,\
                       Thank You !",
                       'paper': paper}
            return my_render_to_response('yaksh/complete.html', context)
        else:
            message = reason or "You are successfully logged out"
            context = {'message':  message, 'paper': paper}
            return my_render_to_response('yaksh/complete.html', context)
    no = False
    message = reason or 'The quiz has been completed. Thank you.'
    if user.groups.filter(name='moderator').count() > 0:
        message = 'You are successfully Logged out.'
    if request.method == 'POST' and 'no' in request.POST:
        no = True
    if not no:
        # Logout the user and quit with the message given.
        answer_paper = AnswerPaper.objects.get(id=answerpaper_id)
        answer_paper.end_time = datetime.datetime.now()
        answer_paper.save()
        return my_redirect('/exam/quizzes/')
    else:
        return my_redirect('/exam/')


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


def get_user_data(username, questionpaper_id=None):
    """For a given username, this returns a dictionary of important data
    related to the user including all the user's answers submitted.
    """
    user = User.objects.get(username=username)
    papers = AnswerPaper.objects.filter(user=user)
    if questionpaper_id is not None:
        papers = papers.filter(question_paper_id=questionpaper_id).order_by(
                '-attempt_number')

    data = {}
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        # Admin user may have a paper by accident but no profile.
        profile = None
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


@login_required
def show_all_quiz(request):
    """Generates a list of all the quizzes
    that are currently in the database."""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page !')

    if request.method == 'POST' and request.POST.get('delete') == 'delete':
        data = request.POST.getlist('quiz')

        if data is None:
            quizzes = Quiz.objects.all()
            context = {'papers': [],
                       'quiz': None,
                       'quizzes': quizzes}
            return my_render_to_response('yaksh/show_quiz.html', context,
                                         context_instance=ci)
        else:
            for i in data:
                quiz = Quiz.objects.get(id=i).delete()
            quizzes = Quiz.objects.all()
            context = {'papers': [],
                       'quiz': None,
                       'quizzes': quizzes}
            return my_render_to_response('yaksh/show_quiz.html', context,
                                         context_instance=ci)

    elif request.method == 'POST' and request.POST.get('edit') == 'edit':
        data = request.POST.getlist('quiz')
        forms = []
        for j in data:
            d = Quiz.objects.get(id=j)
            form = QuizForm(user=user)
            form.initial['start_date'] = d.start_date_time.date()
            form.initial['start_time'] = d.start_date_time.time()
            form.initial['end_date'] = d.end_date_time.date()
            form.initial['end_time'] = d.end_date_time.time()
            form.initial['duration'] = d.duration
            form.initial['active'] = d.active
            form.initial['description'] = d.description
            form.initial['pass_criteria'] = d.pass_criteria
            form.initial['language'] = d.language
            form.initial['prerequisite'] = d.prerequisite_id
            forms.append(form)
        return my_render_to_response('yaksh/edit_quiz.html',
                                     {'forms': forms, 'data': data},
                                     context_instance=ci)
    else:
        quizzes = Quiz.objects.all()
        context = {'papers': [],
                   'quiz': None,
                   'quizzes': quizzes}
        return my_render_to_response('yaksh/show_quiz.html', context,
                                     context_instance=ci)


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
        if data is None:
            questions = Question.objects.all()
            form = QuestionFilterForm()
            context = {'papers': [],
                       'question': None,
                       'questions': questions,
                       'form': form
                       }
            return my_render_to_response('yaksh/showquestions.html', context,
                                         context_instance=ci)
        else:
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
    elif request.method == 'POST' and request.POST.get('edit') == 'edit':
        data = request.POST.getlist('question')

        forms = []
        formsets = []
        for j in data:
            d = Question.objects.get(id=j)
            form = QuestionForm()
            form.initial['summary'] = d.summary
            form.initial['description'] = d.description
            form.initial['points'] = d.points
            form.initial['options'] = d.options
            form.initial['type'] = d.type
            form.initial['active'] = d.active
            form.initial['language'] = d.language
            form.initial['snippet'] = d.snippet
            form.initial['ref_code_path'] = d.ref_code_path
            form.initial['test'] = d.test
            form_tags = d.tags.all()
            form_tags_split = form_tags.values('name')
            initial_tags = ""
            for tag in form_tags_split:
                initial_tags = initial_tags + str(tag['name']).strip() + ","
            if (initial_tags == ","):
                initial_tags = ""
            form.initial['tags'] = initial_tags
            forms.append(form)
            test_case_formset = TestCaseFormSet(prefix='test', instance=d)
            formsets.append(test_case_formset)
            data_list = zip(forms, formsets)

        return my_render_to_response('yaksh/edit_question.html',
                                     {'data': data,
                                     'data_list': data_list},
                                     context_instance=ci)
    else:
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
                paper.questions, paper.questions_answered,
                paper.status
        ]
        writer.writerow(row)
    return response


@login_required
def grade_user(request, username, questionpaper_id=None):
    """Present an interface with which we can easily grade a user's papers
    and update all their marks and also give comments for each paper.
    """
    current_user = request.user
    ci = RequestContext(request)
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')
    data = get_user_data(username, questionpaper_id)
    if request.method == 'POST':
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

        context = {'data': data}
        return my_render_to_response('yaksh/user_data.html', context,
                                     context_instance=ci)
    else:
        context = {'data': data}
        return my_render_to_response('yaksh/grade_user.html', context,
                                     context_instance=ci)


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

    if not user.is_authenticated() or not is_moderator(user):
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
        return my_redirect('/exam/manage/showquiz')
    else:
        form = RandomQuestionForm()
        context = {'form': form}
        return my_render_to_response('yaksh/design_questionpaper.html',
                                     context, context_instance=ci)
