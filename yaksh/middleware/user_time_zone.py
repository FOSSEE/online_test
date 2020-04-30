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
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        user = request.user
        user_tz = 'Asia/Kolkata'
        if hasattr(user, 'profile'):
            if user.profile.timezone:
                user_tz = user.profile.timezone
        timezone.activate(pytz.timezone(user_tz))

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response
