import random
import string
import os
import stat
from os.path import dirname, pardir, abspath, join, exists
import datetime
import collections
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
                QuestionForm, RandomQuestionForm,\
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


def gen_key(no_of_chars):
    """Generate a random key of the number of characters."""
    allowed_chars = string.digits+string.uppercase
    return ''.join([random.choice(allowed_chars) for i in range(no_of_chars)])


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


def fetch_questions(request):
    """Fetch questions from database based on the given search conditions &
    tags"""
    set1 = set()
    set2 = set()
    first_tag = request.POST.get('first_tag')
    first_condition = request.POST.get('first_condition')
    second_tag = request.POST.get('second_tag')
    second_condition = request.POST.get('second_condition')
    third_tag = request.POST.get('third_tag')
    question1 = set(Question.objects.filter(tags__name__in=[first_tag]))
    question2 = set(Question.objects.filter(tags__name__in=[second_tag]))
    question3 = set(Question.objects.filter(tags__name__in=[third_tag]))
    if first_condition == 'and':
        set1 = question1.intersection(question2)
        if second_condition == 'and':
            set2 = set1.intersection(question3)
        else:
            set2 = set1.union(question3)
    else:
        set1 = question1.union(question2)
        if second_condition == 'and':
            set2 = set1.intersection(question3)
        else:
            set2 = set1.union(question3)
    return set2


def _update_marks(answer_paper, state='completed'):
    answer_paper.update_marks_obtained()
    answer_paper.update_percent()
    answer_paper.update_passed()
    answer_paper.update_status(state)
    answer_paper.end_time = datetime.datetime.now()
    answer_paper.save()


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
    avail_quizzes = list(QuestionPaper.objects.filter(quiz__active=True))
    user_answerpapers = AnswerPaper.objects.filter(user=user)
    pre_requisites = []
    enabled_quizzes = []
    disabled_quizzes = []
    unexpired_quizzes = []

    courses = Course.objects.filter(active=True)

    for paper in avail_quizzes:
        quiz_enable_time = paper.quiz.start_date_time
        quiz_disable_time = paper.quiz.end_date_time
        if quiz_enable_time <= datetime.datetime.now() <= quiz_disable_time:
            unexpired_quizzes.append(paper)

    cannot_attempt = True if 'cannot_attempt' in request.GET else False
    quizzes_taken = None if user_answerpapers.count() == 0 else user_answerpapers

    context = {'cannot_attempt': cannot_attempt,
                'quizzes': avail_quizzes,
                'user': user,
                'quizzes_taken': quizzes_taken,
                'unexpired_quizzes': unexpired_quizzes,
                'courses': courses
            }

    return my_render_to_response("yaksh/quizzes_user.html", context)

@login_required
def intro(request, questionpaper_id):
    """Show introduction page before quiz starts"""
    user = request.user
    ci = RequestContext(request)
    quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
    if not quest_paper.quiz.course.is_enrolled(user):
        raise Http404('You are not allowed to view this page!')
    attempt_number = quest_paper.quiz.attempts_allowed
    time_lag = quest_paper.quiz.time_between_attempts
    quiz_enable_time = quest_paper.quiz.start_date_time
    quiz_disable_time = quest_paper.quiz.end_date_time

    quiz_expired = False if quiz_enable_time <= datetime.datetime.now() \
                                <= quiz_disable_time else True

    if quest_paper.quiz.prerequisite:
        try:
            pre_quest = QuestionPaper.objects.get(
                    quiz=quest_paper.quiz.prerequisite)
            answer_papers = AnswerPaper.objects.filter(
                    question_paper=pre_quest, user=user)
            answer_papers_failed = AnswerPaper.objects.filter(
                    question_paper=pre_quest, user=user, passed=False)
            if answer_papers.count() == answer_papers_failed.count():
                context = {'user': user, 'cannot_attempt': True}
                return my_redirect("/exam/quizzes/?cannot_attempt=True")
        except:
            context = {'user': user, 'cannot_attempt': True}
            return my_redirect("/exam/quizzes/?cannot_attempt=True")

    attempted_papers = AnswerPaper.objects.filter(question_paper=quest_paper,
            user=user)
    already_attempted = attempted_papers.count()
    inprogress, previous_attempt, next_attempt = _check_previous_attempt(attempted_papers,
                                                                            already_attempted,
                                                                            attempt_number)

    if previous_attempt:
        if inprogress:
            return show_question(request,
                    previous_attempt.current_question(),
                    previous_attempt.attempt_number,
                    previous_attempt.question_paper.id)
        days_after_attempt = (datetime.datetime.today() - \
                previous_attempt.start_time).days

        if next_attempt:
            if days_after_attempt >= time_lag:
                context = {'user': user,
                            'paper_id': questionpaper_id,
                            'attempt_num': already_attempted + 1,
                            'enable_quiz_time': quiz_enable_time,
                            'disable_quiz_time': quiz_disable_time,
                            'quiz_expired': quiz_expired
                        }
                return my_render_to_response('yaksh/intro.html', context,
                                             context_instance=ci)
        else:
            return my_redirect("/exam/quizzes/")

    else:
        context = {'user': user,
                    'paper_id': questionpaper_id,
                    'attempt_num': already_attempted + 1,
                    'enable_quiz_time': quiz_enable_time,
                    'disable_quiz_time': quiz_disable_time,
                    'quiz_expired': quiz_expired
                }
        return my_render_to_response('yaksh/intro.html', context,
                                     context_instance=ci)


def _check_previous_attempt(attempted_papers, already_attempted, attempt_number):
    next_attempt = False if already_attempted == attempt_number else True
    if already_attempted == 0:
        return False, None, next_attempt
    else:
        previous_attempt = attempted_papers[already_attempted-1]
        if previous_attempt.status == 'inprogress':
            if previous_attempt.time_left() > 0:
                return True, previous_attempt, next_attempt
            else:
                return False, previous_attempt, next_attempt
        else:
            return False, previous_attempt, next_attempt

@login_required
def results_user(request):
    """Show list of Results of Quizzes that is taken by logged-in user."""
    user = request.user
    papers = AnswerPaper.objects.filter(user=user)
    quiz_marks = []
    for paper in papers:
        marks_obtained = paper.marks_obtained
        max_marks = paper.question_paper.total_marks
        percentage = round((marks_obtained/max_marks)*100, 2)
        temp = paper.question_paper.quiz.description, marks_obtained,\
               max_marks, percentage
        quiz_marks.append(temp)
    context = {'papers': quiz_marks}
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
    # test = request.POST.getlist('test')
    type = request.POST.getlist('type')
    active = request.POST.getlist('active')
    language = request.POST.getlist('language')
    snippet = request.POST.getlist('snippet')
    for j, question_id in enumerate(question_list):
        question = Question.objects.get(id=question_id)

        question.summary = summary[j]
        question.description = description[j]
        question.points = points[j]
        # question.options = options[j]
        question.active = active[j]
        question.language = language[j]
        # question.snippet = snippet[j]
        # question.ref_code_path = ref_code_path[j]
        # question.test = test[j]
        question.type = type[j]
        question.save()
    return my_redirect("/exam/manage/questions")


@login_required
def add_question(request, question_id=None):
    """To add a new question in the database.
    Create a new question and store it."""
    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            if question_id is None:
                if 'save_question' in request.POST:
                    form.save()
                    question = Question.objects.order_by("-id")[0]
                    tags = form['tags'].data.split(',')
                    for i in range(0, len(tags)-1):
                        tag = tags[i].strip()
                        question.tags.add(tag)

                    return my_redirect("/exam/manage/questions")

                return my_render_to_response('yaksh/add_question.html',
                                             {'form': form},
                                             context_instance=ci)
                
            else:
                d = Question.objects.get(id=question_id)
                if 'save_question' in request.POST:
                    d.summary = form['summary'].data
                    d.description = form['description'].data
                    d.points = form['points'].data
                    # d.options = form['options'].data
                    d.type = form['type'].data
                    d.active = form['active'].data
                    d.language = form['language'].data
                    # d.snippet = form['snippet'].data
                    # d.ref_code_path = form['ref_code_path'].data
                    # d.test = form['test'].data
                    d.save()
                    question = Question.objects.get(id=question_id)
                    for tag in question.tags.all():
                        question.tags.remove(tag)
                    tags = form['tags'].data.split(',')
                    for i in range(0, len(tags)-1):
                        tag = tags[i].strip()
                        question.tags.add(tag)

                    return my_redirect("/exam/manage/questions")

                return my_render_to_response('yaksh/add_question.html',
                                             {'form': form},
                                             context_instance=ci)

        else:
            return my_render_to_response('yaksh/add_question.html',
                                         {'form': form},
                                         context_instance=ci)
    else:
        form = QuestionForm()
        if question_id is None:
            form = QuestionForm()
            return my_render_to_response('yaksh/add_question.html',
                                         {'form': form},
                                         context_instance=ci)
        else:
            d = Question.objects.get(id=question_id)
            form = QuestionForm()
            form.initial['summary'] = d.summary
            form.initial['description'] = d.description
            form.initial['points'] = d.points
            # form.initial['options'] = d.options
            form.initial['type'] = d.type
            form.initial['active'] = d.active
            form.initial['language'] = d.language
            # form.initial['snippet'] = d.snippet
            # form.initial['ref_code_path'] = d.ref_code_path
            # form.initial['test'] = d.test
            form_tags = d.tags.all()
            form_tags_split = form_tags.values('name')
            initial_tags = ""
            for tag in form_tags_split:
                initial_tags = initial_tags + str(tag['name']).strip() + ","
            if (initial_tags == ","):
                initial_tags = ""
            form.initial['tags'] = initial_tags

            return my_render_to_response('yaksh/add_question.html',
                                         {'form': form},
                                         context_instance=ci)

@login_required
def add_testcase(request, question_id=None):
    """To add new test case for a question"""

    ci = RequestContext(request)
    if not question_id:
        raise Http404('No Question Found')
    question = Question.objects.get(id=question_id)
    initial = {'question': question}

    test_case_type = question.test_case_type

    if test_case_type == "standardtestcase":
        from yaksh.forms import StandardTestCaseForm
            if request.method == "POST":
                form = StandardTestCaseForm(request.POST)
            initial = {'question': question}
                form = StandardTestCaseForm(initial)

    if request.method == "POST":
        if form.is_valid():
            form.save()
    else:
        return my_render_to_response('yaksh/add_testcase.html',
                                     {'form': form},
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
def automatic_questionpaper(request, questionpaper_id=None):
    """Generate automatic question paper for a particular quiz"""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if questionpaper_id is None:
        if request.method == "POST":
            if request.POST.get('save') == 'save':
                quiz = Quiz.objects.order_by("-id")[0]
                quest_paper = QuestionPaper()
                questions = request.POST.getlist('questions')
                tot_marks = 0
                for quest in questions:
                    q = Question.objects.get(id=quest)
                    tot_marks += q.points
                quest_paper.quiz = quiz
                quest_paper.total_marks = tot_marks
                quest_paper.save()
                for quest in questions:
                    q = Question.objects.get(id=quest)
                    quest_paper.fixed_questions.add(q)
                return my_redirect('/exam/manage/showquiz')
            else:
                no_questions = int(request.POST.get('num_questions'))
                fetched_questions = fetch_questions(request)
                n = len(fetched_questions)
                msg = ''
                if (no_questions < n):
                    i = n - no_questions
                    for i in range(0, i):
                        fetched_questions.pop()
                elif (no_questions > n):
                    msg = 'The given Criteria does not satisfy the number\
                    of Questions...'
                tags = Tag.objects.all()
                context = {'data': {'questions': fetched_questions,
                                    'tags': tags,
                                    'msg': msg}}
                return my_render_to_response(
                    'yaksh/automatic_questionpaper.html', context,
                    context_instance=ci)
        else:
            tags = Tag.objects.all()
            context = {'data': {'tags': tags}}
            return my_render_to_response('yaksh/automatic_questionpaper.html',
                                         context, context_instance=ci)

    else:
        if request.method == "POST":
            if request.POST.get('save') == 'save':
                quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
                questions = request.POST.getlist('questions')
                tot_marks = quest_paper.total_marks
                for quest in questions:
                    q = Question.objects.get(id=quest)
                    tot_marks += q.points
                quest_paper.total_marks = tot_marks
                quest_paper.save()
                for quest in questions:
                    q = Question.objects.get(id=quest)
                    quest_paper.questions.add(q)
                return my_redirect('/yaksh/manage/showquiz')
            else:
                no_questions = int(request.POST.get('num_questions'))
                fetched_questions = fetch_questions(request)
                n = len(fetched_questions)
                msg = ''
                if(no_questions < n):
                    i = n - no_questions
                    for i in range(0, i):
                        fetched_questions.pop()
                elif(no_questions > n):
                    msg = 'The given Criteria does not satisfy the number of \
                                                                Questions...'
                tags = Tag.objects.all()
                context = {'data': {'questions': fetched_questions,
                                    'tags': tags,
                                    'msg': msg}}
                return my_render_to_response(
                    'yaksh/automatic_questionpaper.html', context,
                    context_instance=ci)
        else:
            tags = Tag.objects.all()
            context = {'data': {'tags': tags}}
            return my_render_to_response('yaksh/automatic_questionpaper.html',
                                         context, context_instance=ci)


@login_required
def manual_questionpaper(request, questionpaper_id=None):
    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if questionpaper_id is None:
        if request.method == "POST":
            if request.POST.get('save') == 'save':
                questions = request.POST.getlist('questions')
                quest_paper = QuestionPaper()
                quiz = Quiz.objects.order_by("-id")[0]
                tot_marks = 0
                for quest in questions:
                    q = Question.objects.get(id=quest)
                    tot_marks += q.points
                quest_paper.quiz = quiz
                quest_paper.total_marks = tot_marks
                quest_paper.save()
                for i in questions:
                    q = Question.objects.get(id=i)
                    quest_paper.questions.add(q)
                return my_redirect('/exam/manage/showquiz')
            else:
                fetched_questions = fetch_questions(request)
                n = len(fetched_questions)
                msg = ''
                if (n == 0):
                    msg = 'No matching Question found...'
                tags = Tag.objects.all()
                context = {'data': {'questions': fetched_questions,
                                    'tags': tags, 'msg': msg}}
                return my_render_to_response('yaksh/manual_questionpaper.html',
                                             context,
                                             context_instance=ci)
        else:
            tags = Tag.objects.all()
            context = {'data': {'tags': tags}}
            return my_render_to_response('yaksh/manual_questionpaper.html',
                                         context, context_instance=ci)

    else:
        if request.method == "POST":
            if request.POST.get('save') == 'save':
                quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
                questions = request.POST.getlist('questions')
                tot_marks = quest_paper.total_marks
                for quest in questions:
                    q = Question.objects.get(id=quest)
                    tot_marks += q.points
                    quest_paper.total_marks = tot_marks
                    quest_paper.save()
                    for i in questions:
                        q = Question.objects.get(id=i)
                        quest_paper.questions.add(q)
                        return my_redirect('/exam/manage/showquiz')
            else:
                fetched_questions = fetch_questions(request)
                n = len(fetched_questions)
                msg = ''
                if (n == 0):
                    msg = 'No matching Question found...'
                tags = Tag.objects.all()
                context = {'data': {'questions': fetched_questions,
                                    'tags': tags, 'msg': msg}}
                return my_render_to_response('yaksh/manual_questionpaper.html',
                                             context,
                                             context_instance=ci)
        else:
            tags = Tag.objects.all()
            context = {'data': {'tags': tags}}
            return my_render_to_response('yaksh/manual_questionpaper.html',
                                         context, context_instance=ci)


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
    if questionpaper_id is None:
        return my_redirect('/exam/quizzes/')
    try:
        """Right now the app is designed so there is only one active quiz
        at a particular time."""
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
        q = old_paper.current_question()
        return show_question(request, q, attempt_num, questionpaper_id)
    except AnswerPaper.DoesNotExist:
        ip = request.META['REMOTE_ADDR']
        key = gen_key(10)
        try:
            profile = user.get_profile()
        except Profile.DoesNotExist:
            msg = 'You do not have a profile and cannot take the quiz!'
            raise Http404(msg)

        new_paper = questionpaper.make_answerpaper(user, ip, attempt_num)
        # Make user directory.
        user_dir = get_user_dir(user)
        return start(request, attempt_num, questionpaper_id)


def get_questions(paper):
    '''
        Takes answerpaper as an argument. Returns the total questions as
        ordered dictionary, the questions yet to attempt and the questions
        attempted
    '''
    to_attempt = []
    submitted = []
    all_questions = []
    questions = {}
    if paper.questions:
        all_questions = (paper.questions).split('|')
    if paper.questions_answered:
        q_answered = (paper.questions_answered).split('|')
        q_answered.sort()
        submitted = q_answered
    if paper.get_unanswered_questions():
        q_unanswered = paper.get_unanswered_questions()
        q_unanswered.sort()
        to_attempt = q_unanswered
    for index, value in enumerate(all_questions, 1):
        questions[value] = index
        questions = collections.OrderedDict(sorted(questions.items(), key=lambda x:x[1]))
    return questions, to_attempt, submitted


@login_required
def question(request, q_id, attempt_num, questionpaper_id, success_msg=None):
    """Check the credentials of the user and start the exam."""

    user = request.user
    if not user.is_authenticated():
        return my_redirect('/exam/login/')
    q = get_object_or_404(Question, pk=q_id)
    try:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(
            user=request.user, attempt_number=attempt_num, question_paper=q_paper)
    except AnswerPaper.DoesNotExist:
        return my_redirect('/exam/start/')
    if not paper.question_paper.quiz.active:
        reason = 'The quiz has been deactivated!'
        return complete(request, reason, attempt_num, questionpaper_id)
    time_left = paper.time_left()
    if time_left == 0:
        return complete(request, attempt_num, questionpaper_id, reason='Your time is up!')
    quiz_name = paper.question_paper.quiz.description
    questions, to_attempt, submitted = get_questions(paper)
    if success_msg is None:
        context = {'question': q, 'questions': questions, 'paper': paper,
                   'user': user, 'quiz_name': quiz_name, 'time_left': time_left,
                   'to_attempt': to_attempt, 'submitted': submitted}
    else:
        context = {'question': q, 'questions': questions, 'paper': paper,
                   'user': user, 'quiz_name': quiz_name, 'time_left': time_left,
                   'success_msg': success_msg, 'to_attempt': to_attempt,
                   'submitted': submitted}
    if q.type == 'code':
        skipped_answer = paper.answers.filter(question=q, skipped=True)
        if skipped_answer:
            context['last_attempt'] = skipped_answer[0].answer
    ci = RequestContext(request)
    return my_render_to_response('yaksh/question.html', context,
                                 context_instance=ci)


@login_required
def show_question(request, q_id, attempt_num, questionpaper_id, success_msg=None):
    """Show a question if possible."""
    user = request.user
    q_paper = QuestionPaper.objects.get(id=questionpaper_id)
    paper = AnswerPaper.objects.get(user=request.user, attempt_number=attempt_num,
            question_paper=q_paper)
    if not user.is_authenticated():
        return my_redirect('/exam/login/')
    if len(q_id) == 0:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(request, msg, attempt_num, questionpaper_id)
    else:
        return question(request, q_id, attempt_num, questionpaper_id, success_msg)


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


def check(request, q_id, attempt_num=None, questionpaper_id=None):
    """Checks the answers of the user for particular question"""
    user = request.user
    q_paper = QuestionPaper.objects.get(id=questionpaper_id)
    paper = get_object_or_404(AnswerPaper, user=request.user, attempt_number=attempt_num,
            question_paper=q_paper)

    if q_id in paper.questions_answered:
        next_q = paper.skip(q_id)
        return show_question(request, next_q, attempt_num, questionpaper_id)

    if not user.is_authenticated():
        return my_redirect('/exam/login/')

    question = get_object_or_404(Question, pk=q_id)
    # test_cases = TestCase.objects.filter(question=question)

    snippet_code = request.POST.get('snippet')
    user_code = request.POST.get('answer')
    skip = request.POST.get('skip', None)
    success_msg = False
    success = True
    if skip is not None:
        if  question.type == 'code':
            old_skipped = paper.answers.filter(question=question, skipped=True)
            _save_skipped_answer(old_skipped, user_code, paper, question)
        next_q = paper.skip(q_id)
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
        json_data = question.consolidate_answer_data(user_answer) \
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

    _update_marks(paper, 'inprogress')
    time_left = paper.time_left()
    if not result.get('success'):  # Should only happen for non-mcq questions.
        if time_left <= 0:
            reason = 'Your time is up!'
            return complete(request, reason, attempt_num, questionpaper_id)
        if not paper.question_paper.quiz.active:
            reason = 'The quiz has been deactivated!'
            return complete(request, reason, attempt_num, questionpaper_id)
        questions, to_attempt, submitted = get_questions(paper)
        old_answer = paper.answers.filter(question=question, skipped=True)
        if old_answer:
            old_answer[0].answer = user_code
            old_answer[0].save()
        context = {'question': question, 'error_message': result.get('error'),
                   'paper': paper, 'last_attempt': user_code,
                   'quiz_name': paper.question_paper.quiz.description,
                   'time_left': time_left, 'questions': questions,
                   'to_attempt': to_attempt, 'submitted': submitted}
        ci = RequestContext(request)

        return my_render_to_response('yaksh/question.html', context,
                                     context_instance=ci)
    else:
        if time_left <= 0:
            reason = 'Your time is up!'
            return complete(request, reason, attempt_num, questionpaper_id)

        # Display the same question if user_answer is None
        elif not user_answer:
            msg = "Please submit a valid option or code"
            time_left = paper.time_left()
            questions, to_attempt, submitted = get_questions(paper)
            context = {'question': question, 'error_message': msg,
                       'paper': paper, 'quiz_name': paper.question_paper.quiz.description,
                       'time_left': time_left, 'questions': questions,
                       'to_attempt': to_attempt, 'submitted': submitted}
            ci = RequestContext(request)

            return my_render_to_response('yaksh/question.html', context,
                                         context_instance=ci)
        else:
            next_q = paper.completed_question(question.id)
            return show_question(request, next_q, attempt_num,
                                 questionpaper_id, success_msg)


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
        elif question.type == 'mcc':
            answers = set(question.test.splitlines())
            if set(user_answer) == answers:
                correct = True
        elif question.type == 'code':
            user_dir = get_user_dir(user)
            json_result = code_server.run_code(question.language, question.test_case_type, json_data, user_dir)
            result = json.loads(json_result)
            if result.get('success'):
                correct = True

    return correct, result

def get_question_labels(request, attempt_num=None, questionpaper_id=None):
    """Get the question number show in template for corresponding
     question id."""
    unattempted_questions = []
    submitted_questions = []
    try:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(
            user=request.user, attempt_number=attempt_num, question_paper=q_paper)
    except AnswerPaper.DoesNotExist:
        return my_redirect('/exam/start/')
    questions, to_attempt, submitted = get_questions(paper)
    for q_id, question_label in questions.items():
        if q_id in to_attempt:
            unattempted_questions.append(question_label)
        else:
            submitted_questions.append(question_label)
    unattempted_questions.sort()
    submitted_questions.sort()
    return unattempted_questions, submitted_questions

def quit(request, attempt_num=None, questionpaper_id=None):
    """Show the quit page when the user logs out."""
    unattempted_questions, submitted_questions = get_question_labels(request,
                                                 attempt_num, questionpaper_id)
    context = {'id': questionpaper_id, 'attempt_num': attempt_num,
                 'unattempted': unattempted_questions,
                 'submitted': submitted_questions}
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
        unattempted_questions, submitted_questions = get_question_labels(request,
                                                     attempt_num, questionpaper_id)
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(user=user, question_paper=q_paper,
                attempt_number=attempt_num)
        _update_marks(paper)
        obt_marks = paper.marks_obtained
        tot_marks = paper.question_paper.total_marks
        if obt_marks == paper.question_paper.total_marks:
            context = {'message': "Hurray ! You did an excellent job.\
                       you answered all the questions correctly.\
                       You have been logged out successfully,\
                       Thank You !",
                       'unattempted': unattempted_questions,
                       'submitted': submitted_questions}
            return my_render_to_response('yaksh/complete.html', context)
        else:
            message = reason or "You are successfully logged out"
            context = {'message':  message,
                         'unattempted': unattempted_questions,
                         'submitted': submitted_questions}
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
        for j in data:
            d = Question.objects.get(id=j)
            form = QuestionForm()
            form.initial['summary'] = d.summary
            form.initial['description'] = d.description
            form.initial['points'] = d.points
            # form.initial['options'] = d.options
            form.initial['type'] = d.type
            form.initial['active'] = d.active
            form.initial['language'] = d.language
            # form.initial['snippet'] = d.snippet
            # form.initial['ref_code_path'] = d.ref_code_path
            # form.initial['test'] = d.test
            form_tags = d.tags.all()
            form_tags_split = form_tags.values('name')
            initial_tags = ""
            for tag in form_tags_split:
                initial_tags = initial_tags + str(tag['name']).strip() + ","
            if (initial_tags == ","):
                initial_tags = ""
            form.initial['tags'] = initial_tags
            forms.append(form)

        return my_render_to_response('yaksh/edit_question.html',
                                     {'data': data},
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
