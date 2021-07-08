# Restframework Imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes
)
from rest_framework.exceptions import APIException

# Django Imports
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.db.models import Q

# Local Imports
from yaksh.courses.models import (
    Course, Module, Lesson, Enrollment, CourseTeacher
)
from yaksh.courses.serializers import (
    CourseSerializer, ModuleSerializer, LessonSerializer
)


class BasePagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 1000


def index(request):
    return render(request, 'courses.html')


def index2(request):
    return render(request, 'course_detail.html')


class CourseDetail(APIView):
    def get_object(self, pk, user_id):
        course = get_object_or_404(Course, pk=pk)
        if not course.is_valid_user(user_id):
            raise APIException(f"You are not allowed to view {course.name}")
        else:
            return course

    def get(self, request, pk, format=None):
        course = self.get_object(pk, request.user.id)
        serializer = CourseSerializer(
            course, context={"user_id": request.user.id}
        )
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CourseSerializer(
            data=request.data, context={"user_id": request.user.id}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        course = self.get_object(pk, request.user.id)
        serializer = CourseSerializer(
            course, data=request.data, context={"user_id": request.user.id}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        course = self.get_object(pk, request.user.id)
        course.active = False
        course.save()
        serializer = CourseSerializer(
            course, context={"user_id": request.user.id}
        )
        return Response(serializer.data)


class CourseListDetail(APIView, BasePagination):

    def get_objects(self, user_id):
        course_as_ta = list(CourseTeacher.objects.filter(
            teacher_id=user_id).values_list("course_id", flat=True)
        )
        courses = Course.objects.filter(
            Q(owner_id=user_id)|Q(id__in=course_as_ta)
        ).order_by("active").distinct()
        return courses

    def get(self, request, *args, **Kwargs):
        tags = request.query_params.get("name")
        status = request.query_params.get("active")
        courses = self.get_objects(request.user.id)
        if status == 'select' and tags:
            courses = courses.filter(
                name__icontains=tags)
        elif status == 'active':
            courses = courses.filter(
                name__icontains=tags, active=True)
        elif status == 'closed':
            courses = courses.filter(
                name__icontains=tags, active=False)
        page = self.paginate_queryset(courses, request)
        serializer = CourseSerializer(
            page, many=True, context={"user_id": request.user.id}
        )
        paginated = self.get_paginated_response(
            data=serializer.data
        )
        return Response(paginated.data)


class ModuleDetail(APIView):
    def get_object(self, pk):
        module = get_object_or_404(Module, pk=pk)
        return module

    def get(self, request, pk, format=None):
        module = self.get_object(pk)
        serializer = ModuleSerializer(module)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        module = self.get_object(pk)
        serializer = ModuleSerializer(module, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        module = self.get_object(pk)
        module.active = False
        module.save()
        serializer = ModuleSerializer(lesson)
        return Response(serializer.data)


class ModuleListDetail(APIView):
    def get(self, request, course_id, format=None):
        course = get_object_or_404(Course, pk=course_id)
        modules = course.get_modules()
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)


class LessonDetail(APIView):
    def get_object(self, pk, user_id):
        lesson = get_object_or_404(Lesson, pk=pk, owner_id=user_id)
        return lesson

    def get(self, request, pk, format=None):
        lesson = self.get_object(pk, request.user.id)
        serializer = LessonSerializer(
            lesson, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = LessonSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        lesson = self.get_object(pk, request.user.id)
        serializer = LessonSerializer(
            lesson, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        lesson = self.get_object(pk, request.user.id)
        lesson.active = False
        lesson.save()
        serializer = LessonSerializer(
            lesson, context={"request": request}
        )
        return Response(serializer.data)

