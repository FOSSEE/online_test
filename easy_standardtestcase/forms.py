from django import forms

from .models import easy_standardtestcase

class easy_standardtestcaseForm(forms.ModelForm):

    class Meta:
        model = easy_standardtestcase
        fields = ('lang','function','typeval', 'inputVals','operator','output',)