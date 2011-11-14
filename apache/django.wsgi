import os
from os.path import dirname, abspath
import sys

# This file is inside online_test/apache/django.wsgi
MY_DIR = abspath(dirname(dirname(dirname(__file__))))
if MY_DIR not in sys.path:
    sys.path.append(MY_DIR)
    
os.environ['DJANGO_SETTINGS_MODULE'] = 'online_test.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()