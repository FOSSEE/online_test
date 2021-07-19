from django.contrib.contenttypes.models import ContentType

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics

from forum.models import Post, Comment
from yaksh.models import Course, Lesson
from .serializers import PostSerializer, CommentSerializer


@api_view(['GET', 'POST'])
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

    elif request.method == 'POST':
        data = request.data
        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            course_id = serializer.validated_data.get("target_id")
            course = Course.objects.get(id=course_id)
            serializer.validated_data['target'] = course
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostComments(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


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