from notifications_plugin.models import Notification

class NotificationMiddleware(object):
    """ Middleware to get user's notifications """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        user = request.user
        if user.is_authenticated:
            notifications = Notification.objects.get_unread_receiver_notifications(
                user.id
            ).count()
            request.custom_notifications = notifications
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response
