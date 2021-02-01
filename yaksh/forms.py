from django import forms
from yaksh.models import (
    get_model_class, Profile, Quiz, Question, Course, QuestionPaper, Lesson,
    LearningModule, TestCase, languages, question_types, Post, Comment,
    Topic
)
from grades.models import GradingSystem
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.template.defaultfilters import filesizeformat
from textwrap import dedent
try:
    from string import letters
except ImportError:
    from string import ascii_letters as letters
from string import punctuation, digits
import pytz
from ast import literal_eval

from .send_emails import generate_activation_key

languages = (("", "Select Language"),) + languages

question_types = (("", "Select Question Type"),) + question_types

test_case_types = (
    ("standardtestcase", "Standard Testcase"),
    ("stdiobasedtestcase", "StdIO Based Testcase"),
    ("mcqtestcase", "MCQ Testcase"),
    ("hooktestcase", "Hook Testcase"),
    ("integertestcase", "Integer Testcase"),
    ("stringtestcase", "String Testcase"),
    ("floattestcase", "Float Testcase"),
)

status_types = (
    ('select', 'Select Status'),
    ('active', 'Active'),
    ('closed', 'Inactive'),
    )

UNAME_CHARS = letters + "._" + digits
PWD_CHARS = letters + punctuation + digits

attempts = [(i, i) for i in range(1, 6)]
attempts.append((-1, 'Infinite'))
days_between_attempts = ((j, j) for j in range(401))

# Add bootstrap class separated by space
form_input_class = "form-control"


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

    username = forms.CharField(
        max_length=30, help_text='Letters, digits,\
                period and underscores only.',
        widget=forms.TextInput(
            {'class': form_input_class, 'placeholder': "Username"})
        )
    email = forms.EmailField(widget=forms.TextInput(
        {'class': form_input_class, 'placeholder': "Email"}
        ))
    password = forms.CharField(
        max_length=30,
        widget=forms.PasswordInput(
            {'class': form_input_class, 'placeholder': "Password"}))
    confirm_password = forms.CharField(
        max_length=30, widget=forms.PasswordInput(
            {'class': form_input_class, 'placeholder': "Confirm Password"}
            ))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(
        {'class': form_input_class, 'placeholder': "First Name"}
        ))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(
        {'class': form_input_class, 'placeholder': "Last Name"}
        ))
    roll_number = forms.CharField(
        max_length=30, help_text="Use a dummy if you don't have one.",
        widget=forms.TextInput(
            {'class': form_input_class, 'placeholder': "Roll Number"}
        ))
    institute = forms.CharField(
        max_length=128, help_text='Institute/Organization',
        widget=forms.TextInput(
            {'class': form_input_class, 'placeholder': "Institute"}
        ))
    department = forms.CharField(
        max_length=64, help_text='Department you work/study at',
        widget=forms.TextInput(
            {'class': form_input_class, 'placeholder': "Department"}
        ))
    position = forms.CharField(
        max_length=64,
        help_text='Student/Faculty/Researcher/Industry/Fellowship/etc.',
        widget=forms.TextInput(
            {'class': form_input_class, 'placeholder': "Position"}
        ))
    timezone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.common_timezones],
        help_text='All timings are shown based on the selected timezone',
        widget=forms.Select({'class': 'custom-select'}),
        initial=pytz.country_timezones['IN'][0])

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

    def clean_email(self):
        user_email = self.cleaned_data['email']
        if User.objects.filter(email=user_email).exists():
            raise forms.ValidationError("This email already exists")
        return user_email

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
        if settings.IS_DEVELOPMENT:
            new_profile.is_email_verified = True
        else:
            new_profile.activation_key = generate_activation_key(
                new_user.username)
            new_profile.key_expiry_time = timezone.now() + timezone.timedelta(
                minutes=20)
        new_profile.save()
        return u_name, pwd, new_user.email, new_profile.activation_key


class UserLoginForm(forms.Form):
    """Creates a form which will allow the user to log into the system."""

    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={'class': form_input_class, 'placeholder': 'Username'}
        )
    )
    password = forms.CharField(
        max_length=30,
        widget=forms.PasswordInput(
            attrs={'class': form_input_class, 'placeholder': 'Password'}
        )
    )

    def clean(self):
        super(UserLoginForm, self).clean()
        try:
            u_name, pwd = self.cleaned_data["username"],\
                          self.cleaned_data["password"]
            user = authenticate(username=u_name, password=pwd)
        except Exception:
            raise forms.ValidationError(
                "Username and/or Password is not entered"
            )
        if not user:
            raise forms.ValidationError("Invalid username/password")
        return user


class ExerciseForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ExerciseForm, self).__init__(*args, **kwargs)
        self.fields['description'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': "Exercise Description"}
        )

    class Meta:
        model = Quiz
        fields = ['description', 'view_answerpaper', 'active']


class QuizForm(forms.ModelForm):
    """Creates a form to add or edit a Quiz.
    It has the related fields and functions required."""

    def __init__(self, *args, **kwargs):
        super(QuizForm, self).__init__(*args, **kwargs)

        self.fields['start_date_time'].widget.attrs.update(
            {'class': form_input_class}
        )
        self.fields['end_date_time'].widget.attrs.update(
            {'class': form_input_class}
        )
        self.fields['duration'].widget.attrs.update(
            {'class': form_input_class}
        )
        self.fields['description'].widget.attrs.update(
            {'class': form_input_class}
        )
        self.fields['attempts_allowed'].widget.attrs.update(
            {'class': 'custom-select'}
        )
        self.fields['time_between_attempts'].widget.attrs.update(
            {'class': form_input_class}
        )
        self.fields['instructions'].widget.attrs.update(
            {'class': form_input_class}
        )
        self.fields['weightage'].widget.attrs.update(
            {'class': form_input_class}
        )
        self.fields['pass_criteria'].widget.attrs.update(
            {'class': form_input_class}
        )

        self.fields["instructions"].initial = dedent("""\
            <p>
            This examination system has been developed with the intention of
            making you learn programming and be assessed in an interactive and
            fun manner.You will be presented with a series of programming
            questions and problems that you will answer online and get
            immediate feedback for.
            </p><p>Here are some important instructions and rules that you
            should understand carefully.</p>
            <ul><li>For any programming questions, you can submit solutions as
            many times as you want without a penalty. You may skip questions
            and solve them later.</li><li> You <strong>may</strong>
            use your computer's Python/IPython shell or an editor to solve the
            problem and cut/paste the solution to the web interface.
            </li><li> <strong>You are not allowed to use any internet resources
            i.e. no google etc.</strong>
            </li>
            <li> Do not copy or share the questions or answers with anyone
            until the exam is complete <strong>for everyone</strong>.
            </li><li> <strong>All</strong> your attempts at the questions are
            logged. Do not try to outsmart and break the testing system.
            If you do, we know who you are and we will expel you from the
            course. You have been warned.
            </li></ul>
            <p>We hope you enjoy taking this exam !!!</p>
        """)

    class Meta:
        model = Quiz
        exclude = ["is_trial", "creator", "is_exercise"]


class QuestionForm(forms.ModelForm):
    """Creates a form to add or edit a Question.
    It has the related fields and functions required."""

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['summary'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Summary'}
        )
        self.fields['language'].widget.attrs.update(
            {'class': 'custom-select'}
        )
        self.fields['topic'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Topic name'}
        )
        self.fields['type'].widget.attrs.update(
            {'class': 'custom-select'}
        )
        self.fields['description'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Description'}
        )
        self.fields['tags'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Tags'}
        )
        self.fields['solution'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Solution'}
        )
        self.fields['snippet'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Snippet'}
        )
        self.fields['min_time'].widget.attrs.update(
            {'class': form_input_class}
        )

    class Meta:
        model = Question
        exclude = ['user', 'active']


class FileForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(
                                attrs={
                                    'multiple': True,
                                    'class': 'custom-file-input'
                                    }
                                ),
                                required=False)


class RandomQuestionForm(forms.Form):
    question_type = forms.CharField(
        max_length=8, widget=forms.Select(choices=question_types)
    )
    marks = forms.CharField(
        max_length=8, widget=forms.Select(
            choices=(('select', 'Select Marks'),))
    )
    shuffle_questions = forms.BooleanField(required=False)


class QuestionFilterForm(forms.Form):

    language = forms.ChoiceField(
        choices=languages,
        widget=forms.Select(attrs={'class': 'custom-select'}),
        required=False
        )
    question_type = forms.ChoiceField(
        choices=question_types,
        widget=forms.Select(attrs={'class': 'custom-select'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        lang = kwargs.pop("language") if "language" in kwargs else None
        que_type = kwargs.pop("type") if "type" in kwargs else None
        marks = kwargs.pop("marks") if "marks" in kwargs else None
        super(QuestionFilterForm, self).__init__(*args, **kwargs)
        points = Question.objects.filter(
            user_id=user.id).values_list('points', flat=True).distinct()
        points_options = [('', 'Select Marks')]
        points_options.extend([(point, point) for point in points])
        self.fields['marks'] = forms.ChoiceField(
            choices=points_options,
            widget=forms.Select(attrs={'class': 'custom-select'}),
            required=False
        )
        self.fields['marks'].required = False
        self.fields['language'].initial = lang
        self.fields['question_type'].initial = que_type
        self.fields['marks'].initial = marks


class SearchFilterForm(forms.Form):
    search_tags = forms.CharField(
        label='Search Tags',
        widget=forms.TextInput(attrs={'placeholder': 'Search by course name',
                                      'class': form_input_class, }),
        required=False
        )
    search_status = forms.ChoiceField(
        choices=status_types,
        widget=forms.Select(attrs={'class': 'custom-select'})
        )

    def __init__(self, *args, **kwargs):
        status = kwargs.pop("status") if "status" in kwargs else None
        tags = kwargs.pop("tags") if "tags" in kwargs else None
        super(SearchFilterForm, self).__init__(*args, **kwargs)
        self.fields["search_status"].initial = status
        self.fields["search_tags"].initial = tags


class CourseForm(forms.ModelForm):
    """ course form for moderators """
    class Meta:
        model = Course
        fields = [
            'name', 'enrollment', 'active', 'code', 'instructions',
            'start_enroll_time', 'end_enroll_time', 'grading_system',
            'view_grade'
        ]

    def save(self, commit=True, *args, **kwargs):
        instance = super(CourseForm, self).save(commit=False)
        if instance.code:
            instance.hidden = True
        else:
            instance.hidden = False

        if commit:
            instance.save()
        return instance

    def __init__(self, user, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Course Name'}
        )
        self.fields['enrollment'].widget.attrs.update(
            {'class': 'custom-select'}
        )
        self.fields['code'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Course Code'}
        )
        self.fields['instructions'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Course instructions'}
        )
        self.fields['start_enroll_time'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Course Start DateTime'}
        )
        self.fields['end_enroll_time'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Course End DateTime'}
        )
        self.fields['grading_system'].widget.attrs.update(
            {'class': 'custom-select'}
        )
        if (self.instance.id and
                self.instance.teachers.filter(id=user.id).exists()):
            self.fields['grading_system'].widget.attrs['disabled'] = True
        else:
            grading_choices = GradingSystem.objects.filter(
                creator=user
            )
            self.fields['grading_system'].queryset = grading_choices


class ProfileForm(forms.ModelForm):
    """ profile form for students and moderators """

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'institute',
                  'department', 'roll_number', 'position', 'timezone']

    first_name = forms.CharField(max_length=30, widget=forms.TextInput(
                    {'class': form_input_class, 'placeholder': "First Name"}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(
                    {'class': form_input_class, 'placeholder': "Last Name"}))

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            user = kwargs.pop('user')
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].initial = user.first_name
        self.fields['first_name'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'First Name'}
        )
        self.fields['last_name'].initial = user.last_name
        self.fields['last_name'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Last Name'}
        )
        self.fields['institute'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Institute'}
        )
        self.fields['department'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Department'}
        )
        self.fields['roll_number'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Roll Number'}
        )
        self.fields['position'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Position'}
        )
        self.fields['timezone'] = forms.ChoiceField(
            choices=[(tz, tz) for tz in pytz.common_timezones],
            help_text='All timings are shown based on the selected timezone',
            widget=forms.Select({'class': 'custom-select'})
            )


class UploadFileForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'custom-file-input'})
    )


class QuestionPaperForm(forms.ModelForm):
    class Meta:
        model = QuestionPaper
        fields = ['shuffle_questions', 'shuffle_testcases']


class LessonForm(forms.ModelForm):
    video_options = (
            ("---", "Select Video Option"), ("youtube", "Youtube"),
            ("vimeo", "Vimeo"), ("others", "Others")
        )
    video_option = forms.ChoiceField(
        choices=video_options, required=False,
        help_text='Add videos from youtube, vimeo or other',
        widget=forms.Select({'class': 'custom-select'}))
    video_url = forms.CharField(
        widget=forms.TextInput(
            {'class': form_input_class,
             'placeholder': 'Video ID for Youtube, Vimeo and URL for others'}
            ),
        required=False
        )

    def __init__(self, *args, **kwargs):
        super(LessonForm, self).__init__(*args, **kwargs)
        des_msg = "Enter Lesson Description as Markdown text"
        self.fields['name'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Lesson Name'}
        )
        self.fields['description'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': des_msg}
        )
        self.fields['video_path'].widget = forms.HiddenInput()
        try:
            video = literal_eval(self.instance.video_path)
            key = list(video.keys())[0]
            self.fields['video_option'].initial = key
            self.fields['video_url'].initial = video[key]
        except ValueError:
            pass

    class Meta:
        model = Lesson
        exclude = ['creator', 'html_data']

    def clean_video_file(self):
        file = self.cleaned_data.get("video_file")
        if file:
            extension = file.name.split(".")[-1]
            actual_extension = ["mp4", "ogv", "webm"]
            if extension not in actual_extension:
                raise forms.ValidationError(
                    "Please upload video files in {0} format".format(
                        ", ".join(actual_extension))
                    )
            if file.size > settings.MAX_UPLOAD_SIZE:
                raise forms.ValidationError(
                    f"Video file size must be less than "\
                    f"{filesizeformat(settings.MAX_UPLOAD_SIZE)}. "
                    f"Current size is {filesizeformat(file.size)}"
                )
        return file

    def clean_video_path(self):
        path = self.cleaned_data.get("video_path")
        if path:
            try:
                value = literal_eval(path)
                if not isinstance(value, dict):
                    raise forms.ValidationError(
                        "Value must be dictionary e.g {'youtube': 'video-id'}"
                    )
                else:
                    if len(value) > 1:
                        raise forms.ValidationError(
                            "Only one type of video path is allowed"
                        )
            except ValueError:
                raise forms.ValidationError(
                    "Value must be dictionary e.g {'youtube': 'video-id'}"
                )
        return path


class LessonFileForm(forms.Form):
    Lesson_files = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={'multiple': True, 'class': "custom-file-input"}),
        required=False)


class LearningModuleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(LearningModuleForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['size'] = 30
        self.fields['name'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Module Name'}
        )
        self.fields['description'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Module Description'}
        )

    class Meta:
        model = LearningModule
        fields = ['name', 'description', 'active']


class TestcaseForm(forms.ModelForm):

    type = forms.CharField(
        widget=forms.TextInput(
            attrs={'readonly': 'readonly', 'class': form_input_class})
    )

    class Meta:
        model = TestCase
        fields = ["type"]


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "description", "image", "anonymous"]
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control'
                }
            ),
            'image': forms.FileInput(
                attrs={
                    'class': 'form-control-file'
                }
            )
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["description", "image", "anonymous"]
        widgets = {
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control'
                }
            ),
            'image': forms.FileInput(
                attrs={
                    'class': 'form-control-file'
                }
            )
        }


class TopicForm(forms.ModelForm):

    timer = forms.CharField()

    def __init__(self, *args, **kwargs):
        time = kwargs.pop("time") if "time" in kwargs else None
        super(TopicForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Name'}
        )
        self.fields['timer'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Time'}
        )
        self.fields['description'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Description'}
        )
        self.fields['timer'].initial = time

    class Meta:
        model = Topic
        fields = "__all__"

    def clean_timer(self):
        timer = self.cleaned_data.get("timer")
        if timer:
            try:
                hh, mm, ss = timer.split(":")
            except ValueError:
                raise forms.ValidationError(
                    "Marker time should be in the format hh:mm:ss"
                )
        return timer


class VideoQuizForm(forms.ModelForm):

    type = forms.CharField()

    timer = forms.CharField()

    def __init__(self, *args, **kwargs):
        if 'question_type' in kwargs:
            question_type = kwargs.pop('question_type')
        else:
            question_type = "mcq"
        time = kwargs.pop("time") if "time" in kwargs else None
        super(VideoQuizForm, self).__init__(*args, **kwargs)
        self.fields['summary'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Summary'}
        )
        self.fields['language'].widget.attrs.update(
            {'class': 'custom-select'}
        )
        self.fields['topic'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Question topic name'}
        )
        self.fields['points'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Points'}
        )
        self.fields['type'].widget.attrs.update(
            {'class': form_input_class, 'readonly': True}
        )
        self.fields['type'].initial = question_type
        self.fields['description'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Description',
             'id': 'que_description'}
        )
        self.fields['timer'].widget.attrs.update(
            {'class': form_input_class, 'placeholder': 'Quiz Time'}
        )
        self.fields['timer'].initial = time

    class Meta:
        model = Question
        fields = ['summary', 'description', 'points',
                  'language', 'type', 'topic']

    def clean_timer(self):
        timer = self.cleaned_data.get("timer")
        if timer:
            try:
                hh, mm, ss = timer.split(":")
            except ValueError:
                raise forms.ValidationError(
                    "Marker time should be in the format hh:mm:ss"
                )
        return timer