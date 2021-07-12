from django.contrib.contenttypes.models import ContentType

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from forum.models import Post
from yaksh.models import Course, Lesson
from .serializers import PostSerializer


@api_view(['GET'])
def course_post_list(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        course_ct = ContentType.objects.get_for_model(course)
        posts = Post.objects.filter(target_ct=course_ct,
                                    target_id=course.id,
                                    active=True)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def course_post_detail(request, course_id, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        post_serializer = PostSerializer(post)
        return Response(post_serializer.data)


@api_view(['GET'])
def lesson_post_list(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        course_ct = ContentType.objects.get_for_model(course)
        lesson_posts = course.get_lesson_posts()
        serializer = PostSerializer(lesson_posts, many=True)
        return Response(serializer.data)