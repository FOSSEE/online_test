from yaksh.models import Profile
#from django.contrib.auth.models import User

def save_profile(backend, user, response, *args, **kwargs):
    if not hasattr(user, 'profile'):
        profile = Profile.objects.create(user=user)
        profile.roll_number = profile.id
        profile.save()
