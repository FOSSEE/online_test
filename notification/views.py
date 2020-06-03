from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages


from yaksh.models import Course
from .models import Subscription


def toggle_subscription_status(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')

    ct = ContentType.objects.get_for_model(course)
    course_sub = Subscription.objects.get(
        target_ct=ct, user=user, target_id=course.id
    )

    if course_sub.subscribe:
        course_sub.subscribe = False
        message = 'Unsubscribed from the course mail letter.'
    else:
        course_sub.subscribe = True
        message = 'Subscribed to the course mail letter.'
    course_sub.save()
    messages.info(request, message)

    return redirect('yaksh:course_modules', course_id)