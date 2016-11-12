from django import forms
from yaksh.models import get_model_class, Profile, Quiz, Question, TestCase, Course,\
                         QuestionPaper, StandardTestCase, StdioBasedTestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from taggit.managers import TaggableManager
from taggit.forms import TagField
from django.forms.models import inlineformset_factory
from django.db.models import Q
try:
    from string import letters
except ImportError:
    from string import ascii_letters as letters
from string import punctuation, digits
import datetime
import pytz
from textwrap import dedent

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
    )

test_case_types = (
        ("standardtestcase", "Standard Testcase"),
        ("stdiobasedtestcase", "Stdio Based Testcase"),
        ("mcqtestcase", "MCQ Testcase"),
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

    class Meta:
        model = Quiz
        exclude = ["is_trial"]


class QuestionForm(forms.ModelForm):
    """Creates a form to add or edit a Question.
    It has the related fields and functions required."""

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields["hook_code"].initial = dedent("""
                                             def python_hook(user_answer, user_output):
                                                 success=False
                                                 err = 'Incorrect answer'
                                                 '''user answer contains the user code
                                                    and user output contains the std output
                                                    of the executed code.
                                                    always return sucess and err where
                                                    success will be true if the output is correct.
                                                    err will be a string.
                                                    '''
                                                 return success, err
                                             """)

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
    class Meta:
        model = Course
        fields = ['name', 'active', 'enrollment']


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
