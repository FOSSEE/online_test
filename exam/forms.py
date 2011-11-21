from django import forms
from exam.models import Profile

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from string import letters, punctuation, digits

UNAME_CHARS = letters + "._" + digits
PWD_CHARS = letters + punctuation + digits

class UserRegisterForm(forms.Form):

    username = forms.CharField(max_length=30, 
            help_text='Letters, digits, period and underscores only.')
    email = forms.EmailField()
    password = forms.CharField(max_length=30, 
                               widget=forms.PasswordInput())
    confirm_password = forms.CharField(max_length=30, 
                                       widget=forms.PasswordInput())
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    roll_number = forms.CharField(max_length=30, 
                             help_text="Use a dummy if you don't have one.")
    institute = forms.CharField(max_length=128, 
                    help_text='Institute/Organization')
    department = forms.CharField(max_length=64, 
                    help_text='Department you work/study at')
    position = forms.CharField(max_length=64,
                    help_text='Student/Faculty/Researcher/Industry/etc.')

    def clean_username(self):
        u_name = self.cleaned_data["username"]

        if u_name.strip(UNAME_CHARS):
            msg = "Only letters, digits, period and underscore characters are "\
                  "allowed in username"
            raise forms.ValidationError(msg)

        try:
            User.objects.get(username__exact = u_name)
            raise forms.ValidationError("Username already exists.")
        except User.DoesNotExist:
            return u_name

    def clean_password(self):
        pwd = self.cleaned_data['password']
        if pwd.strip(PWD_CHARS):
            raise forms.ValidationError("Only letters, digits and punctuation are \
                                         allowed in password")
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
    username = forms.CharField(max_length = 30)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput())

    def clean(self):
        super(UserLoginForm, self).clean()
        u_name, pwd = self.cleaned_data["username"], self.cleaned_data["password"]
        user = authenticate(username = u_name, password = pwd)

        if not user:
            raise forms.ValidationError("Invalid username/password")

        return user

