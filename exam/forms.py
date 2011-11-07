from django import forms
from exam.models import Profile

class UserRegisterForm(forms.ModelForm):

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    roll_number = forms.CharField(max_length=30)
    #email_address = forms.EmailField()
    #password = forms.CharField(max_length=30, widget=forms.PasswordInput())

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'roll_number']

