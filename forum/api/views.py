from django.contrib.contenttypes.models import ContentType

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics, viewsets

from forum.models import Post, Comment
from yaksh.models import Course, Lesson
from .serializers import PostSerializer, CommentSerializer


class CoursePostList(generics.ListCreateAPIView):

    serializer_class = PostSerializer

    def get_queryset(self):
        try:
            course = Course.objects.get(id=self.kwargs['course_id'])
        except Course.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        course_ct = ContentType.objects.get_for_model(course)
        posts = Post.objects.filter(target_ct=course_ct,
                                    target_id=course.id,
                                    active=True)
        return posts


class PostComments(generics.ListCreateAPIView):

    serializer_class = CommentSerializer

    def get_queryset(self):
        try:
            post = Post.objects.get(id=self.kwargs['post_id'])
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        comments = post.comments.filter(active=True)
        return comments


class LessonPostList(generics.ListCreateAPIView):

    serializer_class = PostSerializer

    def get_queryset(self):
        try:
            course = Course.objects.get(id=self.kwargs['course_id'])
        except Course.DoesNotExists:
            return Response(status=status.HTTP_404_NOT_FOUND)
        course_ct = ContentType.objects.get_for_model(course)
        lesson_posts = course.get_lesson_posts()
        return lesson_posts

    def get_serializer_context(self):
        context = super(LessonPostList, self).get_serializer_context()
        context.update({
            'lesson': 'lesson'
        })
        return context