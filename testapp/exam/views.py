import random
import string
import os
import stat
from os.path import dirname, pardir, abspath, join, exists
import datetime

from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import Http404
from django.db.models import Sum
from taggit.models import Tag
from itertools import chain
# Local imports.
from exam.models import Quiz, Question, QuestionPaper
from exam.models import Profile, Answer, AnswerPaper, User
from exam.forms import UserRegisterForm, UserLoginForm, QuizForm, QuestionForm
from exam.xmlrpc_clients import code_server
from settings import URL_ROOT

# The directory where user data can be saved.
OUTPUT_DIR = abspath(join(dirname(__file__), pardir, 'output'))


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
            return my_render_to_response('exam/register.html', {'form': form},
                                         context_instance=ci)
    else:
        form = UserRegisterForm()
        return my_render_to_response('exam/register.html', {'form': form},
                                      context_instance=ci)


def quizlist_user(request):                                                    
    """Show All Quizzes that is available to logged-in user."""                
    user = request.user                                                        
    avail_quizzes = list(QuestionPaper.objects.filter(quiz__active=True))      
    user_answerpapers = AnswerPaper.objects.filter(user=user)                  
    quizzes_taken = []                                                         
    pre_requisites = []
    context = {}                                       
                                          

    if 'cannot_attempt' in request.GET:
        context['cannot_attempt'] = True
                                                                               
    if user_answerpapers.count() == 0:                                         
        context['quizzes'] = avail_quizzes
        context['user'] = user                      
        context['quizzes_taken'] = None
        return my_render_to_response("exam/quizzes_user.html", context)        
                                                                               
    for answer_paper in user_answerpapers:                                     
        for quiz in avail_quizzes:                                             
            if answer_paper.question_paper.id == quiz.id and \
                answer_paper.end_time != answer_paper.start_time:          
                avail_quizzes.remove(quiz)
                quizzes_taken.append(answer_paper)                             
                                                                               
    context['quizzes'] = avail_quizzes
    context['user'] = user
    context['quizzes_taken'] = quizzes_taken
    return my_render_to_response("exam/quizzes_user.html", context)


def intro(request, questionpaper_id):
    """Show introduction page before quiz starts"""
    user = request.user
    ci = RequestContext(request)
    quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
    if quest_paper.quiz.prerequisite:
        try:
            answer_paper = AnswerPaper.objects.get(
                           quest_paper.quiz.id=quest_paper.quiz.prerequisite.id,
                           user=user)
            if answer_paper.passed:
                context = {'user': user, 'paper_id': questionpaper_id}
                return my_render_to_response('exam/intro.html', context,
                                             context_instance=ci)
            else:
                context = {'user': user, 'cannot_attempt':True}
                return my_redirect("/exam/quizzes/?cannot_attempt=True")
                
        except:
            context = {'user': user, 'cannot_attempt':True}
            return my_redirect("/exam/quizzes/?cannot_attempt=True")
    context = {'user': user, 'paper_id': questionpaper_id}
    ci = RequestContext(request)
    return my_render_to_response('exam/intro.html', context,
                                 context_instance=ci)


def results_user(request):
    """Show list of Results of Quizzes that is taken by logged-in user."""
    user = request.user
    papers = AnswerPaper.objects.filter(user=user)
    quiz_marks = []
    for paper in papers:
        marks_obtained = paper.update_marks_obtained()
        max_marks = paper.question_paper.total_marks
        percentage = round((marks_obtained/max_marks)*100, 2)
        temp = paper.question_paper.quiz.description, marks_obtained,\
               max_marks, percentage
        quiz_marks.append(temp)
    context = {'papers': quiz_marks}
    return my_render_to_response("exam/results_user.html", context)


def edit_quiz(request):
    """Edit the list of quizzes seleted by the user for editing."""

    user = request.user
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    quiz_list = request.POST.getlist('quizzes')
    start_date = request.POST.getlist('start_date')
    duration = request.POST.getlist('duration')
    active = request.POST.getlist('active')
    description = request.POST.getlist('description')
    pass_criteria = request.POST.getlist('pass_criteria')
    language = request.POST.getlist('language')
    prerequisite = request.POST.getlist('prerequisite')

    for j, quiz_id in enumerate(quiz_list):
        quiz = Quiz.objects.get(id=quiz_id)
        quiz.start_date = start_date[j]
        quiz.duration = duration[j]
        quiz.active = active[j]
        quiz.description = description[j]
        quiz.pass_criteria = pass_criteria[j]
        quiz.language = language[j]
        quiz.prerequisite_id = prerequisite[j]
        quiz.save()
    return my_redirect("/exam/manage/showquiz/")


def edit_question(request):
    """Edit the list of questions seleted by the user for editing."""
    user = request.user
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    question_list = request.POST.getlist('questions')
    summary = request.POST.getlist('summary')
    description = request.POST.getlist('description')
    points = request.POST.getlist('points')
    test = request.POST.getlist('test')
    options = request.POST.getlist('options')
    type = request.POST.getlist('type')
    active = request.POST.getlist('active')
    snippet = request.POST.getlist('snippet')
    for j, question_id in enumerate(question_list):
        question = Question.objects.get(id=question_id)
        question.summary = summary[j]
        question.description = description[j]
        question.points = points[j]
        question.test = test[j]
        question.options = options[j]
        question.active = active[j]
        question.snippet = snippet[j]
        question.type = type[j]
        question.save()
    return my_redirect("/exam/manage/questions")


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
            data = form.cleaned_data
            if question_id is None:
                form.save()
                question = Question.objects.order_by("-id")[0]
                tags = form['tags'].data.split(',')
                for i in range(0, len(tags)-1):
                    tag = tags[i].strip()
                    question.tags.add(tag)
                return my_redirect("/exam/manage/questions")
            else:
                d = Question.objects.get(id=question_id)
                d.summary = form['summary'].data
                d.description = form['description'].data
                d.points = form['points'].data
                d.test = form['test'].data
                d.options = form['options'].data
                d.type = form['type'].data
                d.active = form['active'].data
                d.snippet = form['snippet'].data
                d.save()
                question = Question.objects.get(id=question_id)
                for tag in question.tags.all():
                    question.tags.remove(tag)
                tags = form['tags'].data.split(',')
                for i in range(0, len(tags)-1):
                    tag = tags[i].strip()
                    question.tags.add(tag)
                return my_redirect("/exam/manage/questions")
        else:
            return my_render_to_response('exam/add_question.html',
                                         {'form': form},
                                         context_instance=ci)
    else:
        if question_id is None:
            form = QuestionForm()
            return my_render_to_response('exam/add_question.html',
                                         {'form': form},
                                         context_instance=ci)
        else:
            d = Question.objects.get(id=question_id)
            form = QuestionForm()
            form.initial['summary'] = d.summary
            form.initial['description'] = d.description
            form.initial['points'] = d.points
            form.initial['test'] = d.test
            form.initial['options'] = d.options
            form.initial['type'] = d.type
            form.initial['active'] = d.active
            form.initial['snippet'] = d.snippet
            form_tags = d.tags.all()
            form_tags_split = form_tags.values('name')
            initial_tags = ""
            for tag in form_tags_split:
                initial_tags = initial_tags + str(tag['name']).strip() + ","
            if (initial_tags == ","):
                initial_tags = ""
            form.initial['tags'] = initial_tags
            return my_render_to_response('exam/add_question.html',
                                         {'form': form},
                                         context_instance=ci)


def add_quiz(request, quiz_id=None):
    """To add a new quiz in the database.
    Create a new quiz and store it."""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if quiz_id is None:
                form.save()
                quiz = Quiz.objects.order_by("-id")[0]
                return my_redirect("/exam/manage/designquestionpaper")
            else:
                d = Quiz.objects.get(id=quiz_id)
                d.start_date = form['start_date'].data
                d.duration = form['duration'].data
                d.active = form['active'].data
                d.description = form['description'].data
                d.pass_criteria = form['pass_criteria'].data
                d.language = form['language'].data
                d.prerequisite_id = form['prerequisite'].data
                d.save()
                quiz = Quiz.objects.get(id=quiz_id)
                return my_redirect("/exam/manage/showquiz")
        else:
            return my_render_to_response('exam/add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)
    else:
        if quiz_id is None:
            form = QuizForm()
            return my_render_to_response('exam/add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)
        else:
            d = Quiz.objects.get(id=quiz_id)
            form = QuizForm()
            form.initial['start_date'] = d.start_date
            form.initial['duration'] = d.duration
            form.initial['description'] = d.description
            form.initial['active'] = d.active
            form.initial['pass_criteria'] = d.pass_criteria
            form.initial['language'] = d.language
            form.initial['prerequisite'] =  d.prerequisite_id
            return my_render_to_response('exam/add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)


def design_questionpaper(request, questionpaper_id=None):
    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')
    return my_render_to_response('exam/add_questionpaper.html', {},
                                 context_instance=ci)


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
        return my_render_to_response('exam/showquestionpapers.html', context,
                                     context_instance=ci)
    if questionpaper_id is None:
        qu_papers = QuestionPaper.objects.all()
        context = {'papers': qu_papers}
        return my_render_to_response('exam/showquestionpapers.html', context,
                                     context_instance=ci)
    else:
        qu_papers = QuestionPaper.objects.get(id=questionpaper_id)
        quiz = qu_papers.quiz
        questions = qu_papers.questions.all()
        context = {'papers': {'quiz': quiz, 'questions': questions}}
        return my_render_to_response('exam/editquestionpaper.html', context,
                                     context_instance=ci)


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
                    'exam/automatic_questionpaper.html', context,
                    context_instance=ci)
        else:
            tags = Tag.objects.all()
            context = {'data': {'tags': tags}}
            return my_render_to_response('exam/automatic_questionpaper.html',
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
                return my_redirect('/exam/manage/showquiz')
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
                    'exam/automatic_questionpaper.html', context,
                    context_instance=ci)
        else:
            tags = Tag.objects.all()
            context = {'data': {'tags': tags}}
            return my_render_to_response('exam/automatic_questionpaper.html',
                                         context, context_instance=ci)


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
                return my_render_to_response('exam/manual_questionpaper.html',
                                             context,
                                             context_instance=ci)
        else:
            tags = Tag.objects.all()
            context = {'data': {'tags': tags}}
            return my_render_to_response('exam/manual_questionpaper.html',
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
                return my_render_to_response('exam/manual_questionpaper.html',
                                             context,
                                             context_instance=ci)
        else:
            tags = Tag.objects.all()
            context = {'data': {'tags': tags}}
            return my_render_to_response('exam/manual_questionpaper.html',
                                         context, context_instance=ci)


def prof_manage(request):
    """Take credentials of the user with professor/moderator
    rights/permissions and log in."""
    user = request.user
    if user.is_authenticated()\
            and user.groups.filter(name='moderator').count() > 0:
        context = {'user': user}
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
            return my_render_to_response('exam/login.html', context,
                                         context_instance=ci)
    else:
        form = UserLoginForm()
        context = {"form": form}
        return my_render_to_response('exam/login.html', context,
                                     context_instance=ci)


def start(request, questionpaper_id=None):
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
        return complete(request, msg, questionpaper_id)

    try:
        old_paper = AnswerPaper.objects.get(
            question_paper=questionpaper, user=user)
        q = old_paper.current_question()
        return show_question(request, q, questionpaper_id)
    except AnswerPaper.DoesNotExist:
        ip = request.META['REMOTE_ADDR']
        key = gen_key(10)
        try:
            profile = user.get_profile()
        except Profile.DoesNotExist:
            msg = 'You do not have a profile and cannot take the quiz!'
            raise Http404(msg)

        new_paper = questionpaper.make_answerpaper(user, ip,)
        # Make user directory.
        user_dir = get_user_dir(user)
        return start(request, questionpaper_id)


def question(request, q_id, questionpaper_id, success_msg=None):
    """Check the credentials of the user and start the exam."""

    user = request.user
    if not user.is_authenticated():
        return my_redirect('/exam/login/')
    q = get_object_or_404(Question, pk=q_id)
    try:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(
            user=request.user, question_paper=q_paper)
    except AnswerPaper.DoesNotExist:
        return my_redirect('/exam/start/')
    if not paper.question_paper.quiz.active:
        reason = 'The quiz has been deactivated!'
        return complete(request, reason, questionpaper_id)
    time_left = paper.time_left()
    if time_left == 0:
        return complete(request, reason='Your time is up!')
    quiz_name = paper.question_paper.quiz.description
    if success_msg is None:
        context = {'question': q, 'paper': paper, 'user': user,
                   'quiz_name': quiz_name,
                   'time_left': time_left, }
    else:
        context = {'question': q, 'paper': paper, 'user': user,
                   'quiz_name': quiz_name,
                   'time_left': time_left,
                   'success_msg': success_msg}
    ci = RequestContext(request)
    return my_render_to_response('exam/question.html', context,
                                 context_instance=ci)


def show_question(request, q_id, questionpaper_id, success_msg=None):
    """Show a question if possible."""
    if len(q_id) == 0:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(request, msg, questionpaper_id)
    else:
        return question(request, q_id, questionpaper_id, success_msg)


def check(request, q_id, questionpaper_id=None):
    """Checks the answers of the user for particular question"""

    user = request.user
    if not user.is_authenticated():
        return my_redirect('/exam/login/')
    question = get_object_or_404(Question, pk=q_id)
    q_paper = QuestionPaper.objects.get(id=questionpaper_id)
    paper = AnswerPaper.objects.get(user=request.user, question_paper=q_paper)
    snippet_code = request.POST.get('snippet')
    skip = request.POST.get('skip', None)
    success_msg = False
    success = True
    if skip is not None:
        next_q = paper.skip()
        return show_question(request, next_q, questionpaper_id)

    # Add the answer submitted, regardless of it being correct or not.
    if question.type == 'mcq':
        user_answer = request.POST.get('answer')
    elif question.type == 'mcc':
        user_answer = request.POST.getlist('answer')
    else:
        user_code = request.POST.get('answer')
        user_answer = snippet_code + "\n" + user_code

    new_answer = Answer(question=question, answer=user_answer,
                        correct=False)
    new_answer.save()
    paper.answers.add(new_answer)

    # If we were not skipped, we were asked to check.  For any non-mcq
    # questions, we obtain the results via XML-RPC with the code executed
    # safely in a separate process (the code_server.py) running as nobody.
    correct, success, err_msg = validate_answer(user, user_answer, question)
    if correct:
        new_answer.correct = correct
        new_answer.marks = question.points
        new_answer.error = err_msg
        success_msg = True
    else:
        new_answer.error = err_msg
    new_answer.save()

    time_left = paper.time_left()
    if not success:  # Should only happen for non-mcq questions.
        if time_left == 0:
            reason = 'Your time is up!'
            return complete(request, reason, questionpaper_id)
        if not paper.question_paper.quiz.active:
            reason = 'The quiz has been deactivated!'
            return complete(request, reason, questionpaper_id)
        context = {'question': question, 'error_message': err_msg,
                   'paper': paper, 'last_attempt': user_code,
                   'quiz_name': paper.question_paper.quiz.description,
                   'time_left': time_left}
        ci = RequestContext(request)

        return my_render_to_response('exam/question.html', context,
                                     context_instance=ci)
    else:
        if time_left <= 0:
            reason = 'Your time is up!'
            return complete(request, reason, questionpaper_id)
        else:
            next_q = paper.completed_question(question.id)
            return show_question(request, next_q,
                                 questionpaper_id, success_msg)


def validate_answer(user, user_answer, question):
    """
        Checks whether the answer submitted by the user is right or wrong.
        If right then returns correct = True, success and
        message = Correct answer.
        success is True for MCQ's and multiple correct choices because
        only one attempt are allowed for them.
        For code questions success is True only if the answer is correct.
    """
    success = True
    correct = False
    message = 'Incorrect answer'

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
            success, message = code_server.run_code(user_answer, question.test,
                                                user_dir, question.language)
            if success:
                 correct = True
    return correct, success, message


def quit(request, questionpaper_id=None):
    """Show the quit page when the user logs out."""
    context = {'id': questionpaper_id}
    return my_render_to_response('exam/quit.html', context,
                                 context_instance=RequestContext(request))


def complete(request, reason=None, questionpaper_id=None):
    """Show a page to inform user that the quiz has been compeleted."""

    user = request.user
    if questionpaper_id is None:
        logout(request)
        message = reason or "You are successfully logged out."
        context = {'message': message}
        return my_render_to_response('exam/complete.html', context)
    else:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(user=user, question_paper=q_paper)
        obt_marks = paper.update_marks_obtained()
        tot_marks = paper.question_paper.total_marks
        if obt_marks == paper.question_paper.total_marks:
            context = {'message': "Hurray ! You did an excellent job.\
                       you answered all the questions correctly.\
                       You have been logged out successfully,\
                       Thank You !"}
            logout(request)
            return my_render_to_response('exam/complete.html', context)
        else:
            message = reason or "You are successfully logged out"
            context = {'message':  message}
            logout(request)
            return my_render_to_response('exam/complete.html', context)
    no = False
    message = reason or 'The quiz has been completed. Thank you.'
    if user.groups.filter(name='moderator').count() > 0:
        message = 'You are successfully Logged out.'
    if request.method == 'POST' and 'no' in request.POST:
        no = True
    if not no:
        # Logout the user and quit with the message given.
        answer_paper = AnswerPaper.objects.get(id=answerpaper_id)
        answer_paper.endtime = datetime.datetime.now()
        answer_paper.save()
        return my_redirect('/exam/quizzes/')
    else:
        return my_redirect('/exam/')


def monitor(request, questionpaper_id=None):
    """Monitor the progress of the papers taken so far."""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page!')

    if questionpaper_id is None:
        q_paper = QuestionPaper.objects.all()
        context = {'papers': [],
                   'quiz': None,
                   'quizzes': q_paper}
        return my_render_to_response('exam/monitor.html', context,
                                     context_instance=ci)
    # quiz_id is not None.
    try:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
    except QuestionPaper.DoesNotExist:
        papers = []
        q_paper = None
    else:
        papers = AnswerPaper.objects.filter(question_paper=q_paper).annotate(
            total=Sum('answers__marks')).order_by('-total')

    context = {'papers': papers, 'quiz': q_paper, 'quizzes': None}
    return my_render_to_response('exam/monitor.html', context,
                                 context_instance=ci)


def get_user_data(username):
    """For a given username, this returns a dictionary of important data
    related to the user including all the user's answers submitted.
    """
    user = User.objects.get(username=username)
    papers = AnswerPaper.objects.filter(user=user)

    data = {}
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        # Admin user may have a paper by accident but no profile.
        profile = None
    data['user'] = user
    data['profile'] = profile
    data['papers'] = papers
    return data


def show_all_users(request):
    """Shows all the users who have taken various exams/quiz."""

    user = request.user
    if not user.is_authenticated() or not is_moderator(user):
        raise Http404('You are not allowed to view this page !')
    user = User.objects.filter(username__contains="")
    questionpaper = AnswerPaper.objects.all()
    context = {'question': questionpaper}
    return my_render_to_response('exam/showusers.html', context,
                                 context_instance=RequestContext(request))


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
            return my_render_to_response('exam/show_quiz.html', context,
                                         context_instance=ci)
        else:
            for i in data:
                quiz = Quiz.objects.get(id=i).delete()
            quizzes = Quiz.objects.all()
            context = {'papers': [],
                       'quiz': None,
                       'quizzes': quizzes}
            return my_render_to_response('exam/show_quiz.html', context,
                                         context_instance=ci)

    elif request.method == 'POST' and request.POST.get('edit') == 'edit':
        data = request.POST.getlist('quiz')
        forms = []
        for j in data:
            d = Quiz.objects.get(id=j)
            form = QuizForm()
            form.initial['start_date'] = d.start_date
            form.initial['duration'] = d.duration
            form.initial['active'] = d.active
            form.initial['description'] = d.description
            form.initial['pass_criteria'] = d.pass_criteria
            form.initial['language'] = d.language
            form.initial['prerequisite'] = d.prerequisite_id
            forms.append(form)
        return my_render_to_response('exam/edit_quiz.html',
                                     {'forms': forms, 'data': data},
                                     context_instance=ci)
    else:
        quizzes = Quiz.objects.all()
        context = {'papers': [],
                   'quiz': None,
                   'quizzes': quizzes}
        return my_render_to_response('exam/show_quiz.html', context,
                                     context_instance=ci)


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
            context = {'papers': [],
                       'question': None,
                       'questions': questions}
            return my_render_to_response('exam/showquestions.html', context,
                                         context_instance=ci)
        else:
            for i in data:
                question = Question.objects.get(id=i).delete()
            questions = Question.objects.all()
            context = {'papers': [],
                       'question': None,
                       'questions': questions}
            return my_render_to_response('exam/showquestions.html', context,
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
            form.initial['test'] = d.test
            form.initial['options'] = d.options
            form.initial['type'] = d.type
            form.initial['active'] = d.active
            form.initial['snippet'] = d.snippet
            form_tags = d.tags.all()
            form_tags_split = form_tags.values('name')
            initial_tags = ""
            for tag in form_tags_split:
                initial_tags = initial_tags + str(tag['name']).strip() + ","
            if (initial_tags == ","):
                initial_tags = ""
            form.initial['tags'] = initial_tags
            forms.append(form)
        return my_render_to_response('exam/edit_question.html',
                                     {'forms': forms, 'data': data},
                                     context_instance=ci)
    else:
        questions = Question.objects.all()
        context = {'papers': [],
                   'question': None,
                   'questions': questions}
        return my_render_to_response('exam/showquestions.html', context,
                                     context_instance=ci)


def user_data(request, username):
    """Render user data."""

    current_user = request.user
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')

    data = get_user_data(username)

    context = {'data': data}
    return my_render_to_response('exam/user_data.html', context,
                                 context_instance=RequestContext(request))


def grade_user(request, username):
    """Present an interface with which we can easily grade a user's papers
    and update all their marks and also give comments for each paper.
    """
    current_user = request.user
    ci = RequestContext(request)
    if not current_user.is_authenticated() or not is_moderator(current_user):
        raise Http404('You are not allowed to view this page!')

    data = get_user_data(username)
    if request.method == 'POST':
        papers = data['papers']
        for paper in papers:
            for question, answers in paper.get_question_answers().iteritems():
                marks = float(request.POST.get('q%d_marks' % question.id))
                last_ans = answers[-1]
                last_ans.marks = marks
                last_ans.save()
            paper.comments = request.POST.get(
                'comments_%d' % paper.question_paper.id)
            paper.save()

        context = {'data': data}
        return my_render_to_response('exam/user_data.html', context,
                                     context_instance=ci)
    else:
        context = {'data': data}
        return my_render_to_response('exam/grade_user.html', context,
                                     context_instance=ci)
