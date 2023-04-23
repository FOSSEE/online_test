from django.contrib.contenttypes.models import ContentType

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated

from forum.models import Post, Comment
from yaksh.models import Course, Lesson
from .serializers import PostSerializer, CommentSerializer
from .permissions import IsAuthorOrReadOnly


class CoursePostList(generics.ListCreateAPIView):

    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_course(self, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return course

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = self.get_course(course_id)
        course_ct = ContentType.objects.get_for_model(course)
        posts = Post.objects.filter(target_ct=course_ct,
                                    target_id=course.id,
                                    active=True)
        return posts


class CoursePostDetail(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = PostSerializer

    def get_object(self):
        try:
            post = Post.objects.get(id=self.kwargs['post_id'])
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return post

    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'PUT' \
            or self.request.method == 'DELETE' \
                or self.request.method == 'PATCH':
            permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

        return [permission() for permission in permission_classes]


class CoursePostComments(generics.ListCreateAPIView):

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            post = Post.objects.get(id=self.kwargs['post_id'])
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        comments = post.comments.filter(active=True)
        return comments


class CoursePostCommentDetail(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = CommentSerializer

    def get_object(self):
        try:
            comment = Comment.objects.get(id=self.kwargs['comment_id'])
        except Comment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return comment

    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'PUT' \
            or self.request.method == 'DELETE' \
                or self.request.method == 'PATCH':
            permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

        return [permission() for permission in permission_classes]


class LessonPostDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer

    def get_object(self):
        lesson_id = self.kwargs['lesson_id']
        lesson = Lesson.objects.get(id=lesson_id)
        lesson_ct = ContentType.objects.get_for_model(lesson)
        try:
            post = Post.objects.get(
                target_ct=lesson_ct, target_id=lesson_id,
                active=True, title=lesson.name
            )
        except Post.DoesNotExist:
            post = Post.objects.create(
                target_ct=lesson_ct, target_id=lesson_id,
                active=True, title=lesson.name, creator=self.request.user,
                description=f'Discussion on {lesson.name} lesson',
            )

        return post

    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'PUT' \
            or self.request.method == 'DELETE' \
                or self.request.method == 'PATCH':
            permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

        return [permission() for permission in permission_classes]


class LessonPostComments(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            post = Post.objects.get(id=self.kwargs['post_id'])
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        comments = post.comments.filter(active=True)
        return comments


class LessonPostCommentDetail(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = CommentSerializer

    def get_object(self):
        try:
            comment = Comment.objects.get(id=self.kwargs['comment_id'])
        except Comment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return comment

    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'PUT' \
            or self.request.method == 'DELETE' \
                or self.request.method == 'PATCH':
            permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

        return [permission() for permission in permission_classes]
