from collections import OrderedDict

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, generics, pagination
from rest_framework.permissions import IsAuthenticated

from forum.models import Post, Comment
from yaksh.courses.models import Course, Lesson
from .serializers import PostSerializer, CommentSerializer
from .permissions import IsAuthorOrReadOnly


class PostListPagination(pagination.PageNumberPagination):
    page_size = 20

class CoursePostList(generics.ListCreateAPIView):

    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostListPagination

    def get_course(self, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return course

    def get_queryset(self):
        search = None
        if 'search' in self.kwargs:
            search = self.kwargs['search']
        course_id = self.kwargs['course_id']
        course = self.get_course(course_id)
        course_ct = ContentType.objects.get_for_model(course)

        if search:
            posts = Post.objects.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search),
                target_ct=course_ct,
                target_id=course.id,
                active=True,
            ).order_by('-modified_at')
        else:
            posts = Post.objects.filter(target_ct=course_ct,
                                        target_id=course.id,
                                        active=True).order_by('-modified_at')
        return posts

    def create(self, request, *args, **kwargs):
        data = OrderedDict()
        data.update(request.data)
        creator = request.user
        course_id = self.kwargs['course_id']
        course = self.get_course(course_id)
        course_ct = ContentType.objects.get_for_model(course)
        data['target_id'] = course_id
        data['target_ct'] = course_ct.id
        data['target'] = course
        data['creator'] = creator.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


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

    def create(self, request, *args, **kwargs):
        data = request.data
        data['post_field'] = self.kwargs['post_id']
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

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
