import os

from django import forms
from django.contrib.auth.models import User

from certificates.models import Certificate, get_cert_template_dir
from certificates.formatters.utils import HTMLFormatter, render_certificate_template
from certificates.settings import CERTIFICATE_FILE_NAME

class CertificateForm(forms.ModelForm):
    """ Certificate form for moderators """

    def save(self, commit=True, *args, **kwargs):
        instance = super(CertificateForm, self).save(commit=False)

        if instance.html:
            formatter = HTMLFormatter(instance.html)
            _dir = get_cert_template_dir(instance)
            if not os.path.exists(_dir):
                os.makedirs(_dir)

            f_path = os.sep.join(
                (get_cert_template_dir(instance), CERTIFICATE_FILE_NAME)
            )
            with open(f_path, 'w') as f:
                f.write(formatter.get_response())

        if commit:
            instance.save()

        return instance


    class Meta:
        model = Certificate
        fields = ['html', 'active', 'static_files']
