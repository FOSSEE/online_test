import pytz

from django.utils import timezone


class TimezoneMiddleware(object):
    """ Middleware to get user's timezone and activate timezone
        if user timezone is not available default value 'Asia/Kolkata'
        is activated
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_request(self, request):
        user = request.user
        user_tz = 'Asia/Kolkata'
        if hasattr(user, 'profile'):
            if user.profile.timezone:
                user_tz = user.profile.timezone
        timezone.activate(pytz.timezone(user_tz))
