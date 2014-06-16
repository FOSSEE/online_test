from django import forms
from exam.models import Profile, Quiz, Question

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from taggit.forms import TagField
from taggit_autocomplete_modified.managers import TaggableManagerAutocomplete
from taggit_autocomplete_modified.widgets import TagAutocomplete
from taggit_autocomplete_modified import settings

from string import letters, punctuation, digits
import datetime

QUESTION_LANGUAGE_CHOICES = (
    ("select", "Select"),
    ("python", "Python"),
    ("bash", "Bash"),
    ("mcq", "MCQ"),
    ("C", "C Language"),
    ("C++", "C++ Language"),
    ("java", "Java Language"),
    ("scilab", "Scilab"),
    )

QUESTION_TYPE_CHOICES = (
    ("select", "Select"),
    ("mcq", "Multiple Choice"),
    ("code", "Code"),
    )

UNAME_CHARS = letters + "._" + digits
PWD_CHARS = letters + punctuation + digits


class UserRegisterForm(forms.Form):
    """A Class to create new form for User's Registration.
    It has the various fields and functions required to register
    a new user to the system"""

    username = forms.CharField(max_length=30, help_text='Letters, digits,\
                period and underscores only.')
    email = forms.EmailField()
    password = forms.CharField(max_length=30, widget=forms.PasswordInput())
    confirm_password = forms.CharField\
                       (max_length=30, widget=forms.PasswordInput())
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    roll_number = forms.CharField\
                (max_length=30, help_text="Use a dummy if you don't have one.")
    institute = forms.CharField\
                (max_length=128, help_text='Institute/Organization')
    department = forms.CharField\
                (max_length=64, help_text='Department you work/study at')
    position = forms.CharField\
        (max_length=64, help_text='Student/Faculty/Researcher/Industry/etc.')

    def clean_username(self):
        u_name = self.cleaned_data["username"]
        if u_name.strip(UNAME_CHARS):
            msg = "Only letters, digits, period and underscore characters are"\
                  " allowed in username"
            raise forms.ValidationError(msg)
        try:
            User.objects.get(username__exact=u_name)
            raise forms.ValidationError("Username already exists.")
        except User.DoesNotExist:
            return u_name

    def clean_password(self):
        pwd = self.cleaned_data['password']
        if pwd.strip(PWD_CHARS):
            raise forms.ValidationError("Only letters, digits and punctuation\
                                        are allowed in password")
        return pwd

    def clean_confirm_password(self):
        c_pwd = self.cleaned_data['confirm_password']
        pwd = self.data['password']
        if c_pwd != pwd:
            raise forms.ValidationError("Passwords do not match")

        return c_pwd

    def save(self):
        u_name = self.cleaned_data["username"]
        u_name = u_name.lower()
        pwd = self.cleaned_data["password"]
        email = self.cleaned_data['email']
        new_user = User.objects.create_user(u_name, email, pwd)

        new_user.first_name = self.cleaned_data["first_name"]
        new_user.last_name = self.cleaned_data["last_name"]
        new_user.save()

        cleaned_data = self.cleaned_data
        new_profile = Profile(user=new_user)
        new_profile.roll_number = cleaned_data["roll_number"]
        new_profile.institute = cleaned_data["institute"]
        new_profile.department = cleaned_data["department"]
        new_profile.position = cleaned_data["position"]
        new_profile.save()

        return u_name, pwd


class UserLoginForm(forms.Form):
    """Creates a form which will allow the user to log into the system."""

    username = forms.CharField(max_length=30)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput())

    def clean(self):
        super(UserLoginForm, self).clean()
        try:
            u_name, pwd = self.cleaned_data["username"],\
                          self.cleaned_data["password"]
            user = authenticate(username=u_name, password=pwd)
        except Exception:
            raise forms.ValidationError\
                        ("Username and/or Password is not entered")
        if not user:
            raise forms.ValidationError("Invalid username/password")
        return user


class QuizForm(forms.Form):
    """Creates a form to add or edit a Quiz.
    It has the related fields and functions required."""

    start_date = forms.DateField(initial=datetime.date.today)
    duration = forms.IntegerField()
    active = forms.BooleanField(required=False)
    description = forms.CharField(max_length=256, widget=forms.Textarea\
                                  (attrs={'cols': 20, 'rows': 1}))

    def save(self):
        start_date = self.cleaned_data["start_date"]
        duration = self.cleaned_data["duration"]
        active = self.cleaned_data['active']
        description = self.cleaned_data["description"]

        new_quiz = Quiz()
        new_quiz.start_date = start_date
        new_quiz.duration = duration
        new_quiz.active = active
        new_quiz.description = description
        new_quiz.save()


class QuestionForm(forms.Form):
    """Creates a form to add or edit a Question.
    It has the related fields and functions required."""

    summary = forms.CharField(widget=forms.Textarea\
                                        (attrs={'cols': 40, 'rows': 1}))
    description = forms.CharField(widget=forms.Textarea\
                                            (attrs={'cols': 40, 'rows': 1}))
    points = forms.FloatField()
    test = forms.CharField(widget=forms.Textarea\
                                    (attrs={'cols': 40, 'rows': 1}))
    options = forms.CharField(widget=forms.Textarea\
                              (attrs={'cols': 40, 'rows': 1}), required=False)
    language = forms.CharField(max_length=20, widget=forms.Select\
                               (choices=QUESTION_LANGUAGE_CHOICES))
    type = forms.CharField(max_length=8, widget=forms.Select\
                           (choices=QUESTION_TYPE_CHOICES))
    active = forms.BooleanField(required=False)
    tags = TagField(widget=TagAutocomplete(), required=False)
    snippet = forms.CharField(widget=forms.Textarea\
                              (attrs={'cols': 40, 'rows': 1}), required=False)

    def save(self):
        summary = self.cleaned_data["summary"]
        description = self.cleaned_data["description"]
        points = self.cleaned_data['points']
        test = self.cleaned_data["test"]
        options = self.cleaned_data['options']
        language = self.cleaned_data['language']
        type = self.cleaned_data["type"]
        active = self.cleaned_data["active"]
        snippet = self.cleaned_data["snippet"]

        new_question = Question()
        new_question.summary = summary
        new_question.description = description
        new_question.points = points
        new_question.test = test
        new_question.options = options
        new_question.language = language
        new_question.type = type
        new_question.active = active
        new_question.snippet = snippet
        new_question.save()
