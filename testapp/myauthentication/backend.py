import hashlib
from django.contrib.auth.models import User, check_password
from models_spoken import MdlUser

class MyBackend:
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        try:
            user = MdlUser.objects.get(username=username)
            pwd = user.password
            uid = user.id
            firstname = user.firstname
            lastname = user.lastname
            email = user.email
            p = hashlib.md5(password)
	    pwd_valid =  (pwd == p.hexdigest())
            if user and pwd_valid:
                 try:
                     print "here"
                     user = User.objects.get(username=username)
                     print "hh"
                     return user
                 except Exception, e:
                     user=User(id=uid, username=username, password=pwd, first_name=firstname, last_name=lastname, email=email)
                     user.save()
                     return user
        except Exception, e:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except Exception, e:
            return None
