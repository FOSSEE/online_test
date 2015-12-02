from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from yaksh.models import ConcurrentUser


class OneSessionPerUserMiddleware(object):
    def process_request(self, request):
        if isinstance(request.user, User):
            current_key = request.session.session_key
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