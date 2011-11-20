import random
import string
import os
import stat
from os.path import dirname, pardir, abspath, join, exists
import datetime

from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from exam.models import Quiz, Question, QuestionPaper, Profile, Answer
from exam.forms import UserRegisterForm, UserLoginForm
from exam.xmlrpc_clients import python_server
from settings import URL_ROOT

# The directory where user data can be saved.
OUTPUT_DIR = abspath(join(dirname(__file__), pardir, 'output'))


def my_redirect(url):
    """An overridden redirect to deal with URL_ROOT-ing.  See settings.py 
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
    return join(OUTPUT_DIR, str(user.username))
    
def index(request):
    """The start page.
    """
    user = request.user
    if user.is_authenticated():
        return my_redirect("/exam/start/")

    return my_redirect("/exam/login/")

def user_register(request):
    """ Register a new user.
    Create a user and corresponding profile and store roll_number also."""

    user = request.user
    if user.is_authenticated():
        return my_redirect("/exam/start/")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            u_name, pwd = form.save()

            new_user = authenticate(username = u_name, password = pwd)
            login(request, new_user)
            return my_redirect("/exam/start/")
                
        else:
            return my_render_to_response('exam/register.html',
                {'form':form},
                context_instance=RequestContext(request))
    else:
        form = UserRegisterForm()
        return my_render_to_response('exam/register.html',
                {'form':form},
                context_instance=RequestContext(request))

def user_login(request):
    """Take the credentials of the user and log the user in."""

    user = request.user
    if user.is_authenticated():
        return my_redirect("/exam/start/")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data
            login(request, user)
            return my_redirect("/exam/start/")
        else:
            context = {"form": form}
            return my_render_to_response('exam/login.html', context,
                        context_instance=RequestContext(request))
    else:
        form = UserLoginForm()
        context = {"form": form}
        return my_render_to_response('exam/login.html', context,
                                     context_instance=RequestContext(request))

def start(request):
    user = request.user
    try:
        # Right now the app is designed so there is only one active quiz 
        # at a particular time.
        quiz = Quiz.objects.get(active=True)
    except Quiz.DoesNotExist:
        msg = 'No active quiz found, please contact your '\
              'instructor/administrator. Please login again thereafter.'
        return complete(request, reason=msg)
    try:
        old_paper = QuestionPaper.objects.get(user=user, quiz=quiz)
        q = old_paper.current_question()
        return show_question(request, q)
    except QuestionPaper.DoesNotExist:
        ip = request.META['REMOTE_ADDR']
        key = gen_key(10)
        new_paper = QuestionPaper(user=user, user_ip=ip, key=key, quiz=quiz)
        new_paper.start_time = datetime.datetime.now()
        
        # Make user directory.
        user_dir = get_user_dir(user)
        if not exists(user_dir):
            os.mkdir(user_dir)
            # Make it rwx by others.
            os.chmod(user_dir, stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH \
                    | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR \
                    | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)

        questions = [ str(_.id) for _ in Question.objects.all() ]
        random.shuffle(questions)
        
        new_paper.questions = "|".join(questions)
        new_paper.save()
    
        # Show the user the intro page.    
        context = {'user': user}
        ci = RequestContext(request)
        return my_render_to_response('exam/intro.html', context, 
                                     context_instance=ci)

def question(request, q_id):
    user = request.user
    if not user.is_authenticated():
        return my_redirect('/exam/login/')
    q = get_object_or_404(Question, pk=q_id)
    try:
        paper = QuestionPaper.objects.get(user=request.user)
    except QuestionPaper.DoesNotExist:
        my_redirect('/exam/start')
    time_left = paper.time_left()
    if time_left == 0:
        return complete(request, reason='Your time is up!')
    quiz_name = paper.quiz.description
    context = {'question': q, 'paper': paper, 'user': user, 
               'quiz_name': quiz_name, 
               'time_left': time_left}
    ci = RequestContext(request)
    return my_render_to_response('exam/question.html', context, 
                                 context_instance=ci)

def show_question(request, q_id):
    """Show a question if possible."""
    if len(q_id) == 0:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(request, msg)
    else:
        return question(request, q_id)

def check(request, q_id):
    user = request.user
    if not user.is_authenticated():
        return my_redirect('/exam/login/')
    question = get_object_or_404(Question, pk=q_id)
    paper = QuestionPaper.objects.get(user=user)
    answer = request.POST.get('answer')
    skip = request.POST.get('skip', None)
    
    if skip is not None:
        next_q = paper.skip()
        return show_question(request, next_q)

    # Add the answer submitted, regardless of it being correct or not.
    new_answer = Answer(question=question, answer=answer, correct=False)
    new_answer.save()
    paper.answers.add(new_answer)
        
    # Otherwise we were asked to check.  We obtain the results via XML-RPC
    # with the code executed safely in a separate process (the python_server.py)
    # running as nobody.
    user_dir = get_user_dir(user)
    success, err_msg = python_server.run_code(answer, question.test, user_dir)
    
    if success:
        # Note the success and save it.
        new_answer.correct = success
        new_answer.save()

    ci = RequestContext(request)
    if not success:
        time_left = paper.time_left()
        if time_left == 0:
            return complete(request, reason='Your time is up!')
            
        context = {'question': question, 'error_message': err_msg,
                   'paper': paper, 'last_attempt': answer,
                   'quiz_name': paper.quiz.description,
                   'time_left': time_left}

        return my_render_to_response('exam/question.html', context, 
                                     context_instance=ci)
    else:
        next_q = paper.answered_question(question.id)
        return show_question(request, next_q)
        
def quit(request):
    return my_render_to_response('exam/quit.html', 
                                 context_instance=RequestContext(request)) 

def complete(request, reason=None):
    user = request.user
    no = False
    message = reason or 'The quiz has been completed. Thank you.'
    if request.method == 'POST' and 'no' in request.POST:
        no = request.POST.get('no', False)
    if not no:
        # Logout the user and quit with the message given.
        logout(request)
        context = {'message': message}
        return my_render_to_response('exam/complete.html', context)
    else:
        return my_redirect('/exam/')
   
def monitor(request):
    """Monitor the progress of the papers taken so far."""
    q_papers = QuestionPaper.objects.all()
    questions = Question.objects.all()
    # Mapping from question id to points
    marks = dict( ( (q.id, q.points) for q in questions) )
    paper_list = []
    for q_paper in q_papers:
        paper = {}
        user = q_paper.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            # Admin user may have a paper by accident but no profile.
            continue
        paper['username'] = str(user.first_name) + ' ' + str(user.last_name)
        paper['rollno'] = str(profile.roll_number)
        qa = q_paper.questions_answered.split('|')
        answered = ', '.join(sorted(qa))
        paper['answered'] = answered if answered else 'None'
        total = sum( [marks[int(id)] for id in qa if id] )
        paper['total'] = total
        paper_list.append(paper)

    paper_list.sort(cmp=lambda x, y: cmp(x['total'], y['total']), 
                   reverse=True)

    context = {'paper_list': paper_list}
    return my_render_to_response('exam/monitor.html', context,
                                 context_instance=RequestContext(request)) 
