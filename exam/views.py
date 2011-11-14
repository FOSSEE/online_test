import random
import string
import os
import stat
from os.path import dirname, pardir, abspath, join, exists

from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from exam.models import Question, Quiz, Profile, Answer
from exam.forms import UserRegisterForm, UserLoginForm
from exam.xmlrpc_clients import python_server

# The directory where user data can be saved.
OUTPUT_DIR = abspath(join(dirname(__file__), pardir, 'output'))

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
    # Largely copied from Nishanth's quiz app.
    user = request.user
    if user.is_authenticated():
        return redirect("/exam/start/")

    return redirect("/exam/login/")

def user_register(request):
    """ Register a new user.
    Create a user and corresponding profile and store roll_number also."""

    user = request.user
    if user.is_authenticated():
        return redirect("/exam/start/")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            u_name, pwd = form.save()

            new_user = authenticate(username = u_name, password = pwd)
            login(request, new_user)
            return redirect("/exam/start/")
                
        else:
            return render_to_response('exam/register.html',{'form':form},
                context_instance=RequestContext(request))
    else:
        form = UserRegisterForm()
        return render_to_response('exam/register.html',{'form':form},
             context_instance=RequestContext(request))

def user_login(request):
    """Take the credentials of the user and log the user in."""

    user = request.user
    if user.is_authenticated():
        return redirect("/exam/start/")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data
            login(request, user)
            return redirect("/exam/start/")
        else:
            context = {"form": form,}
            return render_to_response('exam/login.html', context,
                 context_instance=RequestContext(request))
    else:
        form = UserLoginForm()
        context = {"form": form}
        return render_to_response('exam/login.html', context,
             context_instance=RequestContext(request))

def show_question(request, q_id):
    """Show a question if possible."""
    if len(q_id) == 0:
        return redirect("/exam/complete")
    else:
        return question(request, q_id)
    
def start(request):
    user = request.user
    try:
        old_quiz = Quiz.objects.get(user=user)
        if not old_quiz.is_active:
            return redirect("/exam/complete/")
        q = old_quiz.current_question()
        return redirect('/exam/%s'%q)
    except Quiz.DoesNotExist:
        ip = request.META['REMOTE_ADDR']
        key = gen_key(10)
        new_quiz = Quiz(user=user, user_ip=ip, key=key)
        
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
        
        new_quiz.questions = "|".join(questions)
        new_quiz.save()
    
        # Show the user the intro page.    
        context = {'user': user}
        ci = RequestContext(request)
        return render_to_response('exam/intro.html', context, 
                                  context_instance=ci)

def question(request, q_id):
    user = request.user
    q = get_object_or_404(Question, pk=q_id)
    try:
        quiz = Quiz.objects.get(user=request.user)
    except Quiz.DoesNotExist:
        redirect('/exam/start')
    context = {'question': q, 'quiz': quiz, 'user': user}
    ci = RequestContext(request)
    return render_to_response('exam/question.html', context, 
                              context_instance=ci)

def check(request, q_id):
    user = request.user
    question = get_object_or_404(Question, pk=q_id)
    quiz = Quiz.objects.get(user=user)
    answer = request.POST.get('answer')
    skip = request.POST.get('skip', None)
    
    if skip is not None:
        next_q = quiz.skip()
        return show_question(request, next_q)
        
    # Otherwise we were asked to check.  We obtain the results via XML-RPC
    # with the code executed safely in a separate process (the python_server.py)
    # running as nobody.
    user_dir = get_user_dir(user)
    success, err_msg = python_server.run_code(answer, question.test, user_dir)

    # Add the answer submitted.
    new_answer = Answer(question=question, answer=answer.strip())    
    new_answer.correct = success
    new_answer.save()
    quiz.answers.add(new_answer)

    ci = RequestContext(request)
    if not success:
        context = {'question': question, 'error_message': err_msg,
                   'quiz': quiz, 'last_attempt': answer}
        return render_to_response('exam/question.html', context, 
                                  context_instance=ci)
    else:
        next_q = quiz.answered_question(question.id)
        return show_question(request, next_q)
        
def quit(request):
    return render_to_response('exam/quit.html', 
                              context_instance=RequestContext(request)) 

def complete(request):
    user = request.user
    yes = True
    if request.method == 'POST':
        yes = request.POST.get('yes', None)
    if yes:
        quiz = Quiz.objects.get(user=user)
        quiz.is_active = False
        quiz.save()
        logout(request)
        return render_to_response('exam/complete.html')
    else:
        return redirect('/exam/')
   
def monitor(request):
    """Monitor the progress of the quizzes taken so far."""
    quizzes = Quiz.objects.all()
    questions = Question.objects.all()
    # Mapping from question id to points
    marks = dict( ( (q.id, q.points) for q in questions) )
    quiz_list = []
    for quiz in quizzes:
        paper = {}
        user = quiz.user
        paper['username'] = str(user.first_name) + ' ' + str(user.last_name)
        paper['rollno'] = str(Profile.objects.get(user=user).roll_number)
        qa = quiz.questions_answered.split('|')
        answered = ', '.join(sorted(qa))
        paper['answered'] = answered if answered else 'None'
        total = sum( [marks[int(id)] for id in qa if id] )
        paper['total'] = total
        quiz_list.append(paper)

    quiz_list.sort(cmp=lambda x, y: cmp(x['total'], y['total']), 
                   reverse=True)

    context = {'quiz_list': quiz_list}
    return render_to_response('exam/monitor.html', context,
                              context_instance=RequestContext(request)) 
