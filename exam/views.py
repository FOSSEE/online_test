import random
import sys
import traceback
import string

from django.db import IntegrityError
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from exam.models import Question, Quiz, Profile, Answer
from exam.forms import UserRegisterForm, UserLoginForm

def gen_key(no_of_chars):
    """Generate a random key of the number of characters."""
    allowed_chars = string.digits+string.uppercase
    return ''.join([random.choice(allowed_chars) for i in range(no_of_chars)])
    
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

        questions = [ str(_.id) for _ in Question.objects.all() ]
        random.shuffle(questions)
        questions = questions[:3]
        
        new_quiz.questions = "|".join(questions)
        new_quiz.save()
        q = new_quiz.current_question()

        return show_question(request, q)

def question(request, q_id):
    q = get_object_or_404(Question, pk=q_id)
    try:
        quiz = Quiz.objects.get(user=request.user)
    except Quiz.DoesNotExist:
        redirect('/exam/start')
    context = {'question': q, 'quiz': quiz}
    ci = RequestContext(request)
    return render_to_response('exam/question.html', context, 
                              context_instance=ci)

def test_python(answer, test_code):
    """Tests given Python function with the test code supplied.

    Returns
    -------
    
    A tuple: (success, error message).
    
    """
    success = False
    tb = None
    try:
        submitted = compile(answer, '<string>', mode='exec')
        g = {}
        exec submitted in g
        _tests = compile(test_code, '<string>', mode='exec')
        exec _tests in g
    except AssertionError:
        type, value, tb = sys.exc_info()
        info = traceback.extract_tb(tb)
        fname, lineno, func, text = info[-1]
        text = str(test_code).splitlines()[lineno-1]
        err = "{0} {1} in: {2}".format(type.__name__, str(value), text)
    except:
        type, value = sys.exc_info()[:2]
        err = "Error: {0}".format(repr(value))
    else:
        success = True
        err = 'Correct answer'
    finally:
        del tb

    return success, err


def check(request, q_id):
    user = request.user
    question = get_object_or_404(Question, pk=q_id)
    quiz = Quiz.objects.get(user=user)
    answer = request.POST.get('answer')
    skip = request.POST.get('skip', None)
    
    if skip is not None:
        next_q = quiz.skip()
        return show_question(request, next_q)
        
    # Otherwise we were asked to check.
    success, err_msg = test_python(answer, question.test)

    # Add the answer submitted.
    new_answer = Answer(question=question, answer=answer.strip())    
    new_answer.correct = success
    new_answer.save()
    quiz.answers.add(new_answer)

    ci = RequestContext(request)
    if not success:
        context = {'question': question, 'error_message': err_msg,
                   'last_attempt': answer}
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
