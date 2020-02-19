from grades.models import GradingSystem, GradeRange
from django import forms


class GradingSystemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(GradingSystemForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update(
            {'class': "form-control", 'placeholder': 'Grading Name'}
        )
        self.fields['description'].widget.attrs.update(
            {'class': "form-control",
             'placeholder': 'Grading description'}
        )
    class Meta:
        model = GradingSystem
        fields = ['name', 'description']


class GradeRangeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GradeRangeForm, self).__init__(*args, **kwargs)
        self.fields['lower_limit'].widget.attrs.update(
            {'class': "form-control", 'placeholder': 'Lower limit'}
        )
        self.fields['upper_limit'].widget.attrs.update(
            {'class': "form-control", 'placeholder': 'Upper limit'}
        )
        self.fields['grade'].widget.attrs.update(
            {'class': "form-control", 'placeholder': 'Grade'}
        )
        self.fields['description'].widget.attrs.update(
            {'class': "form-control",
             'placeholder': 'Description'}
        )

    class Meta:
        model = GradeRange
        fields = "__all__"
