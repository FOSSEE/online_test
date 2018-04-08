"""
settings for yaksh app.
"""

from decouple import config
import os
from django.conf import settings

# The directory where user data can be saved.  This directory will be
# world-writable and all user code will be written and saved here by the
# code server with each user having their own sub-directory.
OUTPUT_DIR = os.path.join(settings.BASE_DIR, "yaksh_data", "output")

YAKSH_MEDIA_ROOT = settings.MEDIA_ROOT

# Set this variable to <False> once the project is in production.
# If this variable is kept <True> in production, email will not be verified.
IS_DEVELOPMENT = config('IS_DEVELOPMENT', default=True, cast=bool)

YAKSH_BASE_DIR = os.path.dirname(os.path.dirname(__file__))

FIXTURES_DIR_PATH = os.path.join(YAKSH_BASE_DIR, 'yaksh', 'fixtures')

# The root of the URL, for example you might be in the situation where you
# are not hosted as host.org/exam/  but as host.org/foo/exam/ for whatever
# reason set this to the root you have to serve at.  In the above example
# host.org/foo/exam set URL_ROOT='/foo'
URL_ROOT = config('URL_ROOT', default='', cast=str)

