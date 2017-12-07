from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from yaksh.models import ConcurrentUser


class OneSessionPerUserMiddleware(object):
    """
    Middleware to handle multiple logins with same credentials
        - Creates a Database entry to record the current user and active session key
        - Checks if the current user has already been logged in. If True, the new session
          key is stored with respect to the user and the old session key is deleted,
          effectively terminating the older session for the same user.
        - The concurrentuser attribute of the User model refers to the ConcurrentUser
          model object and not the concurrent_user field due to behaviour described 
          in the Documentation
          Link: https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#extending-the-existing-user-model)
    """
    def process_request(self, request):
        if isinstance(request.user, User):
            current_key = request.session.session_key
            # 
            # Documentation: 
            # https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#extending-the-existing-user-model
            if hasattr(request.user, 'concurrentuser'):
                active_key = request.user.concurrentuser.session_key
                if active_key != current_key:
                    Session.objects.filter(session_key=active_key).delete()
                    request.user.concurrentuser.session_key = current_key
                    request.user.concurrentuser.save()
            else:
                ConcurrentUser.objects.create(
                    concurrent_user=request.user,
                    session_key=current_key,
                )