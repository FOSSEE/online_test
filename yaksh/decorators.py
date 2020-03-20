from django.shortcuts import render
from django.conf import settings

# Local imports
from yaksh.forms import ProfileForm


def user_has_profile(user):
    return hasattr(user, 'profile')


def has_profile(func):
    """
    This decorator is used to check if the user account has a profile.
    If the user does not have a profile then redirect the user to
    profile edit page.
    """

    def _wrapped_view(request, *args, **kwargs):
        if user_has_profile(request.user):
            return func(request, *args, **kwargs)
        if request.user.groups.filter(name='moderator').exists():
            template = 'manage.html'
        else:
            template = 'user.html'
        form = ProfileForm(user=request.user, instance=None)
        context = {'template': template, 'form': form}
        return render(request, 'yaksh/editprofile.html', context)
    return _wrapped_view


def email_verified(func):
    """
    This decorator is used to check if email is verified.
    If email is not verified then redirect user for email
    verification.
    """

    def is_email_verified(request, *args, **kwargs):
        user = request.user
        context = {}
        if not settings.IS_DEVELOPMENT:
            if user.is_authenticated and user_has_profile(user):
                if not user.profile.is_email_verified:
                    context['success'] = False
                    context['msg'] = "Your account is not verified. \
                                        Please verify your account"
                    return render(
                        request, 'yaksh/activation_status.html', context
                    )
        return func(request, *args, **kwargs)
    return is_email_verified
