from django import forms
from yaksh.models import get_model_class, Profile, Quiz, Question, TestCase, Course,\
                         QuestionPaper, StandardTestCase, StdIOBasedTestCase, \
                         HookTestCase, IntegerTestCase, StringTestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from taggit.managers import TaggableManager
from taggit.forms import TagField
from django.forms.models import inlineformset_factory
from django.db.models import Q
from textwrap import dedent
try:
    from string import letters
except ImportError:
    from string import ascii_letters as letters
from string import punctuation, digits
import datetime
import pytz

languages = (
    ("select", "Select Language"),
    ("python", "Python"),
    ("bash", "Bash"),
    ("c", "C Language"),
    ("cpp", "C++ Language"),
    ("java", "Java Language"),
    ("scilab", "Scilab"),
    )

question_types = (
    ("select", "Select Question Type"),
    ("mcq", "Multiple Choice"),
    ("mcc", "Multiple Correct Choices"),
    ("code", "Code"),
    ("upload", "Assignment Upload"),
    ("integer", "Answer in Integer"),
    ("string", "Answer in String"),
    ("float", "Answer in Float"),
    )

test_case_types = (
        ("standardtestcase", "Standard Testcase"),
        ("stdiobasedtestcase", "StdIO Based Testcase"),
        ("mcqtestcase", "MCQ Testcase"),
        ("hooktestcase", "Hook Testcase"),
        ("integertestcase", "Integer Testcase"),
        ("stringtestcase", "String Testcase"),
        ("floattestcase", "Float Testcase"),
        )

UNAME_CHARS = letters + "._" + digits
PWD_CHARS = letters + punctuation + digits

attempts = [(i, i) for i in range(1, 6)]
attempts.append((-1, 'Infinite'))
days_between_attempts = ((j, j) for j in range(401))

def get_object_form(model, exclude_fields=None):  
    model_class = get_model_class(model)
    class _ObjectForm(forms.ModelForm):
        class Meta:
            model = model_class
            exclude = exclude_fields
    return _ObjectForm


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
    timezone = forms.ChoiceField(choices=[(tz, tz) for tz in pytz.common_timezones],
                                initial=pytz.utc)

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
        new_profile.timezone = cleaned_data["timezone"]
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


class QuizForm(forms.ModelForm):
    """Creates a form to add or edit a Quiz.
    It has the related fields and functions required."""

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        course_id = kwargs.pop('course')
        super(QuizForm, self).__init__(*args, **kwargs)
        self.fields['prerequisite'] = forms.ModelChoiceField(
                queryset=Quiz.objects.filter(course__id=course_id,
                                             is_trial=False))
        self.fields['prerequisite'].required = False
        self.fields['course'] = forms.ModelChoiceField(
                queryset=Course.objects.filter(id=course_id), empty_label=None)
        self.fields["instructions"].initial =  dedent("""\
                                              <p>
                                              This examination system has been 
                                              developed with the intention of 
                                              making you learn programming and 
                                              be assessed in an interactive and
                                              fun manner.
                                              You will be presented with a 
                                              series of programming questions 
                                              and problems that you will answer 
                                              online and get immediate 
                                              feedback for.
                                              </p>
                                              <p> 
                                              Here are some important 
                                              instructions and rules that you 
                                              should understand carefully.</p> 
                                              <ul>
                                              <li>For any programming questions,
                                               you can submit solutions as many 
                                               times as you want without a 
                                               penalty. You may skip questions 
                                               and solve them later.</li>
                                               <li> You <strong>may</strong> 
                                               use your computer's Python/IPython 
                                               shell or an editor to solve the 
                                               problem and cut/paste the 
                                               solution to the web interface.
                                               </li>
                                               <li> <strong>You are not allowed 
                                               to use any internet resources, 
                                               i.e. no google etc.</strong> 
                                               </li>
                                               <li> Do not copy or share the 
                                               questions or answers with anyone 
                                               until the exam is complete 
                                               <strong>for everyone</strong>.
                                               </li>
                                               <li> <strong>All</strong> your 
                                               attempts at the questions are 
                                               logged. Do not try to outsmart 
                                               and break the testing system. 
                                               If you do, we know who you are 
                                               and we will expel you from the 
                                               course. You have been warned.
                                               </li>
                                               </ul>
                                               <p>
                                                We hope you enjoy taking this 
                                                exam !!!
                                                </p>
                                                """)

    class Meta:
        model = Quiz
        exclude = ["is_trial"]


class QuestionForm(forms.ModelForm):
    """Creates a form to add or edit a Question.
    It has the related fields and functions required."""

    class Meta:
        model = Question
        exclude = ['user', 'active']


class FileForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                                 required=False)


class RandomQuestionForm(forms.Form):
    question_type = forms.CharField(max_length=8, widget=forms.Select\
                                    (choices=question_types))
    marks = forms.CharField(max_length=8, widget=forms.Select\
            (choices=(('select', 'Select Marks'),)))
    shuffle_questions = forms.BooleanField(required=False)


class QuestionFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(QuestionFilterForm, self).__init__(*args, **kwargs)
        questions = Question.objects.filter(user_id=user.id)
        points_list = questions.values_list('points', flat=True).distinct()
        points_options = [(None, 'Select Marks')]
        points_options.extend([(point, point) for point in points_list])
        self.fields['marks'] = forms.FloatField(widget=forms.Select\
                                                    (choices=points_options))

    language = forms.CharField(max_length=8, widget=forms.Select\
                                (choices=languages))
    question_type = forms.CharField(max_length=8, widget=forms.Select\
                                    (choices=question_types))


class CourseForm(forms.ModelForm):
    """ course form for moderators """

    class Meta:
        model = Course
        fields = ['name', 'active', 'enrollment', 'instructions']


class ProfileForm(forms.ModelForm):
    """ profile form for students and moderators """

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'institute',
                  'department', 'roll_number', 'position', 'timezone']

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            user = kwargs.pop('user')
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name


class UploadFileForm(forms.Form):
    file = forms.FileField()


class QuestionPaperForm(forms.ModelForm):
    class Meta:
        model = QuestionPaper
        fields = ['shuffle_questions']

