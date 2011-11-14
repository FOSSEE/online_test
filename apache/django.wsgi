import os
from os.path import dirname, abspath
import sys

# This file is inside online_test/apache/django.wsgi
# pth should be online_test
pth = abspath(dirname(dirname(__file__)))
if pth not in sys.path:
    sys.path.append(pth)
# Now add the parent of online_test also.
pth = dirname(pth)
if pth not in sys.path:
    sys.path.append(pth)
    
os.environ['DJANGO_SETTINGS_MODULE'] = 'online_test.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
