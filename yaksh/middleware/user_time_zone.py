import pytz

from django.utils import timezone


class TimezoneMiddleware(object):
    """ Middleware to get user's timezone and activate timezone 
        if user timezone is not available default value 'UTC' is activated """
    def process_request(self, request):
        user = request.user
        if hasattr(user, 'profile'):
       	    user_tz = user.profile.timezone
            timezone.activate(pytz.timezone(user_tz))
        else:
            timezone.activate(pytz.timezone('UTC'))
