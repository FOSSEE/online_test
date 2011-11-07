import random
import sys
import traceback
import string

from django.db import IntegrityError
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from exam.models import Question, Quiz, Profile
from exam.forms import UserRegisterForm

def gen_key(no_of_chars):
    allowed_chars = string.digits+string.uppercase
    return ''.join([random.choice(allowed_chars) for i in range(no_of_chars)])

def index_old(request):
    """The start page.
    """
    question_list = Question.objects.all()
    context = {'question_list': question_list}
    return render_to_response('exam/index.html', context)
    
def index(request):
    """The start page.
    """
    # Largely copied from Nishanth's quiz app.
    user = request.user
    if user.is_authenticated():
        return redirect("/exam/start/")
    else:
        try:
            ip = request.META['REMOTE_ADDR']
            Quiz.objects.get(user_ip=ip)
            return redirect("/exam/complete")
        except Quiz.DoesNotExist:
            pass

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            while True:
                try:
                    username = gen_key(20)
                    new_user = User.objects.create_user(username, "temp@temp.com", "123")
                    break
                except IntegrityError:
                    pass

            new_user.first_name = data['first_name']
            new_user.last_name = data['last_name']
            new_user.save()

            new_profile = Profile(user=new_user)
            new_profile.roll_number = data['roll_number']
            new_profile.save()

            user = authenticate(username=username, password="123")
            login(request, user)
            return redirect("/exam/start/")

        else:
            return render_to_response('exam/register.html',{'form':form},
                context_instance=RequestContext(request))
    else:
        form = UserRegisterForm()
        return render_to_response('exam/register.html',{'form':form},
             context_instance=RequestContext(request))

def show_question(request, q_id):
    if len(q_id) == 0:
        return redirect("/exam/complete")
    else:
        return question(request, q_id)
    
def start(request):
    user = request.user
    try:
        old_quiz = Quiz.objects.get(user=user)
        q = old_quiz.current_question()
        return show_question(request, q)
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

def test_answer(func_code, test_code):
    exec func_code
    exec test_code

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
    retry = True
    try:
        test_answer(answer, question.test)
    except:
        type, value, tb = sys.exc_info()
        info = traceback.extract_tb(tb)
        fname, lineno, func, text = info[-1]
        err = "{0}: {1} In code: {2}".format(type.__name__, str(value), text)
    else:
        retry = False
        err = 'Correct answer'
        
    ci = RequestContext(request)
    if retry:
        context = {'question': question, 'error_message': err}
        return render_to_response('exam/question.html', context, 
                                  context_instance=ci)
    else:
        next_q = quiz.answered_question(question.id)
        return show_question(request, next_q)

def complete(request):
    logout(request)
    return render_to_response('exam/complete.html')
    
