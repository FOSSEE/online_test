# Restframework Imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from rest_framework.exceptions import APIException
from rest_framework import permissions
from rest_framework import generics, status


# Django Imports
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from yaksh.courses import serializers


# Local Imports
from yaksh.courses.models import (
    Course, Module, Lesson, Enrollment, CourseTeacher, Unit,
    TableOfContent, Enrollment, CourseTeacher, Quiz, CourseStatus
)
from yaksh.courses.serializers import (
    CourseProgressSerializer, CourseSerializer, ModuleSerializer, LessonSerializer, TopicSerializer,
    TOCSerializer, QuestionSerializer, EnrollmentSerializer,
    CourseTeacherSerializer, UserSerializer, QuizSerializer
)
from yaksh.models import User
from yaksh.send_emails import send_bulk_mail


class BasePagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 1000


class CoursePermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="moderator").exists()

    def has_object_permission(self, request, view, obj):

        # check if user is owner
        return request.user == obj.owner



class ModeratorDashboard(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    
    def get_queryset(self):
        user = self.request.user
        course_as_ta = CourseTeacher.objects.filter(
            teacher_id=user.id
        ).values_list("course_id", flat=True)
        courses = Course.objects.filter(
            Q(owner_id=user.id) | Q(id__in=course_as_ta),
            is_trial=False
        ).distinct().order_by('-active')
        return courses



class CourseDetail(APIView):
    def get_object(self, pk, user_id):
        course = get_object_or_404(Course, pk=pk)
        if not course.is_valid_user(user_id):
            raise APIException(f"You are not allowed to view {course.name}")
        else:
            return course

    def get(self, request, pk, format=None):
        course = self.get_object(pk, request.user.id)
        self.check_permissions(request)
        self.check_object_permissions(request, course)
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
    def get_object(self, course_id, pk):
        module = get_object_or_404(Module, pk=pk, course_id=course_id)
        return module

    def get(self, request, course_id, pk, format=None):
        module = self.get_object(course_id, pk)
        serializer = ModuleSerializer(module)
        return Response(serializer.data)

    def post(self, request, course_id, format=None):
        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, course_id, pk, format=None):
        module = self.get_object(course_id, pk)
        serializer = ModuleSerializer(module, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, pk, format=None):
        module = self.get_object(course_id, pk)
        module.active = False
        module.save()
        serializer = ModuleSerializer(module)
        return Response(serializer.data)


class ModuleListDetail(APIView):
    def get(self, request, course_id, format=None):
        course = get_object_or_404(Course, pk=course_id)
        modules = course.get_modules()
        serializer = ModuleSerializer(
            modules, many=True, context={"request": request}
        )
        return Response(serializer.data)


class UnitListDetail(APIView):
    def get_object(self, module_id):
        module = get_object_or_404(Module, pk=module_id)
        return module

    def post(self, request, module_id, format=None):
        module = self.get_object(module_id)
        units = request.data.get("units")
        if units:
            unit_bulk_update = []
            for u in units:
                unit = get_object_or_404(Unit, id=u.get("unit_id"))
                unit.order = u.get("order")
                unit_bulk_update.append(unit)
            Unit.objects.bulk_update(unit_bulk_update, ["order"])
            message = "Units updated successfully"
            success = True
        else:
            message = "No units found"
            success = False
        response = {"message": message, "success": success}
        return Response(response, status.HTTP_200_OK)


class LessonDetail(APIView):
    def get_object(self, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        return lesson

    def get_module_object(self, pk):
        module = get_object_or_404(Module, pk=pk)
        return module

    def get(self, request, module_id, pk, format=None):
        lesson = self.get_object(pk)
        serializer = LessonSerializer(
            lesson, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request, module_id, format=None):
        data = request.data
        serializer = LessonSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            ct = ContentType.objects.get_for_model(instance)
            unit = Unit.objects.create(
                module_id=data.get("module_id"),
                order=data.get("order"), content_type=ct,
                object_id=instance.id
            )
            serialized_data = serializer.data
            serialized_data['order'] = data['order']
            serialized_data['type'] = "Lesson"
            serialized_data['unit_id'] = unit.id
            return Response(serialized_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, module_id, pk, format=None):
        data = request.data
        lesson = self.get_object(pk)
        serializer = LessonSerializer(
            lesson, data=data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            serialized_data = serializer.data
            serialized_data['order'] = data['order']
            serialized_data['type'] = "Lesson"
            serialized_data['unit_id'] = data['unit_id']
            return Response(serialized_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, module_id, pk, format=None):
        lesson = self.get_object(pk)
        lesson.active = False
        lesson.save()
        serializer = LessonSerializer(
            lesson, context={"request": request}
        )
        return Response(serializer.data)


class TocDetail(APIView):
    def get_object(self, pk):
        toc = get_object_or_404(TableOfContent, pk=pk)
        return toc

    def get_tocs(self, lesson_id):
        tocs = TableOfContent.objects.filter(lesson_id=lesson_id)
        serializer = TOCSerializer(tocs, many=True)
        return serializer.data

    def get(self, request, lesson_id, pk, format=None):
        toc = self.get_object(pk)
        if toc.content == 1:
            serializer = TopicSerializer(toc.content_object)
        else:
            serializer = QuestionSerializer(toc.content_object)
        serialized_data = serializer.data
        serialized_data["toc_id"] = toc.id
        serialized_data["time"] = toc.time
        serialized_data["ctype"] = toc.content
        return Response(serialized_data)

    def post(self, request, lesson_id, format=None):
        data = request.data
        if data.get("ctype") == 1:
            serializer = TopicSerializer(data=data)
        else:
            serializer = QuestionSerializer(data=data)
        if serializer.is_valid():
            instance = serializer.save()
            ct = ContentType.objects.get_for_model(instance)
            TableOfContent.objects.create(
                lesson_id=lesson_id, content=data.get("ctype"),
                time=data.get("time"), content_type=ct, object_id=instance.id
            )
            serialized_data = self.get_tocs(lesson_id)
            return Response(serialized_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, lesson_id, pk, format=None):
        data = request.data
        toc = self.get_object(pk)
        if data.get("ctype") == 1:
            serializer = TopicSerializer(toc.content_object, data=data)
        else:
            serializer = QuestionSerializer(toc.content_object, data=data)
        if serializer.is_valid():
            serializer.save()
            toc.time = data.get("time")
            toc.save()
            serialized_data = self.get_tocs(lesson_id)
            return Response(serialized_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, lesson_id, pk, format=None):
        toc = self.get_object(pk)
        if toc.content != 1:
            toc.content_object.test_cases.all().delete()
        toc.content_object.delete()
        serialized_data = self.get_tocs(lesson_id)
        return Response(serialized_data, status=status.HTTP_200_OK)


class TocListDetail(APIView):
    def get(self, request, lesson_id, format=None):
        toc = TableOfContent.objects.filter(lesson_id=lesson_id)
        serializer = TOCSerializer(toc, many=True)
        return Response(serializer.data)


class CourseEnrollmentDetail(APIView):
    def get_object(self, course_id, user_id):
        course = get_object_or_404(Course, id=course_id)
        if not course.is_valid_user(user_id):
            raise APIException(f"You are not allowed to view {course.name}")
        else:
            return course

    def get(self, request, course_id, format=None):
        user = request.user
        enrollment_status = request.query_params.get("status")
        course = self.get_object(course_id, user.id)
        enrollments = Enrollment.objects.select_related(
            "student", "course", "student__profile").filter(course_id=course_id)
        if enrollment_status:
            enrollments = enrollments.filter(status=enrollment_status)
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    def post(self, request, course_id, format=None):
        user = request.user
        students = request.data.get("students")
        status = request.data.get("status")
        if students:
            enrollment_bulk_update = []
            for u in students:
                enrollment = get_object_or_404(Enrollment, id=u)
                enrollment.status = status
                enrollment_bulk_update.append(enrollment)
            Enrollment.objects.bulk_update(enrollment_bulk_update, ["status"])
        course = self.get_object(course_id, user.id)
        enrollments = Enrollment.objects.filter(course_id=course_id)
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)


class CourseTeacherDetail(APIView):
    def get_object(self, course_id, user_id):
        course = get_object_or_404(Course, id=course_id)
        if not course.is_valid_user(user_id):
            raise APIException(f"You are not allowed to view {course.name}")
        else:
            return course

    def get(self, request, course_id, format=None):
        user = request.user
        course = self.get_object(course_id, user.id)
        courseteachers = CourseTeacher.objects.filter(course_id=course_id)
        serializer = CourseTeacherSerializer(courseteachers, many=True)
        return Response(serializer.data)

    def post(self, request, course_id, format=None):
        user = request.user
        course = self.get_object(course_id, user.id)
        data = request.data
        if data.get("action") == "delete":
            CourseTeacher.objects.deleteUsers(
                data.get("users"), course_id
            )
        elif data.get("action") == 'search':
            search_by = data.get('search_by', "username")
            u_name = data.get("u_name")
            users = CourseTeacher.objects.searchUsers(
                search_by, u_name, user.id, course_id
            )
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        else:
            CourseTeacher.objects.addUsers(
                data.get("users"), course_id
            )

        courseteachers = CourseTeacher.objects.filter(course_id=course_id)
        serializer = CourseTeacherSerializer(courseteachers, many=True)
        return Response(serializer.data)


class CourseSendMail(APIView):
    def get_object(self, course_id, user_id):
        course = get_object_or_404(Course, id=course_id)
        if not course.is_valid_user(user_id):
            raise APIException(f"You are not allowed to view {course.name}")
        else:
            return course

    def post(self, request, course_id, format=None):
        user = request.user
        course = self.get_object(course_id, user.id)
        user_ids = request.data.get("students")
        subject = request.data.get("subject")
        body = request.data.get("body")
        students = User.objects.filter(id__in=user_ids).values_list("email", flat=True)
        message = send_bulk_mail(subject, body, students, None)
        return Response({"message": message})


class CourseProgressDetail(APIView):

    def get_objects(self, course_id):
        course_status = CourseStatus.objects.filter(course_id=course_id)
        return course_status

    def get(self, request, course_id, format=None):
        course_status = self.get_objects(course_id)
        serializer = CourseProgressSerializer(course_status, many=True)
        return Response(serializer.data)


class QuizDetail(APIView):
    def get_object(self, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        return quiz

    def get_module_object(self, pk):
        module = get_object_or_404(Module, pk=pk)
        return module

    def get(self, request, module_id, pk, format=None):
        quiz = self.get_object(pk)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    def post(self, request, module_id=None, format=None):
        data = request.data
        serializer = QuizSerializer(data=data)
        if serializer.is_valid():
            instance = serializer.save()
            ct = ContentType.objects.get_for_model(instance)
            unit = Unit.objects.create(
                module_id=module_id,
                order=data.get("order"), content_type=ct,
                object_id=instance.id
            )
            serialized_data = serializer.data
            serialized_data['order'] = data['order']
            serialized_data['type'] = "Quiz"
            serialized_data['unit_id'] = unit.id
            return Response(serialized_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, module_id, pk, format=None):
        data = request.data
        quiz = self.get_object(pk)
        serializer = QuizSerializer(quiz, data=data)
        if serializer.is_valid():
            serializer.save()
            serialized_data = serializer.data
            serialized_data['order'] = data['order']
            serialized_data['type'] = "Quiz"
            serialized_data['unit_id'] = data['unit_id']
            return Response(serialized_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, module_id, pk, format=None):
        quiz = self.get_object(pk)
        quiz.active = False
        quiz.save()
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)
