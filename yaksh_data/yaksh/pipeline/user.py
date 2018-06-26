from yaksh.models import Profile


def save_profile(backend, user, response, *args, **kwargs):
    if not hasattr(user, 'profile'):
        profile = Profile.objects.create(user=user)
        profile.roll_number = profile.id
    else:
        profile = Profile.objects.get(user=user)
    profile.is_email_verified = True
    profile.save()
