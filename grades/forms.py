from grades.models import GradingSystem
from django import forms


class GradingSystemForm(forms.ModelForm):
    class Meta:
        model = GradingSystem
        fields = ['name', 'description']
