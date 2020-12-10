# Django Imports
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404

# Local Imports
from stats.models import TrackLesson, LessonLog, str_to_time, time_to_seconds
from yaksh.models import Course
from yaksh.decorators import email_verified


@login_required
@email_verified
def add_tracker(request, tracker_id):
    user = request.user
    track = get_object_or_404(
        TrackLesson.objects.select_related("course"), id=tracker_id
    )
    if not track.course.is_student(user):
        raise Http404("You are not enrolled in this course")
    context = {}
    video_duration = request.POST.get('video_duration')
    current_time = request.POST.get('current_video_time')
    if current_time:
        track.set_current_time(current_time)
        track.video_duration = video_duration
        track.save()
        if not track.watched:
            track.set_watched()
            track.save()
        LessonLog.objects.create(
            track_id=track.id, current_time=current_time,
            last_access_time=timezone.now()
        )
        success = True
    else:
        success = False
    context = {"success": success}
    return JsonResponse(context)


@login_required
@email_verified
def view_lesson_watch_stats(request, course_id, lesson_id):
    user = request.user
    course = get_object_or_404(
        Course.objects.prefetch_related("students"), id=course_id
    )
    if not course.is_creator(user) and not course.is_teacher(user):
        raise Http404('This course does not belong to you')
    trackings = TrackLesson.objects.get_queryset().filter(
        course_id=course_id, lesson_id=lesson_id
    ).order_by("id")
    percentage_data = TrackLesson.objects.get_percentage_data(trackings)
    visited = trackings.count()
    completed = trackings.filter(watched=True).count()
    students_total = course.students.count()
    paginator = Paginator(trackings, 30)
    page = request.GET.get('page')
    trackings = paginator.get_page(page)
    context = {
        'objects': trackings, 'total': visited, 'course_id': course_id,
        'lesson_id': lesson_id, "percentage_data": percentage_data,
        'completion': [completed, students_total-completed, students_total],
        'visits': [visited, students_total-visited, students_total]
    }
    return render(request, 'view_lesson_tracking.html', context)
