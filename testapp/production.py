from project.settings import *

DEBUG=False
TEMPLATE_DEBUG=DEBUG

DATABASE_ENGINE = 'django.db.backends.mysql'
DATABASE_NAME = 'online_test'
DATABASE_USER = 'online_test_user'
# Imports DATABASE_PASSWORD from testapp/local.py that is not part of git repo
from testapp.local import DATABASE_PASSWORD