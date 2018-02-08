from grades.models import GradingSystem
from django import forms

class GradingSystemForm(forms.ModelForm):
    def __init__(self, *args, ** kwargs):
        super(GradingSystemForm, self).__init__(*args, **kwargs)
        system = getattr(self, 'instance', None)
        if system.name == 'default':
            self.fields['name'].widget.attrs['readonly'] = True

    class Meta:
        model = GradingSystem
        fields = ['name', 'description', 'can_be_used']
