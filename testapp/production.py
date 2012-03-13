from testapp.settings import *

DEBUG=False
TEMPLATE_DEBUG=DEBUG


DATABASES["default"]["ENGINE"] = 'django.db.backends.mysql'
DATABASES["default"]["NAME"] = 'online_test'
DATABASES["default"]["USER"] = 'online_test_user'

from testapp.local import DATABASE_PASSWORD
# Imports DATABASE_PASSWORD from testapp/local.py that is not part of git repo
DATABASES["default"]["PASSWORD"] = DATABASE_PASSWORD

