from django.shortcuts import redirect

from .settings import URL_ROOT


def index(request):
    return redirect('{0}/exam/'.format(URL_ROOT))
