# Local imports
try:
    from string import letters
except ImportError:
    from string import ascii_letters as letters
from string import digits, punctuation
# Local imports
import hashlib
from random import randint
from textwrap import dedent

# Django imports
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings

def generate_activation_key(username):
    """ Generate hashed secret key for email activation """
    chars = letters + digits + punctuation
    secret_key = get_random_string(randint(10, 40), chars)
    return hashlib.sha256((secret_key + username).encode('utf-8')).hexdigest()

def send_user_mail(user_mail, key):
    """ Send mail to user whose email is to be verified
        This function should get two args i.e user_email and secret_key.
        The activation url is generated from settings.PRODUCTION_URL and key.
    """
    try:
        to = user_mail
        subject = "Yaksh Email Verification"
        msg = dedent("""\
                To activate your account and verify your email address,
                please click the following link:
                {0}/exam/activate/{1}
                If clicking the link above does not work,
                copy and paste the URL in a new browser window instead.
                For any issue, please write us on {2}

                Regards
                Yaksh Team
            """.format(settings.PRODUCTION_URL, key, settings.REPLY_EMAIL)
            )

        send_mail(subject, msg, settings.SENDER_EMAIL, [to])
        msg = "An activation link is sent to your registered email.\
                        Please activate the link within 20 minutes."
        success = True
    except Exception as exc_msg:
        msg = """Error: {0}. Please check your email address.\
                If email address is correct then
                Please contact your \
                instructor/administrator.""".format(exc_msg)
        success = False

    return success, msg
