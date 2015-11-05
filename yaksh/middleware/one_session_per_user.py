from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from yaksh.models import Visitor


class OneSessionPerUserMiddleware(object):
    def process_request(self, request):
        if isinstance(request.user, User):
            current_key = request.session.session_key
            if hasattr(request.user, 'visitor'):
                active_key = request.user.visitor.session_key
                print active_key, current_key
                if active_key != current_key:
                    Session.objects.filter(session_key=active_key).delete()
                    request.user.visitor.session_key = current_key
                    request.user.visitor.save()
            else:
                Visitor.objects.create(
                    visitor_user=request.user,
                    session_key=current_key,
                )