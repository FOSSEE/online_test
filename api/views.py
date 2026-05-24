# ----------------------------
# IMPORTS
# ----------------------------
from django.http import Http404, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
import tempfile
import os
from zipfile import ZipFile
from io import BytesIO

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes
)
from yaksh.send_emails import send_bulk_mail

from rest_framework.parsers import MultiPartParser, FormParser

from yaksh.models import (
    Question, Quiz, QuestionPaper, QuestionSet,
    AnswerPaper, Course, Answer, Profile, CourseStatus,
    Badge, UserBadge, BadgeProgress, UserStats, UserActivity,
    DailyActivity, Lesson, LearningModule, LearningUnit, LessonFile,
    TestCase, McqTestCase, StdIOBasedTestCase, StandardTestCase,
    HookTestCase, IntegerTestCase, StringTestCase, FloatTestCase,
    ArrangeTestCase, FileUpload, AssignmentUpload, Course 
)
from yaksh.models import get_model_class
from yaksh.views import is_moderator, get_html_text, prof_manage, add_as_moderator, get_toc_contents, _get_questions, _get_questions_from_tags, _remove_already_present
from django.db.models import Q, Count, Avg, Sum, F, FloatField
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
from collections import defaultdict

from yaksh.code_server import get_result as get_result_from_code_server
from yaksh.settings import SERVER_POOL_PORT, SERVER_HOST_NAME

from api.serializers import (
    QuestionSerializer, QuizSerializer, QuestionPaperSerializer,
    QuestionPaperDetailSerializer, AnswerPaperSerializer, CourseSerializer, BadgeSerializer,
    UserBadgeSerializer, BadgeProgressSerializer, UserStatsSerializer,
    UserActivitySerializer, CourseProgressSerializer, CourseCatalogSerializer,
    LessonDetailSerializer, LearningModuleDetailSerializer, LearningUnitDetailSerializer, MinimalLearningUnitSerializer,
    SimpleUserSerializer, ProfileSerializer, AnswerDetailSerializer, AnswerPaperGradingSerializer, UserAttemptSerializer, GradeUpdateSerializer, GradingCourseSerializer,
    MonitorAnswerPaperSerializer, StudentDashboardCourseSerializer, CourseWithCompletionSerializer, QuestionSetSerializer, TagSerializer, ViewAnswerPaperResponseSerializer
)

from rest_framework import generics, permissions, status
from grades.models import GradingSystem
from .serializers import GradingSystemSerializer

from yaksh.forms import LessonForm, LessonFileForm, ExerciseForm
from yaksh.views import get_html_text, is_moderator, test_mode
from django.shortcuts import get_object_or_404
from yaksh.models import MicroManager
from yaksh.tasks import update_user_marks
from yaksh.file_utils import is_csv
from yaksh.models import Post, Comment, Course, Lesson, TableOfContents, Quiz, User, CourseStatus
from api.serializers import PostSerializer, CommentSerializer
from rest_framework import generics, permissions
from django.contrib.contenttypes.models import ContentType

from notifications_plugin.models import Notification
from api.serializers import NotificationSerializer
from django.db import transaction
from taggit.models import Tag  


import json
import os
import ruamel.yaml


def get_quiz_les_display_name(item):
    typ, obj_id = item
    if typ == "quiz":
        try:
            obj = Quiz.objects.get(id=obj_id)
            return f"{obj.description} (quiz)"
        except Quiz.DoesNotExist:
            return f"Quiz {obj_id} (quiz)"
    elif typ == "lesson":
        try:
            obj = Lesson.objects.get(id=obj_id)
            return f"{obj.name} (lesson)"
        except Lesson.DoesNotExist:
            return f"Lesson {obj_id} (lesson)"
    return ""

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user"""
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        roll_number = request.data.get('roll_number', '')
        institute = request.data.get('institute', '')
        department = request.data.get('department', '')
        position = request.data.get('position', '')
        timezone = request.data.get('timezone', 'Asia/Kolkata')

        # Required validation
        if not username or not email or not password or not first_name or not last_name:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name
        )

        # Create profile
        profile, created = Profile.objects.get_or_create(user=user)
        profile.roll_number = roll_number
        profile.institute = institute
        profile.department = department
        profile.position = position
        profile.timezone = timezone
        profile.save()

        token, created = Token.objects.get_or_create(user=user)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_moderator': profile.is_moderator,
                'roll_number': profile.roll_number,
                'institute': profile.institute,
                'department': profile.department,
                'position': profile.position,
                'timezone': profile.timezone,
                'bio': profile.bio,
                'phone': profile.phone,
                'city': profile.city,
                'country': profile.country,
                'linkedin': profile.linkedin,
                'github': profile.github,
                'display_name': profile.display_name,
            },
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': 'Registration failed', 'details': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_user(request):
    """User login endpoint"""
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password required'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'},
                            status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        profile, created = Profile.objects.get_or_create(user=user)

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_moderator': profile.is_moderator,
                'roll_number': profile.roll_number,
                'institute': profile.institute,
                'department': profile.department,
                'position': profile.position,
                'timezone': profile.timezone,
                'bio': profile.bio,
                'phone': profile.phone,
                'city': profile.city,
                'country': profile.country,
                'linkedin': profile.linkedin,
                'github': profile.github,
                'display_name': profile.display_name,
            },
            'token': token.key,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': 'Login failed', 'details': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    """Logout endpoint"""
    request.user.auth_token.delete()
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ----------------------------
# SOCIAL AUTH API (SPA Flow)
# ----------------------------
import urllib.parse
import requests as http_requests
from social_django.utils import load_strategy, load_backend
from django.conf import settings as django_settings


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_social_auth_url(request):
    """Return the OAuth authorization URL for a given provider.
    Query params: provider, redirect_uri
    """
    provider = request.GET.get('provider')
    redirect_uri = request.GET.get('redirect_uri', '')

    if not provider or not redirect_uri:
        return Response(
            {'error': 'provider and redirect_uri are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    encoded_redirect = urllib.parse.quote(redirect_uri, safe='')

    if provider == 'google-oauth2':
        client_id = django_settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
        if not client_id:
            return Response({'error': 'Google OAuth2 is not configured'}, status=400)
        url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={encoded_redirect}&"
            f"response_type=code&"
            f"scope=email%20profile&"
            f"access_type=offline&"
            f"state=google-oauth2"
        )
    elif provider == 'github':
        client_id = django_settings.SOCIAL_AUTH_GITHUB_KEY
        if not client_id:
            return Response({'error': 'GitHub OAuth is not configured'}, status=400)
        url = (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={encoded_redirect}&"
            f"scope=user:email&"
            f"state=github"
        )
    else:
        return Response({'error': f'Unsupported provider: {provider}'}, status=400)

    return Response({'url': url})


def _exchange_code_for_token(provider, code, redirect_uri):
    """Exchange an OAuth authorization code for an access token."""
    if provider == 'google-oauth2':
        resp = http_requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': django_settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'client_secret': django_settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
            timeout=10,
        )
    elif provider == 'github':
        resp = http_requests.post(
            'https://github.com/login/oauth/access_token',
            data={
                'code': code,
                'client_id': django_settings.SOCIAL_AUTH_GITHUB_KEY,
                'client_secret': django_settings.SOCIAL_AUTH_GITHUB_SECRET,
                'redirect_uri': redirect_uri,
            },
            headers={'Accept': 'application/json'},
            timeout=10,
        )
    else:
        raise ValueError(f'Unsupported provider: {provider}')

    data = resp.json()
    print(f"[Social Auth Debug] Provider: {provider}")
    print(f"[Social Auth Debug] redirect_uri sent: {redirect_uri}")
    print(f"[Social Auth Debug] Response status: {resp.status_code}")
    print(f"[Social Auth Debug] Response body: {data}")
    if 'error' in data:
        raise ValueError(data.get('error_description', data.get('error')))

    access_token = data.get('access_token')
    if not access_token:
        raise ValueError('No access_token in provider response')
    return access_token


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def social_login(request):
    """Exchange an OAuth authorization code for a DRF auth token.
    Body: { provider, code, redirect_uri }
    Returns: { user, token } (same format as login_user)
    """
    provider = request.data.get('provider')
    code = request.data.get('code')
    redirect_uri = request.data.get('redirect_uri')

    if not provider or not code or not redirect_uri:
        return Response(
            {'error': 'provider, code, and redirect_uri are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Step 1: Exchange authorization code for access token
    try:
        access_token = _exchange_code_for_token(provider, code, redirect_uri)
    except ValueError as e:
        return Response(
            {'error': f'Token exchange failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Step 2: Use social_core to authenticate / create user via pipeline
    try:
        strategy = load_strategy(request)
        backend = load_backend(strategy, provider, redirect_uri=redirect_uri)
        user = backend.do_auth(access_token)
    except Exception as e:
        return Response(
            {'error': f'Authentication failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user or not user.is_active:
        return Response(
            {'error': 'Authentication failed or user is inactive'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Step 3: Generate DRF token and return user data
    token, _ = Token.objects.get_or_create(user=user)
    profile, _ = Profile.objects.get_or_create(user=user)

    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_moderator': profile.is_moderator,
            'roll_number': profile.roll_number,
            'institute': profile.institute,
            'department': profile.department,
            'position': profile.position,
            'timezone': profile.timezone,
            'bio': profile.bio,
            'phone': profile.phone,
            'city': profile.city,
            'country': profile.country,
            'linkedin': profile.linkedin,
            'github': profile.github,
            'display_name': profile.display_name,
        },
        'token': token.key,
        'message': 'Social login successful'
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_moderator_status(request):
    """Get current moderator status (active/inactive)"""
    user = request.user
    
    try:
        group = Group.objects.get(name='moderator')
        is_moderator_active = group.user_set.filter(id=user.id).exists()
    except Group.DoesNotExist:
        is_moderator_active = False
    
    return Response({
        'is_moderator': user.profile.is_moderator if hasattr(user, 'profile') else False,
        'is_moderator_active': is_moderator_active,
        'can_toggle': user.profile.is_moderator if hasattr(user, 'profile') else False
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_moderator_role_api(request):
    """Toggle moderator role - switch between teacher and student view"""
    user = request.user
    
    try:
        group = Group.objects.get(name='moderator')
    except Group.DoesNotExist:
        return Response(
            {'error': 'The Moderator group does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user has permanent moderator designation
    if not user.profile.is_moderator:
        return Response(
            {'error': 'You are not allowed to perform this action'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Toggle group membership
    is_currently_in_group = group.user_set.filter(id=user.id).exists()
    
    if is_currently_in_group:
        group.user_set.remove(user)
        is_moderator_active = False
        message = 'Switched to student view'
    else:
        group.user_set.add(user)
        is_moderator_active = True
        message = 'Switched to teacher view'
    
    return Response({
        'success': True,
        'is_moderator_active': is_moderator_active,
        'message': message
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or update user profile"""
    try:
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Optional: Remove or comment out this check for development
        # if not profile.is_email_verified:
        #     return Response({
        #         'error': 'Email not verified. Please verify your email before accessing profile.',
        #         'email_verified': False
        #     }, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            # Get profile data
            serializer = ProfileSerializer(profile, context={'request': request})
            return Response({
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        
        else:  # PUT or PATCH
            # Update profile data
            partial = request.method == 'PATCH'
            serializer = ProfileSerializer(
                profile, 
                data=request.data, 
                partial=partial,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Profile updated successfully',
                    'user': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': 'An error occurred while processing your request',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ============================================================
#  NOTIFICATION APIs (Common for both students and teachers)
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get notifications for the authenticated user
    
    Query params:
    - limit: Number of notifications to return (default: all)
    - include_read: Include read notifications (default: false)
    """
    user = request.user
    include_read = request.GET.get('include_read', 'false').lower() == 'true'
    limit = request.GET.get('limit', None)
    
    try:
        if include_read:
            notifications = Notification.objects.filter(receiver=user).order_by('-created_at')
        else:
            notifications = Notification.objects.get_unread_receiver_notifications(user.id)
        
        if limit:
            try:
                limit = int(limit)
                notifications = notifications[:limit]
            except ValueError:
                pass
        
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'notifications': serializer.data,
            'is_moderator': is_moderator(user)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_notifications_count(request):
    """Get count of unread notifications for the authenticated user"""
    user = request.user
    
    try:
        unread_count = Notification.objects.get_unread_receiver_notifications(user.id).count()
        
        return Response({
            'success': True,
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



import random
import hashlib
from django.core.cache import cache
from django.core.mail import send_mail

def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_password_change(request):
    user=request.user
    code = str(random.randint(100000, 999999))
    cache_key = f"pwd_change_otp:{user.id}"
    OTP_TTL = 120
    cache.set(cache_key, hash_code(code), timeout=OTP_TTL)
    send_mail(
        subject="Password change verification",
        message=f"Your code is {code}. Valid for 1 minute.",
        from_email="no-reply@yourapp.com",
        recipient_list=[user.email],
    )

    return Response({"message": "OTP sent"})
    


from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import constant_time_compare

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_password_change(request):
    user = request.user
    code = request.data.get("code")
    new_password = request.data.get("new_password")

    if not code or not new_password:
        return Response({"error": "Missing fields"}, status=400)

    cache_key = f"pwd_change_otp:{user.id}"
    cached_hash = cache.get(cache_key)
    
    if not cached_hash:
        return Response({"error": "OTP expired or invalid"}, status=400)

    if not constant_time_compare(cached_hash, hash_code(code)):
        return Response({"error": "Invalid OTP"}, status=400)

    try:
        validate_password(new_password, user)
    except Exception as e:
        return Response({"error": list(e.messages)}, status=400)

    user.set_password(new_password)
    user.save()

    cache.delete(cache_key)

    return Response({"success": True})




# Forget Password APIs

def send_password_otp(user):
    code = str(random.randint(100000, 999999))
    cache_key = f"pwd_change_otp:{user.id}"
    OTP_TTL = 120

    cache.set(cache_key, hash_code(code), timeout=OTP_TTL)

    send_mail(
        subject="Password change verification",
        message=f"Your code is {code}. Valid for 1 minute.",
        from_email="no-reply@yourapp.com",
        recipient_list=[user.email],
    )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    email = request.data.get("email")
    user = User.objects.filter(email=email).first()
    if user:
        send_password_otp(user)
    else:
        print("user not found")

    # Always same response → anti-enumeration
    return Response(
        {"message": "If the email exists, an OTP has been sent"}
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def confirm_forgot_password(request):
    email = request.data.get("email")
    code = request.data.get("code")
    new_password = request.data.get("new_password")

    if not email or not code or not new_password:
        return Response({"error": "Invalid request"}, status=400)

    user = User.objects.filter(email=email).first()
    if not user:
        # anti-enumeration
        return Response({"error": "Invalid request"}, status=400)

    cache_key = f"pwd_change_otp:{user.id}"
    cached_hash = cache.get(cache_key)

    if not cached_hash:
        return Response({"error": "OTP expired or invalid"}, status=400)

    if not constant_time_compare(cached_hash, hash_code(code)):
        return Response({"error": "OTP expired or invalid"}, status=400)

    try:
        validate_password(new_password, user)
    except Exception:
        # keep it vague on purpose
        return Response({"error": "Invalid password"}, status=400)

    user.set_password(new_password)
    user.save()

    cache.delete(cache_key)

    return Response({"success": True})







@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, message_uid):
    """
    Mark a single notification as read
    
    URL params:
    - message_uid: UUID of the notification to mark as read
    """
    user = request.user
    
    try:
        Notification.objects.mark_single_notification(
            user.id, message_uid, True
        )
        
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all unread notifications as read for the authenticated user"""
    user = request.user
    
    try:
        unread_notifications = Notification.objects.get_unread_receiver_notifications(user.id)
        msg_uuids = [str(notif.message.uid) for notif in unread_notifications]
        
        if msg_uuids:
            Notification.objects.mark_bulk_msg_notifications(
                user.id, msg_uuids, True
            )
        
        return Response({
            'success': True,
            'message': f'Marked {len(msg_uuids)} notification(s) as read',
            'count': len(msg_uuids)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_bulk_notifications_read(request):
    """
    Mark multiple specific notifications as read
    
    Request body:
    {
        "notification_uids": ["uuid1", "uuid2", "uuid3"]
    }
    """
    user = request.user
    notification_uids = request.data.get('notification_uids', [])
    
    if not notification_uids:
        return Response({
            'success': False,
            'error': 'No notification UIDs provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        Notification.objects.mark_bulk_msg_notifications(
            user.id, notification_uids, True
        )
        
        return Response({
            'success': True,
            'message': f'Marked {len(notification_uids)} notification(s) as read',
            'count': len(notification_uids)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================
#  ORIGINAL FOSSEE API VIEWS (UNCHANGED)
# ============================================================

class QuestionList(APIView):
    def get(self, request, format=None):
        questions = Question.objects.filter(user=request.user)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionDetail(APIView):
    def get_question(self, pk, user):
        try:
            return Question.objects.get(pk=pk, user=user)
        except Question.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        question = self.get_question(pk, request.user)
        serializer = QuestionSerializer(question)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        question = self.get_question(pk, request.user)
        serializer = QuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        question = self.get_question(pk, request.user)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseList(APIView):
    def get(self, request, format=None):
        courses = Course.objects.filter(students=request.user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


class StartQuiz(APIView):
    permission_classes = [IsAuthenticated] # FIX 1: Secure the view

    def get_quiz(self, pk, user):
        try:
            return Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            raise Http404

    def get(self, request, course_id, quiz_id, format=None):
        context = {}
        user = request.user
        quiz = self.get_quiz(quiz_id, user)
        questionpaper = quiz.questionpaper_set.first()

        last_attempt = AnswerPaper.objects.get_user_last_attempt(
            questionpaper, user, course_id)

        if last_attempt and last_attempt.is_attempt_inprogress():
            # NEW FIX: Did their time expire while they were offline?
            if last_attempt.time_left() <= 0:
                last_attempt.update_marks()
                last_attempt.set_end_time(timezone.now())
                last_attempt.refresh_from_db()
                # Do NOT return Response(context) here. Let it drop down 
                # so the system checks if they have another valid attempt left
            else:
                # Time is still valid, let them resume
                serializer = AnswerPaperSerializer(last_attempt)
                context["time_left"] = last_attempt.time_left()
                context["answerpaper"] = serializer.data
                return Response(context)

        can_attempt, msg = questionpaper.can_attempt_now(user, course_id)
        if not can_attempt:
            return Response({'message': msg}, status=status.HTTP_403_FORBIDDEN)

        attempt_number = 1 if not last_attempt else last_attempt.attempt_number + 1
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')

        # FIX: Catch Double-click Race conditions (Integrity Error)
        try:
            answerpaper = questionpaper.make_answerpaper(
                user, ip, attempt_number, course_id
            )
        except IntegrityError:
            answerpaper = AnswerPaper.objects.get_user_last_attempt(
                questionpaper, user, course_id)

        serializer = AnswerPaperSerializer(answerpaper)
        context["time_left"] = answerpaper.time_left()
        context["answerpaper"] = serializer.data
        return Response(context, status=status.HTTP_201_CREATED)


class QuizList(APIView):
    def get(self, request, format=None):
        quizzes = Quiz.objects.filter(creator=request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = QuizSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizDetail(APIView):
    def get_quiz(self, pk, user):
        try:
            return Quiz.objects.get(pk=pk, creator=user)
        except Quiz.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        quiz = self.get_quiz(pk, request.user)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        quiz = self.get_quiz(pk, request.user)
        serializer = QuizSerializer(quiz, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        quiz = self.get_quiz(pk, request.user)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionPaperList(APIView):
    def get(self, request, format=None):
        questionpapers = QuestionPaper.objects.filter(quiz__creator=request.user)
        serializer = QuestionPaperSerializer(questionpapers, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = QuestionPaperSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            quiz_id = request.data.get('quiz')
            question_ids = request.data.get('fixed_questions', [])
            questionset_ids = request.data.get('random_questions', [])

            if QuestionPaper.objects.filter(quiz=quiz_id).exists():
                return Response({'error': 'Already exists'},
                                status=status.HTTP_409_CONFLICT)

            # validate ownership
            if not Quiz.objects.filter(pk=quiz_id, creator=user).exists():
                raise Http404

            for qid in question_ids:
                if not Question.objects.filter(pk=qid, user=user).exists():
                    raise Http404

            for qset_id in questionset_ids:
                qset = QuestionSet.objects.get(pk=qset_id)
                for q in qset.questions.all():
                    if q.user != user:
                        raise Http404

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class QuestionPaperDetail(APIView):
    def get_questionpaper(self, pk, user):
        try:
            return QuestionPaper.objects.get(pk=pk, quiz__creator=user)
        except QuestionPaper.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        questionpaper = self.get_questionpaper(pk, request.user)
        serializer = QuestionPaperSerializer(questionpaper)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        questionpaper = self.get_questionpaper(pk, request.user)
        serializer = QuestionPaperSerializer(questionpaper, data=request.data)
        if serializer.is_valid():
            user = request.user
            quiz_id = request.data.get('quiz')
            question_ids = request.data.get('fixed_questions', [])
            questionset_ids = request.data.get('random_questions', [])

            if not Quiz.objects.filter(pk=quiz_id, creator=user).exists():
                raise Http404

            for qid in question_ids:
                if not Question.objects.filter(pk=qid, user=user).exists():
                    raise Http404

            for qset_id in questionset_ids:
                qset = QuestionSet.objects.get(pk=qset_id)
                for q in qset.questions.all():
                    if q.user != user:
                        raise Http404

            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        questionpaper = self.get_questionpaper(pk, request.user)
        questionpaper.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnswerPaperList(APIView):
    def get(self, request, format=None):
        answerpapers = AnswerPaper.objects.filter(
            question_paper__quiz__creator=request.user
        )
        serializer = AnswerPaperSerializer(answerpapers, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        try:
            qp_id = request.data['question_paper']
            attempt_number = request.data['attempt_number']
            course_id = request.data['course']
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        ip = request.META['REMOTE_ADDR']

        questionpaper = QuestionPaper.objects.get(pk=qp_id)
        course = Course.objects.get(pk=course_id)

        if not (
            user in course.students.all() or
            user in course.teachers.all() or
            user == course.creator
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        answerpaper = questionpaper.make_answerpaper(
            user, ip, attempt_number, course_id
        )

        serializer = AnswerPaperSerializer(answerpaper)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AnswerValidator(APIView):
    permission_classes = [IsAuthenticated] # FIX 1: Secure the view

    def post(self, request, answerpaper_id, question_id, format=None):
        user = request.user
        
        try:
            answerpaper = AnswerPaper.objects.get(pk=answerpaper_id, user=user)
        except AnswerPaper.DoesNotExist:
            return Response({'error': 'Answer paper not found'}, status=status.HTTP_404_NOT_FOUND)

        # FIX 2: Prevent users from submitting after time is up
        if answerpaper.time_left() <= -10 or answerpaper.status == 'completed':
            if answerpaper.status == 'inprogress':
                answerpaper.update_marks()
                answerpaper.set_end_time(timezone.now())
            return Response({'error': 'Time is up!'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

        if question not in answerpaper.questions.all():
            return Response({'error': 'Question not in this answer paper'}, status=status.HTTP_404_NOT_FOUND)

        user_answer = None

        # FIX 4: Handle File Uploads correctly
        if question.type == 'upload':
            uploaded_files = request.FILES.getlist('assignment')
            if not uploaded_files:
                return Response({'error': 'Please upload an assignment file'}, status=status.HTTP_400_BAD_REQUEST)
            
            AssignmentUpload.objects.filter(assignmentQuestion=question, answer_paper=answerpaper).delete()
            
            uploads_to_create = []
            for fname in uploaded_files:
                fname._name = fname._name.replace(" ", "_")
                uploads_to_create.append(AssignmentUpload(
                    assignmentQuestion=question, assignmentFile=fname, answer_paper=answerpaper
                ))
            AssignmentUpload.objects.bulk_create(uploads_to_create)
            user_answer = 'ASSIGNMENT UPLOADED'
        else:
            # Normal text/array answers
            try:
                raw_answer = request.data.get('answer')
                if raw_answer is None:
                    return Response({'error': 'Answer is required'}, status=status.HTTP_400_BAD_REQUEST)
                
                if question.type in ['mcq', 'mcc', 'arrange']:
                    user_answer = raw_answer if isinstance(raw_answer, list) else [raw_answer]
                elif question.type == 'integer':
                    user_answer = int(raw_answer[0] if isinstance(raw_answer, list) else raw_answer)
                elif question.type == 'float':
                    user_answer = float(raw_answer[0] if isinstance(raw_answer, list) else raw_answer)
                else:
                    user_answer = raw_answer[0] if isinstance(raw_answer, list) else str(raw_answer)
            except (ValueError, TypeError) as e:
                return Response({'error': f'Invalid answer format'}, status=status.HTTP_400_BAD_REQUEST)

        # FIX 3: Don't duplicate answers. Update existing one if user changes answer
        try:
            if question in answerpaper.get_questions_answered() and question.type not in ['code', 'upload']:
                ans = answerpaper.get_latest_answer(question.id)
                ans.answer = user_answer
                ans.correct = False
                ans.save()
            else:
                ans = Answer.objects.create(question=question, answer=user_answer)
                answerpaper.answers.add(ans)
        except Exception as e:
            return Response({'error': f'Failed to save answer'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Validate answer
        try:
            json_data = None
            if question.type == 'code':
                json_data = question.consolidate_answer_data(user_answer, user)

            result = answerpaper.validate_answer(user_answer, question, json_data, ans.id)

            if question.type not in ['code', 'upload']:
                if result.get('success'):
                    ans.correct = True
                    ans.marks = (question.points * result.get('weight', 1) / question.get_maximum_test_case_weight()) if question.partial_grading else question.points
                else:
                    ans.correct = False
                    ans.marks = 0
                
                ans.error = json.dumps(result.get('error'))
                ans.save()
                answerpaper.update_marks(state='inprogress')

            return Response(result)
            
        except Exception as e:
            # Check if it's a code server connection error
            if 'ConnectionError' in str(type(e).__name__) or 'Connection refused' in str(e):
                return Response({
                    'success': False,
                    'error': 'Code server unavailable. Try again later.'
                }, status=status.HTTP_202_ACCEPTED)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, uid):
        # Code execution polling
        ans = Answer.objects.get(pk=uid)
        url = f"{SERVER_HOST_NAME}:{SERVER_POOL_PORT}"
        result = get_result_from_code_server(url, uid)

        if result['status'] == 'done':
            final = json.loads(result['result'])
            ans.error = json.dumps(final.get('error'))
            if final.get('success'):
                ans.correct = True
                ans.marks = ans.question.points
            ans.save()

            answerpaper = ans.answerpaper_set.first()
            if answerpaper:
                answerpaper.update_marks(state='inprogress')

        return Response(result)

class GetCourse(APIView):
    def get(self, request, pk, format=None):
        course = Course.objects.get(id=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data)


class QuitQuiz(APIView):
    permission_classes = [IsAuthenticated] # FIX 1: Secure the view

    def get(self, request, answerpaper_id, format=None):
        try:
            answerpaper = AnswerPaper.objects.get(id=answerpaper_id, user=request.user)
        except AnswerPaper.DoesNotExist:
            return Response({'error': 'AnswerPaper not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # FIX 5: Stop the timer so the attempt registers as closed correctly
        if answerpaper.status == 'inprogress':
            answerpaper.update_marks() # Score their paper before quitting!
            answerpaper.status = 'quit'
            answerpaper.save()
            answerpaper.set_end_time(timezone.now())
            
        serializer = AnswerPaperSerializer(answerpaper)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_submission_status(request, answerpaper_id):
    """Get quiz submission status with all questions"""
    user = request.user
    
    try:
        answerpaper = AnswerPaper.objects.get(id=answerpaper_id, user=user)
    except AnswerPaper.DoesNotExist:
        return Response(
            {'error': 'Answer paper not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # =======================================================
    # FIX 1: Close out "inprogress" papers automatically
    # like the original Yaksh backend complete() function did.
    # =======================================================
    if answerpaper.status == 'inprogress':
        answerpaper.update_marks()
        answerpaper.set_end_time(timezone.now())
        answerpaper.refresh_from_db()  # Ensure we have the latest graded math
    
    # Get course ID from answerpaper
    course_id = None
    if hasattr(answerpaper, 'course_id'):
        course_id = answerpaper.course_id
        
    # =======================================================
    # FIX 2: Correctly count unattempted questions using 
    # FOSSEE's M2M 'questions_answered' instead of .exists()
    # =======================================================
    #answered_question_ids = set(answerpaper.questions_answered.values_list('id', flat=True))
    
    # Get all questions and their attempt status
    questions_data = []
    for question in answerpaper.questions.all():
        # Check if question has been answered
        answered = answerpaper.answers.filter(question=question).exists()
        
        question_title = question.summary if hasattr(question, 'summary') and question.summary else (
            question.description[:50] + '...' if question.description else f'Question {question.id}'
        )
        questions_data.append({
            'id': question.id,
            'title': question_title,
            'attempted': answered,
            'type': question.type
        })
    
    attempted_count = len([q for q in questions_data if q['attempted']])
    not_attempted_count = len(questions_data) - attempted_count
    
    quiz_name = answerpaper.question_paper.quiz.description if answerpaper.question_paper and answerpaper.question_paper.quiz else 'Quiz'
    
    return Response({
        'answerpaper_id': answerpaper.id,
        'quiz_name': quiz_name,
        'course_id': course_id,
        'status': answerpaper.status,
        'questions': questions_data,
        'attempted_count': attempted_count,
        'not_attempted_count': not_attempted_count,
        'total_questions': len(questions_data),
        'percent': getattr(answerpaper, 'percent', 0)
    }, status=status.HTTP_200_OK)

    
# ============================================================
#  STUDENT DASHBOARD APIs
# ============================================================


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def student_dash(request):
    """
    API for Student Dashboard (replaces quizlist_user).
    GET: Returns enrolled courses and other available courses.
    POST: Search for hidden courses by code.
    """
    user = request.user
    courses = []
    completion_percentages = {}

    if request.method == "POST":
        course_code = request.data.get('course_code')
        if course_code:
            try:
                if hasattr(Course.objects, 'get_hidden_courses'):
                    courses = list(Course.objects.get_hidden_courses(code=course_code))
                else:
                    courses = list(Course.objects.filter(code=course_code, hidden=True))
            except Exception:
                courses = []
        else:
            return Response({'error': 'Course code is required for search'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        enrolled_courses = user.students.filter(is_trial=False).order_by('-id')
        courses = list(enrolled_courses)

    for course in courses:
        if course.is_enrolled(user):
            completion_percentages[course.id] = course.get_completion_percent(user)
        else:
            completion_percentages[course.id] = None

    serializer = StudentDashboardCourseSerializer(
        courses, 
        many=True, 
        context={'user': user, 'completion_percentages': completion_percentages}
    )

    # --- Add user stats to the response ---
    user_stats, _ = UserStats.objects.get_or_create(user=user)
    stats_serializer = UserStatsSerializer(user_stats)

    # --- Enhanced statistics and highlights ---
    total_enrolled = user.students.filter(is_trial=False).count()
    active_enrolled = user.students.filter(is_trial=False, active=True).count()
    avg_completion = (
        sum([v for v in completion_percentages.values() if v is not None]) /
        max(1, len([v for v in completion_percentages.values() if v is not None]))
    ) if completion_percentages else 0

    # Recent courses (last 5 enrolled)
    recent_courses = user.students.filter(is_trial=False).order_by('-created_on')[:5]
    recent_courses_data = StudentDashboardCourseSerializer(
        recent_courses, many=True, context={'user': user, 'completion_percentages': completion_percentages}
    ).data

    # Top completed courses
    top_courses = sorted(
        [
            (course, completion_percentages.get(course.id, 0) or 0)
            for course in courses if completion_percentages.get(course.id) is not None
        ],
        key=lambda x: x[1], reverse=True
    )[:5]
    top_courses_data = StudentDashboardCourseSerializer(
        [c[0] for c in top_courses], many=True, context={'user': user, 'completion_percentages': completion_percentages}
    ).data

    # Recent activities (last 5)
    recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:5]
    recent_activities_data = UserActivitySerializer(recent_activities, many=True).data

    # Badges
    badges = UserBadge.objects.filter(user=user)
    badges_data = UserBadgeSerializer(badges, many=True).data

    # Upcoming quizzes (active, not attempted)
    upcoming_quizzes = []
    for course in courses[:10]:
        for module in course.learning_module.all():
            for unit in module.learning_unit.filter(type='quiz'):
                quiz = unit.quiz
                if quiz and quiz.active and (not AnswerPaper.objects.filter(user=user, question_paper__quiz=quiz, status='completed').exists()):
                    upcoming_quizzes.append({
                        'id': quiz.id,
                        'course_id': course.id,
                        'name': quiz.description,
                        'course_name': course.name,
                        'module_name': module.name,
                        'is_exercise': getattr(quiz, 'is_exercise', False)
                    })
    upcoming_quizzes = upcoming_quizzes[:5]

    return Response({
        'courses': serializer.data,
        'user': {
            'id': user.id,
            'name': user.get_full_name(),
            'username': user.username,
            'email': user.email
        },
        'stats': stats_serializer.data,
        'dashboard': {
            'total_enrolled': total_enrolled,
            'active_enrolled': active_enrolled,
            'avg_completion': round(avg_completion, 1),
            'recent_courses': recent_courses_data,
            'top_courses': top_courses_data,
            'recent_activities': recent_activities_data,
            'badges': badges_data,
            'upcoming_quizzes': upcoming_quizzes
        }
    })
    


# ============================================================
#  COURSES & ENROLLMENT APIs
# ============================================================


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_courselist(request):
    """
    API endpoint to get only enrolled courses for the logged-in user.
    """
    user = request.user
    courses_data = []

    enrolled_courses = user.students.filter(is_trial=False).order_by('-id')

    for course in enrolled_courses:
        _percent = course.get_completion_percent(user)
        courses_data.append({
            'data': course,
            'completion_percentage': _percent,
        })

    serializer = CourseWithCompletionSerializer(courses_data, many=True, context={'request': request})
    return Response({
        'user_id': user.id,
        'courses': serializer.data,
        'title': 'Enrolled Courses'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_new_courses(request):
    """
    API endpoint to search for new (not enrolled) courses by course code.
    """
    user = request.user
    course_code = request.data.get('course_code')
    enrolled_ids = user.students.filter(is_trial=False).values_list("id", flat=True)
    new_courses = Course.objects.get_hidden_courses(code=course_code).exclude(id__in=enrolled_ids)

    courses_data = []
    for course in new_courses:
        courses_data.append({
            'data': course,
            'completion_percentage': None,  # Not enrolled, so no completion
        })

    serializer = CourseWithCompletionSerializer(courses_data, many=True, context={'request': request})
    return Response({
        'courses': serializer.data,
        'title': 'Search Results'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_available_courses(request):
    """
    API endpoint to get all active, non-enrolled courses for the student.
    Used by the 'Add New Course' tab to show browseable courses.
    """
    user = request.user
    enrolled_ids = user.students.filter(is_trial=False).values_list("id", flat=True)
    available_courses = Course.objects.filter(
        active=True, is_trial=False, hidden=False
    ).exclude(id__in=enrolled_ids).order_by('-id')

    courses_data = []
    for course in available_courses:
        courses_data.append({
            'data': course,
            'completion_percentage': None,
        })

    serializer = CourseWithCompletionSerializer(courses_data, many=True, context={'request': request})
    return Response({
        'courses': serializer.data,
        'title': 'Available Courses'
    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_request_api(request, course_id):
    """
    API endpoint for students to request enrollment in a course.
    This is used when the course requires approval from instructors.
    """
    user = request.user
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if enrollment is allowed
    if not course.is_active_enrollment() and course.hidden:
        return Response(
            {
                'error': 'Unable to add enrollments for this course',
                'message': 'Please contact your instructor/administrator.'
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if already enrolled
    if course.students.filter(id=user.id).exists():
        return Response(
            {'message': 'You are already enrolled in this course'},
            status=status.HTTP_200_OK
        )
    
    # Check if already requested
    if course.requests.filter(id=user.id).exists():
        return Response(
            {'message': 'Enrollment request already pending'},
            status=status.HTTP_200_OK
        )
    
    # Send enrollment request
    course.request(user)
    
    # Log activity
    UserActivity.create_activity(
        user=user,
        activity_type='enrollment_requested',
        title=f'Requested enrollment in {course.name}',
        description=f'Awaiting approval from {course.creator.get_full_name()}',
        icon='clock',
        color='yellow',
        course_id=course.id
    )
    
    return Response(
        {
            'message': f'Enrollment request sent for {course.name}',
            'instructor': course.creator.get_full_name(),
            'course_name': course.name
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def self_enroll_api(request, course_id):
    """
    API endpoint for students to self-enroll in a course.
    This is used when the course allows self-enrollment without approval.
    """
    user = request.user
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if course allows self-enrollment
    if not course.is_self_enroll():
        return Response(
            {
                'error': 'This course does not allow self-enrollment',
                'message': 'Please request enrollment instead.'
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if already enrolled
    if course.students.filter(id=user.id).exists():
        return Response(
            {'message': 'You are already enrolled in this course'},
            status=status.HTTP_200_OK
        )
    
    # Self-enroll the user
    was_rejected = False
    course.enroll(was_rejected, user)
    
    # Create or get course status
    CourseStatus.objects.get_or_create(user=user, course=course)
    
    # Log activity
    UserActivity.create_activity(
        user=user,
        activity_type='course_enrolled',
        title=f'Enrolled in {course.name}',
        description=f'Started learning with {course.creator.get_full_name()}',
        icon='check',
        color='green',
        course_id=course.id
    )
    
    return Response(
        {
            'message': f'Successfully enrolled in {course.name}',
            'instructor': course.creator.get_full_name(),
            'course_name': course.name,
            'course_id': course.id
        },
        status=status.HTTP_201_CREATED
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_catalog(request):
    """Get course catalog with optional filtering"""
    user = request.user
    
    # Get query parameters
    level = request.GET.get('level')
    category = request.GET.get('category')
    enrollment_status = request.GET.get('enrollment_status', 'all')
    
    # Base query - active courses only
    courses = Course.objects.filter(active=True, hidden=False).prefetch_related(
        'learning_module', 'learning_module__learning_unit', 'creator', 'students'
    )
    
    # Filter by enrollment status
    if enrollment_status == 'enrolled':
        courses = courses.filter(students=user)
    elif enrollment_status == 'completed':
        completed_course_ids = CourseStatus.objects.filter(
            user=user, grade__isnull=False
        ).values_list('course_id', flat=True)
        courses = courses.filter(id__in=completed_course_ids)
    
    # Order by creation date (newest first)
    courses = courses.order_by('-created_on')
    
    # Serialize
    serializer = CourseCatalogSerializer(
        courses, many=True, context={'user': user}
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def enrolled_courses(request):
    """Get list of enrolled courses"""
    user = request.user
    
    courses = Course.objects.filter(students=user, active=True).order_by('-created_on')
    serializer = CourseProgressSerializer(courses, many=True, context={'user': user})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_course(request, course_id):
    """Enroll user in a course"""
    user = request.user
    
    try:
        course = Course.objects.get(id=course_id, active=True)
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if already enrolled
    if course.students.filter(id=user.id).exists():
        return Response(
            {'message': 'Already enrolled in this course'},
            status=status.HTTP_200_OK
        )
    
    # Enroll user
    course.students.add(user)
    
    # Create or get course status
    CourseStatus.objects.get_or_create(user=user, course=course)
    
    # Log activity
    UserActivity.create_activity(
        user=user,
        activity_type='course_enrolled',
        title=f'Enrolled in {course.name}',
        description='Started learning journey',
        icon='check',
        color='green',
        course_id=course.id
    )
    
    return Response(
        {'message': 'Successfully enrolled in course'},
        status=status.HTTP_201_CREATED
    )


# ============================================================
#  COURSE MODULES & LESSONS APIs
# ============================================================


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_modules(request, course_id):
    """Get all modules for a course with progress and grade"""
    user = request.user
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check enrollment
    if not course.students.filter(id=user.id).exists():
        return Response(
            {'error': 'You are not enrolled for this course!'},
            status=status.HTTP_403_FORBIDDEN
        )
        
    # Check course is active (enrollment window check is intentionally excluded here:
    # enrolled students should always be able to access their course content)
    if not course.active:
        return Response(
            {'error': "{0} is not currently active".format(course.name)},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Use model method to get modules (handles ordering and is_trial)
    learning_modules = course.get_learning_modules()
    
    # Calculate global course progress
    course_percentage = course.get_completion_percent(user)
    
    # Get grade if available
    grade = None
    course_status = CourseStatus.objects.filter(course=course, user=user).first()
    if course_status:
        if not course_status.grade:
            course_status.set_grade()
        grade = course_status.get_grade()

    # Pass course object in context so serializer can calculate module progress efficiently
    context = {'user': user, 'course': course}
    serializer = LearningModuleDetailSerializer(
        learning_modules, many=True, context=context
    )
    
    return Response({
        'course': {
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'progress': course_percentage,
            'grade': grade,
            'instructions': course.instructions,
        },
        'modules': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def module_detail(request, module_id):
    """Get detailed module information with units"""
    user = request.user
    
    try:
        module = LearningModule.objects.get(id=module_id)
    except LearningModule.DoesNotExist:
        return Response(
            {'error': 'Module not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Find course that contains this module AND the user is enrolled in
    courses = Course.objects.filter(learning_module=module, students=user)
    course = courses.first()

    if not course:
         # Fallback to checking any course if user not enrolled (for consistent error messaging)
         course = Course.objects.filter(learning_module=module).first()
         if not course:
            return Response(
                {'error': 'Course not found for this module'},
                status=status.HTTP_404_NOT_FOUND
            )
         # If we found a course but user isn't in it (logic above failed), return 403
         if not course.students.filter(id=user.id).exists():
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_403_FORBIDDEN
            )
            
    # Check active status of the course
    if not course.active or not course.is_active_enrollment():
         return Response(
             {'error': "{0} is either expired or not active".format(course.name)},
             status=status.HTTP_403_FORBIDDEN
         )

    serializer = LearningModuleDetailSerializer(
        module, context={'user': user, 'course': course}
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lesson_detail(request, lesson_id):
    """Get detailed lesson information"""
    user = request.user
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Lesson not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Find course containing this lesson
    learning_unit = LearningUnit.objects.filter(lesson=lesson).first()
    if not learning_unit:
        return Response(
            {'error': 'Learning unit not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    course = Course.objects.filter(
        learning_module__learning_unit=learning_unit
    ).first()
    
    if not course:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check enrollment
    if not course.students.filter(id=user.id).exists():
        return Response(
            {'error': 'Not enrolled in this course'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = LessonDetailSerializer(
        lesson, context={'request': request, 'user': user, 'course_id': course.id}
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_lesson(request, lesson_id):
    """Mark a lesson as completed"""
    user = request.user
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        return Response(
            {'error': 'Lesson not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Find the learning unit and course
    learning_unit = LearningUnit.objects.filter(lesson=lesson).first()
    if not learning_unit:
        return Response(
            {'error': 'Learning unit not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    course = Course.objects.filter(
        learning_module__learning_unit=learning_unit
    ).first()
    
    if not course:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get or create course status
    course_status, created = CourseStatus.objects.get_or_create(
        user=user, course=course
    )
    
    # Mark unit as completed
    if not course_status.completed_units.filter(id=learning_unit.id).exists():
        course_status.completed_units.add(learning_unit)
        
        # Update current unit to next unit
        module = learning_unit.learning_unit.first()
        if module:
            next_unit = module.get_next_unit(learning_unit.id)
            if next_unit:
                course_status.current_unit = next_unit
                course_status.save()
        
        # Log activity
        UserActivity.create_activity(
            user=user,
            activity_type='lesson_completed',
            title='Completed lesson',
            description=lesson.name,
            icon='check',
            color='green',
            course_id=course.id,
            lesson_id=lesson.id
        )
        
        # Update user stats
        user_stats, created = UserStats.objects.get_or_create(user=user)
        user_stats.update_streak()
        user_stats.add_learning_time(0.5)  # Assume 30 minutes per lesson
        
        # Check and update badge progress
        _check_and_award_badges(user)
    
    return Response(
        {'message': 'Lesson marked as completed'},
        status=status.HTTP_200_OK
    )




# ============================================================
#  ANSWERPAPER APIs
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_answerpaper_api(request, questionpaper_id, course_id):
    """
    API endpoint equivalent of view_answerpaper from yaksh.views.
    Validates if the user is a student in the course and if the quiz allows viewing.
    """
    user = request.user
    quiz = get_object_or_404(QuestionPaper, pk=questionpaper_id).quiz
    course = get_object_or_404(Course, pk=course_id)
    
    # Mirror equivalent logic directly from your view
    if quiz.view_answerpaper and user in course.students.all():
        # Get raw data dict from model
        user_data = AnswerPaper.objects.get_user_data(user, questionpaper_id, course_id)
        
        has_user_assignments = AssignmentUpload.objects.filter(
            answer_paper__user=user, 
            answer_paper__course_id=course.id,
            answer_paper__question_paper_id=questionpaper_id
        ).exists()

        # Find module name connected to this quiz and course
        module_name = None
        # Get learning units for this quiz
        units = LearningUnit.objects.filter(quiz=quiz)
        if units.exists():
            # Find the module that contains this unit and belongs to this course
            module = course.learning_module.filter(learning_unit__in=units).first()
            if module:
                module_name = module.name

        # Format the papers data to include student answers alongside questions,
        # just like in api_grade_user_attempt
        papers_data = []
        for paper in user_data.get('papers', []):
            questions_data = []
            total_marks = 0.0
            
            # Fetch the specific answers for this attempt
            for question, answers in paper.get_question_answers().items():
                question_data = QuestionSerializer(question).data
                total_marks += float(question_data.get('points', 0) or 0)
                answer_data = None
                
                if answers and answers[0] is not None:
                    if isinstance(answers[0], dict) and answers[0].get('answer'):
                        ans_obj = answers[0]['answer']
                        answer_data = {
                            'id': ans_obj.id,
                            'answer_content': ans_obj.answer,
                            'marks': ans_obj.marks,
                            'correct': ans_obj.correct,
                            'error': ans_obj.error,
                            'skipped': getattr(ans_obj, 'skipped', False)
                        }
                if answer_data is None:
                    answer_data = {
                        'id': None,
                        'answer_content': None,
                        'marks': 0.0,
                        'correct': False,
                        'error': None,
                        'skipped': True
                    }
                questions_data.append({
                    'question': question_data,
                    'answer': answer_data
                })
                
            papers_data.append({
                'id': paper.id,
                'attempt_number': paper.attempt_number,
                'start_time': paper.start_time,
                'end_time': paper.end_time,
                'marks_obtained': paper.marks_obtained,
                'total_marks': total_marks,
                'percent': paper.percent,
                'status': paper.status,
                'comments': paper.comments,
                'questions': questions_data
            })
        
        # Package directly as a dictionary rather than wrapping in a serializer
        # This gives you total control over the output structure
        response_data = {
            'quiz': QuizSerializer(quiz).data,
            'course_id': course.id,
            'course_name': course.name,      # <--- Added
            'module_name': module_name,      # <--- Added
            'has_user_assignments': has_user_assignments,
            'user': SimpleUserSerializer(user_data.get('user')).data if user_data.get('user') else None,
            'profile': ProfileSerializer(user_data.get('user').profile).data if hasattr(user_data.get('user'), 'profile') else None,
            'papers': papers_data,
            'questionpaper_id': user_data.get('questionpaperid')
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    else:
        # User not enrolled or quiz has view_answerpaper turned off
        return Response(
            {"detail": "You do not have permission to view this answer paper."},
            status=status.HTTP_403_FORBIDDEN
        )
        
# ============================================================
#  BADGES & INSIGHTS APIs
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_badges(request):
    """Get user's earned and in-progress badges"""
    user = request.user
    
    # Get unlocked badges
    unlocked_badges = UserBadge.objects.filter(user=user).select_related('badge')
    unlocked_serializer = UserBadgeSerializer(unlocked_badges, many=True)
    
    # Get in-progress badges
    in_progress_badges = BadgeProgress.objects.filter(
        user=user
    ).exclude(
        badge__in=unlocked_badges.values_list('badge', flat=True)
    ).select_related('badge')
    
    # Update progress for all badges
    for badge_progress in in_progress_badges:
        badge_progress.update_progress()
    
    in_progress_serializer = BadgeProgressSerializer(in_progress_badges, many=True)
    
    # Get locked badges (active badges that are neither unlocked nor in-progress)
    unlocked_badge_ids = list(unlocked_badges.values_list('badge', flat=True))
    in_progress_badge_ids = list(in_progress_badges.values_list('badge', flat=True))
    locked_badges = Badge.objects.filter(active=True).exclude(
        id__in=unlocked_badge_ids + in_progress_badge_ids
    )
    locked_serializer = BadgeSerializer(locked_badges, many=True)
    
    return Response({
        'unlocked': unlocked_serializer.data,
        'inProgress': in_progress_serializer.data,
        'locked': locked_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements(request):
    """Get user achievements and milestones"""
    user = request.user
    
    user_stats, created = UserStats.objects.get_or_create(user=user)
    
    achievements = {
        'total_badges': UserBadge.objects.filter(user=user).count(),
        'total_challenges': user_stats.total_challenges_solved,
        'current_streak': user_stats.current_streak,
        'longest_streak': user_stats.longest_streak,
        'courses_completed': CourseStatus.objects.filter(
            user=user, grade__isnull=False
        ).count(),
        'perfect_scores': AnswerPaper.objects.filter(
            user=user, status='completed', percent=100
        ).count()
    }
    
    return Response(achievements, status=status.HTTP_200_OK)


# ============================================================
#  HELPER FUNCTIONS
# ============================================================

def _check_and_award_badges(user):
    """Check and award badges to user based on criteria"""
    active_badges = Badge.objects.filter(active=True)
    
    for badge in active_badges:
        # Skip if already earned
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            continue
        
        # Check criteria
        if badge.check_criteria(user):
            # Award badge
            UserBadge.objects.create(user=user, badge=badge)
            
            # Log activity
            UserActivity.create_activity(
                user=user,
                activity_type='badge_earned',
                title='Earned badge',
                badge_name=badge.name,
                icon='award',
                color='amber'
            )
        else:
            # Update or create progress
            badge_progress, created = BadgeProgress.objects.get_or_create(
                user=user, badge=badge
            )
            badge_progress.update_progress()


# ============================================================
#  TEACHER APIs - Content Creation
# ============================================================

def _check_teacher_permission(user):
    """Check if user is a moderator/teacher"""
    try:
        return is_moderator(user)
    except:
        return False


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    """Get teacher dashboard statistics"""
    user = request.user
    
    if not _check_teacher_permission(user):
        # Check if user has moderator designation but is in student mode
        has_moderator_designation = hasattr(user, 'profile') and user.profile.is_moderator
        if has_moderator_designation:
            return Response(
                {
                    'error': 'You are currently in student view. Please switch to teacher view to access this page.',
                    'can_toggle': True,
                    'is_moderator_designation': True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(
            {'error': 'You are not authorized to access this page'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get courses created by teacher
    courses = Course.objects.filter(
        Q(creator=user) | Q(teachers=user),
        is_trial=False
    ).distinct()
    
    # Calculate statistics (current period)
    total_courses = courses.count()
    active_courses = courses.filter(active=True).count()
    
    # Total students enrolled across all courses
    total_students = User.objects.filter(
        students__in=courses
    ).distinct().count()
    
    # Recent courses (last 5)
    recent_courses = courses.order_by('-created_on')[:5]
    
    # Calculate average completion rate
    # Include all courses with enrolled students in the calculation
    # Courses with 0% completion should still contribute to the average
    completion_rates = []
    for course in courses:
        enrolled_count = course.students.count()
        if enrolled_count > 0:
            # Count students who have completed the course (have a grade assigned)
            completed_count = CourseStatus.objects.filter(
                course=course, grade__isnull=False
            ).count()
            # Calculate completion rate for this course (can be 0% if no completions)
            course_completion_rate = (completed_count / enrolled_count) * 100
            completion_rates.append(course_completion_rate)
    
    # Calculate average across all courses with enrolled students
    # If no courses have enrolled students, return 0
    avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0
    
    # Recent events (upcoming quizzes)
    upcoming_quizzes = []
    for course in courses[:10]:  # Check first 10 courses
        for module in course.learning_module.all():
            for unit in module.learning_unit.filter(type='quiz'):
                quiz = unit.quiz
                if quiz and quiz.active:
                    upcoming_quizzes.append({
                        'id': quiz.id,
                        'course_id': course.id,
                        'name': quiz.description,
                        'course_name': course.name,
                        'module_name': module.name,
                        'is_exercise': getattr(quiz, 'is_exercise', False)
                    })

    # Top Students Logic
    top_students = []
    try:
        # Get all answer papers for courses managed by this teacher
        from django.db.models import Sum, Avg, Count
        
        # Filter completed answer papers with valid marks
        completed_papers = AnswerPaper.objects.filter(
            status='completed',
            course__in=courses,
            marks_obtained__isnull=False
        )
        
        # Get top students by average score across all their quizzes
        # This gives a fairer representation than total sum
        # Require at least 1 completed quiz to be considered
        top_performers = completed_papers.values(
            'user__id', 
            'user__first_name', 
            'user__last_name', 
            'user__username'
        ).annotate(
            avg_score=Avg('marks_obtained'),
            total_score=Sum('marks_obtained'),
            quiz_count=Count('id')
        ).filter(
            quiz_count__gte=1  # At least one completed quiz
        ).order_by('-avg_score')[:5]
        
        for student in top_performers:
            # Get the course where they scored the highest average
            user_id = student['user__id']
            best_course_data = completed_papers.filter(
                user__id=user_id
            ).values('course__id', 'course__name').annotate(
                course_avg=Avg('marks_obtained')
            ).order_by('-course_avg').first()
            
            # Get student name
            name = f"{student['user__first_name']} {student['user__last_name']}".strip()
            if not name:
                name = student['user__username']
            
            # Use the course where they scored best, or fallback to any course they took
            if best_course_data and best_course_data.get('course__name'):
                subject = best_course_data['course__name']
            else:
                # Fallback: get any course they took
                any_paper = completed_papers.filter(user__id=user_id).first()
                subject = any_paper.course.name if any_paper and any_paper.course else 'General'
            
            # Round the average score for display
            avg_score = round(student['avg_score'] or 0, 1)
            
            top_students.append({
                'id': user_id,
                'name': name,
                'subject': subject,
                'score': avg_score
            })
            
    except Exception as e:
        import traceback
        print(f"Error calculating top students: {e}")
        print(traceback.format_exc())

    
    return Response({
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_students': total_students,
        'avg_completion': round(avg_completion, 1),
        'top_students': top_students,
        'recent_courses': [
            {
                'id': course.id,
                'name': course.name,
                'active': course.active,
                'students_count': course.students.count(),
                'modules_count': course.learning_module.count(),
                'start_date': course.start_enroll_time,
                'end_date': course.end_enroll_time
            }
            for course in recent_courses
        ],
        'upcoming_quizzes': upcoming_quizzes[:5]
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_courses_list(request):
    """Get list of courses created/managed by teacher"""
    user = request.user
    
    if not _check_teacher_permission(user):
        # Check if user has moderator designation but is in student mode
        has_moderator_designation = hasattr(user, 'profile') and user.profile.is_moderator
        if has_moderator_designation:
            return Response(
                {
                    'error': 'You are currently in student view. Please switch to teacher view to access this page.',
                    'can_toggle': True,
                    'is_moderator_designation': True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(
            {'error': 'You are not authorized to access this page'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get query parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Base query - courses created or taught by user
    courses = Course.objects.filter(
        Q(creator=user) | Q(teachers=user),
        is_trial=False
    ).distinct()
    
    # Apply search filter
    if search_query:
        courses = courses.filter(name__icontains=search_query)
    
    # Apply status filter
    if status_filter == 'active':
        courses = courses.filter(active=True)
    elif status_filter == 'inactive':
        courses = courses.filter(active=False)
    elif status_filter == 'draft':
        # Draft courses could be those without modules or inactive
        courses = courses.filter(
            Q(active=False) | Q(learning_module__isnull=True)
        ).distinct()
    
    # Order by creation date
    courses = courses.order_by('-created_on')
    
    # Serialize courses with additional stats
    courses_data = []
    for course in courses:
        enrolled_count = course.students.count()
        completed_count = CourseStatus.objects.filter(
            course=course, grade__isnull=False
        ).count()
        completion_rate = (completed_count / enrolled_count * 100) if enrolled_count > 0 else 0
        
        courses_data.append({
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'active': course.active,
            'enrollment': course.enrollment,
            'students_count': enrolled_count,
            'completions': completed_count,
            'completion_rate': round(completion_rate, 1),
            'modules_count': course.learning_module.count(),
            'created_on': course.created_on.isoformat() if course.created_on else None,
            'start_date': course.start_enroll_time.isoformat() if course.start_enroll_time else None,
            'end_date': course.end_enroll_time.isoformat() if course.end_enroll_time else None,
            'status': 'Active' if course.active else 'Inactive'
        })
    
    return Response(courses_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_create_course(request):
    """Create a new course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized to create courses'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get form data
        name = request.data.get('name')
        enrollment = request.data.get('enrollment', 'default')
        code = request.data.get('code', '')
        instructions = request.data.get('instructions', '')
        start_enroll_time = request.data.get('start_enroll_time')
        end_enroll_time = request.data.get('end_enroll_time')
        grading_system_id = request.data.get('grading_system_id')
        view_grade = request.data.get('view_grade', False)
        active = request.data.get('active', True)
        
        if not name:
            return Response(
                {'error': 'Course name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create course
        course = Course.objects.create(
            name=name,
            enrollment=enrollment,
            code=code,
            instructions=instructions,
            view_grade=view_grade,
            active=active,
            hidden=False,  # Make courses visible by default for students
            creator=user
        )
        
        # Set enrollment times if provided
        if start_enroll_time:
            try:
                course.start_enroll_time = datetime.fromisoformat(start_enroll_time.replace('Z', '+00:00'))
            except:
                pass
        
        if end_enroll_time:
            try:
                course.end_enroll_time = datetime.fromisoformat(end_enroll_time.replace('Z', '+00:00'))
            except:
                pass
        
        # Set grading system if provided
        if grading_system_id:
            try:
                from grades.models import GradingSystem
                grading_system = GradingSystem.objects.get(id=grading_system_id, creator=user)
                course.grading_system = grading_system
            except:
                pass
        
        # Set hidden based on code
        if code:
            course.hidden = True
        else:
            course.hidden = False
        
        course.save()
        
        return Response({
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'active': course.active,
            'message': 'Course created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to create course', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_get_course(request, course_id):
    """Get course details for teacher"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify ownership
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response(
                {'error': 'You do not have permission to access this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get modules
        modules = course.learning_module.order_by('order')
        modules_data = []
        for module in modules:
            units = module.learning_unit.order_by('order')
            modules_data.append({
                'id': module.id,
                'name': module.name,
                'description': module.description,
                'order': module.order,
                'active': module.active,
                'units_count': units.count(),
                'units': [
                    {
                        'id': unit.id,
                        'type': unit.type,
                        'order': unit.order,
                        'lesson_id': unit.lesson.id if unit.lesson else None,
                        'quiz_id': unit.quiz.id if unit.quiz else None,
                        'name': unit.lesson.name if unit.lesson else (unit.quiz.description if unit.quiz else ''),
                        'is_exercise': unit.quiz.is_exercise if unit.quiz else False # <--- ADD THIS LINE
                    }
                    for unit in units
                ]
            })
        
        enrolled_count = course.students.count()
        completed_count = CourseStatus.objects.filter(
            course=course, grade__isnull=False
        ).count()
        
        return Response({
            'id': course.id,
            'name': course.name,
            'code': course.code,
            'enrollment': course.enrollment,
            'instructions': course.instructions,
            'active': course.active,
            'view_grade': course.view_grade,
            'start_enroll_time': course.start_enroll_time.isoformat() if course.start_enroll_time else None,
            'end_enroll_time': course.end_enroll_time.isoformat() if course.end_enroll_time else None,
            'grading_system_id': course.grading_system.id if course.grading_system else None,
            'modules': modules_data,
            'students_count': enrolled_count,
            'completions': completed_count,
            'created_on': course.created_on.isoformat() if course.created_on else None
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def teacher_update_course(request, course_id):
    """Update an existing course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify ownership
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response(
                {'error': 'You do not have permission to update this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update fields
        if 'name' in request.data:
            course.name = request.data['name']
        if 'enrollment' in request.data:
            course.enrollment = request.data['enrollment']
        if 'code' in request.data:
            course.code = request.data['code']
            course.hidden = bool(request.data['code'])
        if 'instructions' in request.data:
            course.instructions = request.data['instructions']
        if 'view_grade' in request.data:
            course.view_grade = request.data['view_grade']
        if 'active' in request.data:
            course.active = request.data['active']
        
        # Update enrollment times
        if 'start_enroll_time' in request.data:
            try:
                start_time = request.data['start_enroll_time']
                course.start_enroll_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except:
                pass
        
        if 'end_enroll_time' in request.data:
            try:
                end_time = request.data['end_enroll_time']
                course.end_enroll_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except:
                pass
        
        # Update grading system
        if 'grading_system_id' in request.data:
            grading_system_id = request.data['grading_system_id']
            if grading_system_id:
                try:
                    from grades.models import GradingSystem
                    grading_system = GradingSystem.objects.get(id=grading_system_id, creator=user)
                    course.grading_system = grading_system
                except:
                    pass
            else:
                course.grading_system = None
        
        course.save()
        
        return Response({
            'id': course.id,
            'name': course.name,
            'message': 'Course updated successfully'
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to update course', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
#  MODULE MANAGEMENT APIs
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_get_course_modules(request, course_id):
    """Get all modules for a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify ownership
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to access this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get modules ordered by order
        modules = course.learning_module.order_by('order')
        modules_data = []
        
        for module in modules:
            units = module.learning_unit.order_by('order')
            units_data = []
            for unit in units:
                unit_data = {
                    'id': unit.id,
                    'type': unit.type,
                    'order': unit.order,
                }
                if unit.type == 'lesson' and unit.lesson:
                    unit_data['lesson_id'] = unit.lesson.id
                    unit_data['name'] = unit.lesson.name
                elif unit.type == 'quiz' and unit.quiz:
                    unit_data['quiz_id'] = unit.quiz.id
                    unit_data['name'] = unit.quiz.description
                    unit_data['is_exercise'] = unit.quiz.is_exercise # <--- ADD THIS LINE
                units_data.append(unit_data)
            
            modules_data.append({
                'id': module.id,
                'name': module.name,
                'description': module.description,
                'order': module.order,
                'active': module.active,
                'check_prerequisite': module.check_prerequisite,
                'units_count': units.count(),
                'units': units_data
            })
        
        return Response(modules_data, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_create_module(request, course_id):
    """Create a new module for a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify ownership
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response(
                {'error': 'You do not have permission to modify this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get form data
        name = request.data.get('name')
        description = request.data.get('description', '')
        order = request.data.get('order')
        check_prerequisite = request.data.get('check_prerequisite', False)
        active = request.data.get('active', True)
        
        if not name:
            return Response(
                {'error': 'Module name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Auto-calculate order if not provided
        if order is None:
            last_module = course.learning_module.order_by('-order').first()
            order = (last_module.order + 1) if last_module else 1
        
        # Convert markdown to HTML
        html_data = get_html_text(description) if description else ''
        
        # Create module
        module = LearningModule.objects.create(
            name=name,
            description=description,
            html_data=html_data,
            order=order,
            check_prerequisite=check_prerequisite,
            active=active,
            creator=user
        )
        
        # Add module to course
        course.learning_module.add(module)
        
        return Response({
            'id': module.id,
            'name': module.name,
            'description': module.description,
            'order': module.order,
            'active': module.active,
            'message': 'Module created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to create module', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


from api.serializers import LearningModuleSerializer

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def teacher_update_module(request, course_id, module_id):
    """Update an existing module"""
    user = request.user

    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        course = Course.objects.get(id=course_id)
        module = LearningModule.objects.get(id=module_id)

        # Verify ownership
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response(
                {'error': 'You do not have permission to modify this course'},
                status=status.HTTP_403_FORBIDDEN
            )

        if module.creator != user and not course.is_creator(user) and not course.is_teacher(user):
            return Response(
                {'error': 'You do not have permission to modify this module'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify module belongs to course
        if module not in course.learning_module.all():
            return Response(
                {'error': 'Module does not belong to this course'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update fields
        if 'name' in request.data:
            module.name = request.data['name']
        if 'description' in request.data:
            module.description = request.data['description']
            module.html_data = get_html_text(request.data['description']) if request.data['description'] else ''
        if 'order' in request.data:
            module.order = request.data['order']
        if 'check_prerequisite' in request.data:
            module.check_prerequisite = request.data['check_prerequisite']
        if 'active' in request.data:
            module.active = request.data['active']

        module.save()

        serializer = LearningModuleSerializer(module)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except LearningModule.DoesNotExist:
        return Response(
            {'error': 'Module not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to update module', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def teacher_delete_module(request, course_id, module_id):
    """Delete a module from a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        module = LearningModule.objects.get(id=module_id)
        
        # Verify ownership
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response(
                {'error': 'You do not have permission to modify this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if module.creator != user and not course.is_creator(user) and not course.is_teacher(user):
            return Response(
                {'error': 'You do not have permission to delete this module'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify module belongs to course
        if module not in course.learning_module.all():
            return Response(
                {'error': 'Module does not belong to this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove module from course
        course.learning_module.remove(module)
        
        # Delete module (cascade will delete learning units)
        module.delete()
        
        return Response({
            'message': 'Module deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except LearningModule.DoesNotExist:
        return Response(
            {'error': 'Module not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to delete module', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


        


# ============================================================
#  LESSON MANAGEMENT APIs
# ============================================================


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_lesson_handler(request, course_id, module_id, lesson_id=None):
    user = request.user
    
    if not is_moderator(user):
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
    
    course = get_object_or_404(Course, id=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'This Lesson does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
    module = get_object_or_404(LearningModule, id=module_id)
    
    # GET: Retrieve lesson details
    if request.method == "GET":
        if not lesson_id:
            return Response({'error': 'lesson_id required'}, status=status.HTTP_400_BAD_REQUEST)
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        lesson_files = LessonFile.objects.filter(lesson=lesson)
        toc_data = get_toc_contents(request, course_id, lesson_id)
        
        video_url = None
        if lesson.video_file:
            video_url = request.build_absolute_uri(lesson.video_file.url)

        return Response({
            'id': lesson.id,
            'name': lesson.name,
            'description': lesson.description,
            'video_path': lesson.video_path,
            'video_file': video_url,
            'active': lesson.active,
            'files': [{'id': f.id, 'name': f.file.name, 'url': request.build_absolute_uri(f.file.url)} for f in lesson_files],
            'toc': toc_data
        })
    
    # POST: Create new lesson
    if request.method == "POST":
        if lesson_id:
            return Response({'error': 'Use PUT to update existing lesson'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Basic fields
            active = request.data.get('active', True)
            if isinstance(active, str):
                active = active.lower() == 'true'

            # ✅ FIX: Prepare creation dictionary to handle file during creation
            create_kwargs = {
                'name': request.data.get('name'),
                'description': request.data.get('description', ''),
                'video_path': request.data.get('video_path', ''),
                'active': active,
                'creator': user
            }

            # Handle Video File
            video_file = request.FILES.get("video_file")
            if video_file:
                create_kwargs['video_file'] = video_file

            lesson = Lesson.objects.create(**create_kwargs)
            
            lesson.html_data = get_html_text(lesson.description)
            lesson.save()
            
            # Handle file uploads
            lessonfiles = request.FILES.getlist('Lesson_files')
            if lessonfiles:
                for les_file in lessonfiles:
                    LessonFile.objects.get_or_create(lesson=lesson, file=les_file)
            
            # Add to module
            last_unit = module.get_learning_units().last()
            new_order = (last_unit.order + 1) if (last_unit and last_unit.order is not None) else 1
            
            # Use create directly with order to satisfy NOT NULL constraint
            unit = LearningUnit.objects.create(
                type="lesson", 
                lesson=lesson,
                order=new_order
            )

            module.learning_unit.add(unit)
            
            return Response({'message': 'Lesson created', 'lesson_id': lesson.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # PUT: Update existing lesson
    if request.method == "PUT":
        if not lesson_id:
            return Response({'error': 'lesson_id required for update'}, status=status.HTTP_400_BAD_REQUEST)
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        try:
            # Update fields directly
            lesson.name = request.data.get('name', lesson.name)
            lesson.description = request.data.get('description', lesson.description)
            lesson.video_path = request.data.get('video_path', lesson.video_path)
            
            active = request.data.get('active', lesson.active)
            if isinstance(active, str):
                active = active.lower() == 'true'
            lesson.active = active

            # Handle Video File Logic (Clear or Update)
            clear_video = request.data.get("video_file-clear")
            video_file = request.FILES.get("video_file")
            
            if (clear_video == 'true' or video_file) and lesson.video_file:
                 # Logic from views.py: remove previous file if new uploaded or cleared
                 # Note: model's remove_file helper or manual deletion
                 if hasattr(lesson, 'remove_file'):
                     lesson.remove_file()
                 else:
                     lesson.video_file.delete(save=False)
                     lesson.video_file = None

            if video_file:
                lesson.video_file = video_file

            lesson.html_data = get_html_text(lesson.description)
            lesson.save()
            
             # Handle new file uploads
            lessonfiles = request.FILES.getlist('Lesson_files') if hasattr(request.FILES, 'getlist') else request.FILES.get('Lesson_files', [])
            if lessonfiles:
                for les_file in lessonfiles:
                    LessonFile.objects.get_or_create(lesson=lesson, file=les_file)

            # Handle file deletion (list of IDs)
            # Frontend should send 'delete_files' as a list of IDs to remove
            if hasattr(request.data, 'getlist'):
                delete_files = request.data.getlist('delete_files')
            else:
                delete_files = request.data.get('delete_files')
                if delete_files and not isinstance(delete_files, list):
                    delete_files = [delete_files]

            if not delete_files and 'delete_files' in request.data:
                # Handle case where it might be sent as comma separated string or single value
                 val = request.data.get('delete_files')
                 if val:
                     delete_files = [val] if not isinstance(val, list) else val
            
            if delete_files:
                LessonFile.objects.filter(id__in=delete_files, lesson=lesson).delete()
            
            # Ensure unit exists and order is correct
            # We don't change order on simple update usually, unless reordering API is called, 
            # but we preserve connection
            if not module.learning_unit.filter(lesson=lesson).exists():
                 # Re-add if missing
                 last_unit = module.get_learning_units().last()
                 order = last_unit.order + 1 if last_unit else 1
                 unit, created = LearningUnit.objects.get_or_create(
                    type="lesson", lesson=lesson
                 )
                 unit.order = order
                 unit.save()
                 module.learning_unit.add(unit.id)
            
            return Response({'message': 'Lesson updated', 'lesson_id': lesson.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # DELETE: Remove lesson
    if request.method == "DELETE":
        if not lesson_id:
            return Response({'error': 'lesson_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        # Check ownership again implicitly handled by course/module logic above but specific check:
        # if lesson.creator != user and ... (already handled by course permission check above)
        
        lesson.delete()
        return Response({'message': 'Lesson deleted'}, status=status.HTTP_204_NO_CONTENT)


#===========================================================
# DESIGN MODULE APIs
#===========================================================


def get_quiz_les_display_name(item):
    """Helper to get display name for quiz/lesson tuple (type, id)"""
    typ, obj_id = item
    if typ == "quiz":
        try:
            return f"{Quiz.objects.get(id=obj_id).description} (quiz)"
        except Quiz.DoesNotExist:
            return "Unknown Quiz"
    elif typ == "lesson":
        try:
            return f"{Lesson.objects.get(id=obj_id).name} (lesson)"
        except Lesson.DoesNotExist:
            return "Unknown Lesson"
    return ""

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_design_module(request, module_id, course_id=None):
    user = request.user
    if not is_moderator(user):
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    # Get course if course_id is provided
    # Note: Even if course_id isn't provided, we might want to ensure the user owns the module
    # The original view checks course ownership if course_id is passed, otherwise assumes module ownership check later
    # implied by fetching LearningModule and modifying it.
    if course_id:
        try:
            course = Course.objects.get(id=course_id)
            if not course.is_creator(user) and not course.is_teacher(user):
                return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
        except Course.DoesNotExist:
             return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        learning_module = LearningModule.objects.get(id=module_id)
    except LearningModule.DoesNotExist:
        return Response({'error': 'Module not found'}, status=status.HTTP_404_NOT_FOUND)

    # 1. GET: Return current module design info (Available vs Chosen)
    if request.method == "GET":
        # Get existing units in order
        units = learning_module.get_learning_units()
        
        # Calculate available quizzes/lessons not yet in module
        # FIX: Manually collect IDs from units and use DB exclude instead of set subtraction helper
        added_quiz_ids = set()
        added_lesson_ids = set()
        
        for unit in units:
            if unit.type == 'quiz' and unit.quiz_id:
                added_quiz_ids.add(unit.quiz_id)
            elif unit.type == 'lesson' and unit.lesson_id:
                added_lesson_ids.add(unit.lesson_id)
        
        # Query strictly for items NOT in the added sets
        quizzes = Quiz.objects.filter(creator=user, is_trial=False).exclude(id__in=added_quiz_ids)
        lessons = Lesson.objects.filter(creator=user).exclude(id__in=added_lesson_ids)
        
        available_pool = []
        for q in quizzes:
            # Pass the is_exercise flag for quizzes (third argument)
            available_pool.append(("quiz", q.id, getattr(q, 'is_exercise', False)))
        for l in lessons:
            # Lessons cannot be exercises, default to False
            available_pool.append(("lesson", l.id, False))
        
        # Sort or format for display
        quiz_les_display = [
            {
                "type": typ,
                "id": obj_id,
                # Create a composite key often used by frontend (e.g., "15:quiz")
                "value_key": f"{obj_id}:{typ}", 
                "display_name": get_quiz_les_display_name((typ, obj_id)),
                # Inject the boolean value
                "is_exercise": is_exc
            }
            for typ, obj_id, is_exc in available_pool
        ]
        
        return Response({
            'learning_units': MinimalLearningUnitSerializer(units, many=True).data,
            'quiz_les_list': quiz_les_display,
            'module_id': learning_module.id,
            'course_id': course_id
        })


    # 2. POST: Handle actions (add, change, remove, change_prerequisite)
    if request.method == "POST":
        action = request.data.get("action")
        
        # --- ADD UNITS ---
        if action == "add":
            # Support both list of strings ["1:quiz", "2:lesson"] or comma-sep string "1:quiz,2:lesson"
            add_values = request.data.get("chosen_list", [])
            if isinstance(add_values, str):
                add_values = add_values.split(',') if add_values else []
                
            to_add_list = []
            if add_values:
                ordered_units = learning_module.get_learning_units()
                start_val = ordered_units.last().order + 1 if ordered_units.exists() else 1
                
                for order, value in enumerate(add_values, start_val):
                    # Value format expects "id:type" (e.g. "45:quiz")
                    if ":" not in str(value):
                        continue
                        
                    learning_id, type_ = str(value).split(":")
                    
                    if type_ == "quiz":
                        unit, _ = LearningUnit.objects.get_or_create(
                            order=order, quiz_id=learning_id, type=type_
                        )
                    else:
                        unit, _ = LearningUnit.objects.get_or_create(
                            order=order, lesson_id=learning_id, type=type_
                        )
                    to_add_list.append(unit)
                
                if to_add_list:
                    learning_module.learning_unit.add(*to_add_list)
                    return Response({'message': "Lesson/Quiz added successfully"})
                return Response({'error': "Invalid data format for chosen_list"}, status=400)
            else:
                return Response({'error': "Please select a lesson/quiz to add"}, status=400)

        # --- REORDER UNITS ---
        elif action == "change":
            # Expects "unit_id:order"
            order_list = request.data.get("ordered_list", [])
            if isinstance(order_list, str):
                order_list = order_list.split(',') if order_list else []

            if order_list:
                for order_str in order_list:
                    if ":" not in str(order_str):
                        continue
                    learning_unit_id, learning_order = str(order_str).split(":")
                    if learning_order:
                        try:
                            learning_unit = learning_module.learning_unit.get(id=learning_unit_id)
                            learning_unit.order = learning_order
                            learning_unit.save()
                        except (LearningUnit.DoesNotExist, ValueError):
                            continue
                return Response({'message': "Order changed successfully"})
            else:
                return Response({'error': "Please select a lesson/quiz to change"}, status=400)

        # --- REMOVE UNITS ---
        elif action == "remove":
            remove_values = request.data.get("delete_list", [])
            # Support list or single value
            if not isinstance(remove_values, list):
                remove_values = [remove_values]
            
            if remove_values:
                # Remove association from module first
                learning_module.learning_unit.remove(*remove_values)
                # Delete actual unit objects (as per original logic)
                LearningUnit.objects.filter(id__in=remove_values).delete()
                return Response({'message': "Lessons/quizzes deleted successfully"})
            else:
                return Response({'error': "Please select a lesson/quiz to remove"}, status=400)

        # --- CHECK PREREQUISITE ---
        elif action == "change_prerequisite":
            unit_list = request.data.get("check_prereq", [])
            if not isinstance(unit_list, list):
                unit_list = [unit_list]

            if unit_list:
                for unit in unit_list:
                    try:
                        learning_unit = learning_module.learning_unit.get(id=unit)
                        learning_unit.toggle_check_prerequisite()
                        learning_unit.save()
                    except LearningUnit.DoesNotExist:
                        continue
                return Response({'message': "Changed prerequisite status successfully"})
            else:
                return Response({'error': "Please select a lesson/quiz to change prerequisite"}, status=400)

        return Response({'error': "Invalid action"}, status=400)

#=============================================================
# DESIGN QUESTION PAPER APIs
#=============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def design_questionpaper_api(request, course_id, quiz_id, questionpaper_id=None):
    user = request.user
    
    # Check permissions
    if not is_moderator(user):
        return Response({'detail': 'You are not allowed to view this page!'}, status=status.HTTP_403_FORBIDDEN)
        
    if quiz_id:
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if quiz.creator != user and not course_id:
            return Response({'detail': 'This quiz does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
            
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response({'detail': 'This Course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)

    # Fetch/create paper definition
    if questionpaper_id is None:
        question_paper, created = QuestionPaper.objects.get_or_create(quiz_id=quiz_id)
    else:
        question_paper = get_object_or_404(QuestionPaper, id=questionpaper_id, quiz_id=quiz_id)

    response_data = {}

    if request.method == 'POST':
        action = request.data.get('action') 
        
        if action == 'add-fixed':
            question_ids = request.data.get('checked_ques', [])
            if isinstance(question_ids, str):
                question_ids = [qid for qid in question_ids.split(',') if qid]
                
            if question_ids:
                if question_paper.fixed_question_order:
                    ques_order = question_paper.fixed_question_order.split(",") + [str(q) for q in question_ids]
                    questions_order = ",".join(ques_order)
                else:
                    questions_order = ",".join([str(q) for q in question_ids])
                    
                questions = Question.objects.filter(id__in=question_ids)
                question_paper.fixed_question_order = questions_order
                question_paper.save()
                question_paper.fixed_questions.add(*questions)
                response_data['message'] = "Questions added successfully"
            else:
                return Response({'detail': 'Please select at least one question'}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'remove-fixed':
            question_ids = request.data.get('added_questions', [])
            if question_ids:
                if question_paper.fixed_question_order:
                    que_order = question_paper.fixed_question_order.split(",")
                    for qid in question_ids:
                        if str(qid) in que_order:
                            que_order.remove(str(qid))
                    question_paper.fixed_question_order = ",".join(que_order) if que_order else ""
                    question_paper.save()
                question_paper.fixed_questions.remove(*question_ids)
                response_data['message'] = "Questions removed successfully"
            else:
                return Response({'detail': 'Please select at least one question'}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'add-random':
            question_ids = request.data.get('random_questions', [])
            num_of_questions = request.data.get('num_of_questions', 1)
            marks = request.data.get('marks')
            
            if question_ids and marks:
                with transaction.atomic():
                    random_set = QuestionSet.objects.create(marks=marks, num_questions=num_of_questions)
                    random_ques = Question.objects.filter(id__in=question_ids)
                    random_set.questions.add(*random_ques)
                    question_paper.random_questions.add(random_set)
                response_data['message'] = "Random questions added successfully"
            else:
                return Response({'detail': 'Please provide questions and marks'}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'remove-random':
            random_set_ids = request.data.get('random_sets', [])
            if random_set_ids:
                question_paper.random_questions.remove(*random_set_ids)
                response_data['message'] = "Random sets removed successfully"
            else:
                return Response({'detail': 'Please select a question set'}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'save':
            serializer = QuestionPaperSerializer(question_paper, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                response_data['message'] = "Question Paper saved successfully"
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        elif action == 'filter':
            marks = request.data.get('marks')
            tags = request.data.get('question_tags')
            question_type = request.data.get('question_type')
            
            questions = None
            if marks:
                questions = _get_questions(user, question_type, marks)
            elif tags:
                questions = _get_questions_from_tags(tags, user)
                
            if questions is not None:
                questions = _remove_already_present(question_paper.id, questions)
                response_data['filtered_questions'] = QuestionSerializer(questions, many=True).data

        # Final cleanup for post requests (updates summary statistics of marks on the paper)
        question_paper.update_total_marks()
        question_paper.save()

    # GET response construction (acts as standard fetch, and applies after any POST interaction)
    que_tags = Question.objects.filter(active=True, user=user).values_list('tags', flat=True).distinct()
    all_tags = Tag.objects.filter(id__in=que_tags)
    
    response_data.update({
        'question_paper': QuestionPaperSerializer(question_paper).data,
        'fixed_questions': QuestionSerializer(question_paper.get_ordered_questions(), many=True).data,
        'random_sets': QuestionSetSerializer(question_paper.random_questions.all(), many=True).data,
        'all_tags': TagSerializer(all_tags, many=True).data,
        'course_id': course_id
    })

    return Response(response_data, status=status.HTTP_200_OK)



#=============================================================
# Exercise APIs
#=============================================================

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_exercise_handler(request, course_id, module_id, quiz_id=None):
    user = request.user
    if not is_moderator(user):
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    course = get_object_or_404(Course, pk=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'This Course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
    
    module = get_object_or_404(LearningModule, id=module_id)

    # Helper function to match the Yaksh backend's ownership allowance 
    # (teachers on the same course can edit each other's course exercises)
    def has_quiz_permission(quiz):
        if quiz.creator != user and not (course.is_creator(user) or course.is_teacher(user)):
            return False
        return True

    # GET: Retrieve exercise details
    if request.method == "GET":
        if not quiz_id:
            return Response({'error': 'quiz_id required'}, status=status.HTTP_400_BAD_REQUEST)
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if not has_quiz_permission(quiz):
            return Response({'error': 'This quiz does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = QuizSerializer(quiz)
        data = serializer.data
        
        # Append QuestionPaper ID so frontend can redirect to paper design view
        question_paper = quiz.questionpaper_set.first()
        data['questionpaper_id'] = question_paper.id if question_paper else None
        
        return Response(data)

    # POST: Create a new exercise
    if request.method == "POST":
        if quiz_id:
            return Response({'error': 'Use PUT for updating existing exercises'}, status=status.HTTP_400_BAD_REQUEST)
        
        form = ExerciseForm(request.data)
        if form.is_valid():
            quiz = form.save(commit=False)
            # Enforce parameters identical to Yaksh backend
            quiz.is_exercise = True
            quiz.time_between_attempts = 0
            quiz.weightage = 0
            quiz.allow_skip = False
            quiz.attempts_allowed = -1
            quiz.duration = 1000
            quiz.pass_criteria = 0
            quiz.creator = user
            quiz.save()
            
            # Setup module mapping
            last_unit = module.get_learning_units().last()
            order = last_unit.order + 1 if last_unit else 1
            unit, created = LearningUnit.objects.get_or_create(
                type="quiz", quiz=quiz, order=order
            )
            if created:
                module.learning_unit.add(unit.id)
                
            # Guarantee a QuestionPaper exists
            question_paper, _ = QuestionPaper.objects.get_or_create(quiz=quiz)
                
            return Response({
                'message': 'Exercise saved', 
                'quiz_id': quiz.id, 
                'questionpaper_id': question_paper.id
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    # PUT: Update an existing exercise
    if request.method == "PUT":
        if not quiz_id:
            return Response({'error': 'quiz_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if not has_quiz_permission(quiz):
            return Response({'error': 'This quiz does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
            
        form = ExerciseForm(request.data, instance=quiz)
        if form.is_valid():
            quiz = form.save(commit=False)
            # Enforce the parameters again to match the robust setup in Yaksh
            quiz.is_exercise = True
            quiz.time_between_attempts = 0
            quiz.weightage = 0
            quiz.allow_skip = False
            quiz.attempts_allowed = -1
            quiz.duration = 1000
            quiz.pass_criteria = 0
            quiz.save()
            
            question_paper = quiz.questionpaper_set.first()
            return Response({
                'message': 'Exercise updated', 
                'quiz_id': quiz.id,
                'questionpaper_id': question_paper.id if question_paper else None
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Delete exercise
    if request.method == "DELETE":
        if not quiz_id:
            return Response({'error': 'quiz_id required'}, status=status.HTTP_400_BAD_REQUEST)
            
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if not has_quiz_permission(quiz):
            return Response({'error': 'This quiz does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
            
        # Optional: Standard clean up for Learning Unit relationships
        unit = module.learning_unit.filter(type='quiz', quiz=quiz).first()
        if unit:
            module.learning_unit.remove(unit)
            unit.delete()
            
        quiz.delete()
        return Response({'message': 'Exercise deleted'}, status=status.HTTP_204_NO_CONTENT)

    return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)



# ============================================================
#  QUIZ APIs
# ============================================================

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_quiz_handler(request, course_id, module_id, quiz_id=None):
    """
    Unified API handler for managing quizzes (Create, Retrieve, Update, Delete)
    within a specific course module.
    """
    user = request.user
    
    # Permission check
    if not _check_teacher_permission(user):
        return Response({'error': 'You are not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        course = get_object_or_404(Course, id=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
            
        module = get_object_or_404(LearningModule, id=module_id)
        
        # GET: Retrieve quiz details
        if request.method == "GET":
            if not quiz_id:
                return Response({'error': 'quiz_id required for retrieval'}, status=status.HTTP_400_BAD_REQUEST)
                
            quiz = get_object_or_404(Quiz, id=quiz_id)
            if quiz.creator != user:
                return Response({'error': 'This quiz does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
                
            unit = module.learning_unit.filter(type='quiz', quiz=quiz).first()
            if not unit:
                return Response({'error': 'Quiz not attached to this module'}, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({
                'id': quiz.id,
                'description': quiz.description,
                'instructions': quiz.instructions or '',
                'duration': quiz.duration,
                'attempts_allowed': quiz.attempts_allowed,
                'time_between_attempts': quiz.time_between_attempts,
                'pass_criteria': quiz.pass_criteria,
                'weightage': quiz.weightage,
                'allow_skip': quiz.allow_skip,
                'view_answerpaper': quiz.view_answerpaper,
                'is_exercise': quiz.is_exercise,
                'active': quiz.active,
                'order': unit.order
            })

        # POST: Create new quiz
        if request.method == "POST":
            if quiz_id:
                return Response({'error': 'Use PUT to update existing quiz'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Form data extraction
            description = request.data.get('description')
            if not description:
                return Response({'error': 'Quiz description/name is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                quiz = Quiz.objects.create(
                    description=description,
                    instructions=request.data.get('instructions', ''),
                    duration=request.data.get('duration', 20),
                    attempts_allowed=request.data.get('attempts_allowed', 1),
                    time_between_attempts=request.data.get('time_between_attempts', 0.0),
                    pass_criteria=request.data.get('pass_criteria', 40.0),
                    weightage=request.data.get('weightage', 100.0),
                    allow_skip=request.data.get('allow_skip', True),
                    view_answerpaper=request.data.get('view_answerpaper', True),
                    is_exercise=request.data.get('is_exercise', False),
                    active=request.data.get('active', True),
                    creator=user
                )

                # Create QuestionPaper
                QuestionPaper.objects.create(quiz=quiz)
                
                # Determine order
                order = request.data.get('order')
                if order is None:
                    last_unit = module.get_learning_units().last()
                    order = (last_unit.order + 1) if (last_unit and last_unit.order is not None) else 1
                
                # Create unit and add to module (same as lesson handler)
                unit = LearningUnit.objects.create(
                    type='quiz',
                    quiz=quiz,
                    order=order
                )
                module.learning_unit.add(unit)
                
                return Response({
                    'id': quiz.id,
                    'message': 'Quiz created successfully',
                    'order': order,
                    'unit_id': unit.id,
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # PUT: Update existing quiz
        if request.method == "PUT":
            if not quiz_id:
                return Response({'error': 'quiz_id required for update'}, status=status.HTTP_400_BAD_REQUEST)
                
            quiz = get_object_or_404(Quiz, id=quiz_id)
            if quiz.creator != user:
                return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
                
            unit = module.learning_unit.filter(type='quiz', quiz=quiz).first()
            if not unit:
                return Response({'error': 'Quiz not in this module'}, status=status.HTTP_400_BAD_REQUEST)

            # Update fields
            if 'description' in request.data: quiz.description = request.data['description']
            if 'instructions' in request.data: quiz.instructions = request.data['instructions']
            if 'duration' in request.data: quiz.duration = request.data['duration']
            if 'attempts_allowed' in request.data: quiz.attempts_allowed = request.data['attempts_allowed']
            if 'time_between_attempts' in request.data: quiz.time_between_attempts = request.data['time_between_attempts']
            if 'pass_criteria' in request.data: quiz.pass_criteria = request.data['pass_criteria']
            if 'weightage' in request.data: quiz.weightage = request.data['weightage']
            if 'allow_skip' in request.data: quiz.allow_skip = request.data['allow_skip']
            if 'view_answerpaper' in request.data: quiz.view_answerpaper = request.data['view_answerpaper']
            if 'is_exercise' in request.data: quiz.is_exercise = request.data['is_exercise']
            if 'active' in request.data: quiz.active = request.data['active']
            
            if 'order' in request.data:
                unit.order = request.data['order']
                unit.save()
            
            quiz.save()
            return Response({'message': 'Quiz updated', 'id': quiz.id})

        # DELETE: Delete quiz
        if request.method == "DELETE":
            if not quiz_id:
                return Response({'error': 'quiz_id required'}, status=status.HTTP_400_BAD_REQUEST)

            quiz = get_object_or_404(Quiz, id=quiz_id)
            if quiz.creator != user:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
                
            unit = module.learning_unit.filter(type='quiz', quiz=quiz).first()
            if unit:
                module.learning_unit.remove(unit)
                unit.delete()
                
            quiz.delete()
            return Response({'message': 'Quiz deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
#  QUESTION MANAGEMENT APIs
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_questions_list(request):
    """Get list of questions created by teacher"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get query parameters
    question_type = request.GET.get('type', '')
    language = request.GET.get('language', '')
    search = request.GET.get('search', '')
    active = request.GET.get('active', None)
    
    # Base query - questions created by user
    # Base query - questions created by user
    questions = Question.objects.filter(user=user)
    
    # Apply filters
    if question_type:
        questions = questions.filter(type=question_type)
    if language:
        questions = questions.filter(language=language)
    if search:
        questions = questions.filter(
            Q(summary__icontains=search) | Q(description__icontains=search)
        )
    if active is not None:
        questions = questions.filter(active=active.lower() == 'true')
    
    # Order by creation
    questions = questions.order_by('-id')
    
    # Serialize questions
    questions_data = []
    for question in questions:
        try:
            test_cases = question.get_test_cases_as_dict()
            if test_cases is None:
                test_cases = []
        except Exception:
            test_cases = []
        questions_data.append({
            'id': question.id,
            'summary': question.summary,
            'description': question.description,
            'type': question.type,
            'language': question.language,
            'points': question.points,
            'active': question.active,
            'topic': question.topic,
            'test_cases_count': len(test_cases),
            'created': question.id  # Using ID as proxy for creation order
        })
    
    return Response(questions_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_test_question(request, question_id):
    """Create trial quiz for teacher to test a question"""
    user = request.user
    from yaksh.views import test_mode, is_moderator
    
    if not is_moderator(user):
        return Response({'error': 'Only teachers can test questions'}, status=403)
    
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=404)
    
    trial_paper, trial_course, trial_module = test_mode(user, False, [str(question.id)], None)
    trial_paper.update_total_marks()
    trial_paper.save()
    
    return Response({
        'questionpaper_id': trial_paper.id,
        'module_id': trial_module.id,
        'course_id': trial_course.id,
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_get_question(request, question_id):
    """Get question details with test cases and files"""
    user = request.user

    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        question = Question.objects.get(id=question_id)

        # Verify ownership
        if question.user != user:
            return Response(
                {'error': 'You do not have permission to access this question'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get test cases
        test_cases = question.get_test_cases_as_dict()

        # Get files
        from yaksh.models import FileUpload
        files = []
        for f in FileUpload.objects.filter(question=question):
            # Build absolute URL for the file
            file_url = request.build_absolute_uri(f.file.url) if hasattr(f.file, "url") else ""
            files.append({
                "id": f.id,
                "name": os.path.basename(f.file.name),
                "url": file_url,  # Full URL with domain
                "extract": f.extract,
                "hide": f.hide,
            })

        return Response({
            'id': question.id,
            'summary': question.summary,
            'description': question.description,
            'type': question.type,
            'language': question.language,
            'points': question.points,
            'active': question.active,
            'topic': question.topic,
            'snippet': question.snippet,
            'solution': question.solution,
            'partial_grading': question.partial_grading,
            'grade_assignment_upload': question.grade_assignment_upload,
            'min_time': question.min_time,
            'test_cases': test_cases,
            'files': files  
        }, status=status.HTTP_200_OK)

    except Question.DoesNotExist:
        return Response(
            {'error': 'Question not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_question_file(request, file_id):
    try:
        file_obj = FileUpload.objects.get(id=file_id)
        # Optional: check ownership/permissions here
        file_obj.delete()
        return Response({'message': 'File deleted successfully'}, status=status.HTTP_200_OK)
    except FileUpload.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_question_file(request, question_id):
    import os
    from yaksh.models import FileUpload, Question
    question = get_object_or_404(Question, id=question_id, user=request.user)
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({'error': 'No file provided'}, status=400)
    file_obj = FileUpload.objects.create(
        question=question,
        file=uploaded_file,
        extract=False,
        hide=False
    )
    # Extract just the filename, not the full path
    file_name = os.path.basename(file_obj.file.name)
    # Build absolute URL
    file_url = request.build_absolute_uri(file_obj.file.url)
    return Response({
        'id': file_obj.id,
        'name': file_name,
        'url': file_url,  # Full URL with domain
        'extract': file_obj.extract,
        'hide': file_obj.hide,
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_create_question(request):
    """Create a new question with test cases"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get question data
        summary = request.data.get('summary')
        description = request.data.get('description', '')
        question_type = request.data.get('type')
        language = request.data.get('language', 'python')
        points = request.data.get('points', 1.0)
        active = request.data.get('active', True)
        topic = request.data.get('topic', '')
        snippet = request.data.get('snippet', '')
        solution = request.data.get('solution', '')
        partial_grading = request.data.get('partial_grading', False)
        min_time = request.data.get('min_time', 0)
        test_cases_data = request.data.get('test_cases', [])
        
        if not summary or not question_type:
            return Response(
                {'error': 'Question summary and type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create question
        question = Question.objects.create(
            summary=summary,
            description=description,
            type=question_type,
            language=language,
            points=points,
            active=active,
            topic=topic,
            snippet=snippet,
            solution=solution,
            partial_grading=partial_grading,
            min_time=min_time,
            user=user
        )
        
        # Create test cases based on question type
        for tc_data in test_cases_data:
            tc_type = tc_data.get('type') or tc_data.get('test_case_type')
            if not tc_type:
                continue
            
            try:
                model_class = get_model_class(tc_type)
                
                # Handle different test case types
                if tc_type == 'mcc' or tc_type == 'mcqtestcase':
                    # For MCQ and MCC, we need multiple McqTestCase entries (One for each option)
                    options = tc_data.get('options', [])
                    if isinstance(options, str):
                        try:
                            options = json.loads(options)
                        except Exception:
                            options = [options]
                    
                    correct_indices = tc_data.get('correct')
                    # Standardize correct answer(s) into a list for iteration
                    if not isinstance(correct_indices, list):
                        correct_indices = [correct_indices] if correct_indices is not None else []
                    
                    # Filter empty options dynamically as they arrive from frontend
                    cleaned_options = [opt for opt in options if str(opt).strip()]
                    
                    model_class = get_model_class('mcqtestcase')
                    for idx, option in enumerate(cleaned_options):
                        model_class.objects.create(
                            question=question,
                            options=str(option).strip(),
                            correct=(idx in correct_indices),
                            type='mcqtestcase'
                        )

                elif tc_type == 'stdiobasedtestcase':
                    model_class.objects.create(
                        question=question,
                        expected_input=tc_data.get('expected_input', ''),
                        expected_output=tc_data.get('expected_output', ''),
                        weight=tc_data.get('weight', 1.0),
                        hidden=tc_data.get('hidden', False),
                        type=tc_type
                    )
                elif tc_type == 'standardtestcase':
                    model_class.objects.create(
                        question=question,
                        test_case=tc_data.get('test_case', ''),
                        weight=tc_data.get('weight', 1.0),
                        hidden=tc_data.get('hidden', False),
                        test_case_args=tc_data.get('test_case_args', ''),
                        type=tc_type
                    )
                elif tc_type == 'hooktestcase':
                    model_class.objects.create(
                        question=question,
                        hook_code=tc_data.get('hook_code', ''),
                        weight=tc_data.get('weight', 1.0),
                        hidden=tc_data.get('hidden', False),
                        type=tc_type
                    )
                elif tc_type == 'integertestcase':
                    model_class.objects.create(
                        question=question,
                        correct=tc_data.get('correct'),
                        type=tc_type
                    )
                elif tc_type == 'stringtestcase':
                    model_class.objects.create(
                        question=question,
                        correct=tc_data.get('correct', ''),
                        string_check=tc_data.get('string_check', 'lower'),
                        type=tc_type
                    )
                elif tc_type == 'floattestcase':
                    model_class.objects.create(
                        question=question,
                        correct=tc_data.get('correct'),
                        error_margin=tc_data.get('error_margin', 0.0),
                        type=tc_type
                    )
                elif tc_type == 'arrangetestcase':
                    options = tc_data.get('options', [])
                    if isinstance(options, str):
                        try:
                            options = json.loads(options)
                        except Exception:
                            options = [options]
                    
                    if isinstance(options, list):
                        # Create a distinct DB row for each option sequentially
                        for opt in options:
                            if str(opt).strip():  # Ignore empty lines
                                model_class.objects.create(
                                    question=question,
                                    options=str(opt).strip(),
                                    type=tc_type
                                )
                    else:
                        model_class.objects.create(
                            question=question,
                            options=str(options),
                            type=tc_type
                        )

            except Exception as e:
                # Log error but continue with other test cases
                print(f"Error creating test case: {e}")
                continue
        
        return Response({
            'id': question.id,
            'summary': question.summary,
            'type': question.type,
            'message': 'Question created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to create question', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def teacher_update_question(request, question_id):
    """Update an existing question"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        question = Question.objects.get(id=question_id)
        
        # Verify ownership
        if question.user != user:
            return Response(
                {'error': 'You do not have permission to update this question'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update question fields
        if 'summary' in request.data:
            question.summary = request.data['summary']
        if 'description' in request.data:
            question.description = request.data['description']
        if 'type' in request.data:
            question.type = request.data['type']
        if 'language' in request.data:
            question.language = request.data['language']
        if 'points' in request.data:
            question.points = request.data['points']
        if 'active' in request.data:
            question.active = request.data['active']
        if 'topic' in request.data:
            question.topic = request.data['topic']
        if 'snippet' in request.data:
            question.snippet = request.data['snippet']
        if 'solution' in request.data:
            question.solution = request.data['solution']
        if 'partial_grading' in request.data:
            question.partial_grading = request.data['partial_grading']
        if 'min_time' in request.data:
            question.min_time = request.data['min_time']
        if 'grade_assignment_upload' in request.data:
            question.grade_assignment_upload = request.data['grade_assignment_upload']

        question.save()

        # Update file extract/hide flags if provided
        if 'files' in request.data:
            from yaksh.models import FileUpload
            files_data = request.data['files']
            for file_data in files_data:
                file_id = file_data.get('id')
                if file_id is not None:
                    try:
                        file_obj = FileUpload.objects.get(id=file_id, question=question)
                        # Update extract and hide flags
                        if 'extract' in file_data:
                            extract = file_data['extract']
                            file_obj.extract = str(extract).lower() == 'true' if isinstance(extract, str) else bool(extract)
                        if 'hide' in file_data:
                            hide = file_data['hide']
                            file_obj.hide = str(hide).lower() == 'true' if isinstance(hide, str) else bool(hide)
                        file_obj.save()
                    except FileUpload.DoesNotExist:
                        continue

        
        # Update test cases if provided
        if 'test_cases' in request.data:
            test_cases_data = request.data['test_cases']
            
            # Special case for arrange, mcq, and mcc: wipe old rows and securely recreate them 
            if question.type in ['arrange', 'mcq', 'mcc']:
                question.testcase_set.all().delete() # Drop old test case choices
                
                for tc_data in test_cases_data:
                    tc_type = tc_data.get('type') or tc_data.get('test_case_type')
                    if tc_type == 'arrangetestcase':
                        from yaksh.models import ArrangeTestCase
                        options = tc_data.get('options', [])
                        if isinstance(options, str):
                            try:
                                options = json.loads(options)
                            except Exception:
                                options = [options]
                                
                        if isinstance(options, list):
                            for opt in options:
                                if str(opt).strip():
                                    ArrangeTestCase.objects.create(question=question, options=str(opt).strip(), type=tc_type)
                        else:
                            ArrangeTestCase.objects.create(question=question, options=str(options), type=tc_type)
                            
                    elif tc_type in ['mcqtestcase', 'mcc']:
                        from yaksh.models import McqTestCase
                        options = tc_data.get('options', [])
                        if isinstance(options, str):
                            try:
                                options = json.loads(options)
                            except Exception:
                                options = [options]
                                
                        correct_indices = tc_data.get('correct')
                        if not isinstance(correct_indices, list):
                            correct_indices = [correct_indices] if correct_indices is not None else []
                            
                        cleaned_options = [opt for opt in options if str(opt).strip()]
                        
                        for idx, option in enumerate(cleaned_options):
                            McqTestCase.objects.create(
                                question=question,
                                options=str(option).strip(),
                                correct=(idx in correct_indices),
                                type='mcqtestcase'
                            )
            
            
            else:
                # --- Keep all the existing update logic here exactly as is ---
                # Get IDs of incoming test cases
                incoming_tc_ids = set()
                for tc_data in test_cases_data:
                    tc_id = tc_data.get('id')
                    if tc_id:
                        incoming_tc_ids.add(int(tc_id))
                
                # Get existing test case IDs
                existing_testcases = question.testcase_set.all()
                existing_tc_ids = {tc.id for tc in existing_testcases}
                
                # Delete test cases that are no longer in the incoming data
                testcases_to_delete = existing_tc_ids - incoming_tc_ids
                if testcases_to_delete:
                    from yaksh.models import TestCase
                    TestCase.objects.filter(id__in=testcases_to_delete).delete()
                
                # Update or create test cases
                for tc_data in test_cases_data:
                    tc_type = tc_data.get('type') or tc_data.get('test_case_type')
                    if not tc_type:
                        continue
                    
                    tc_id = tc_data.get('id')
                    
                    try:
                        model_class = get_model_class(tc_type)
                        
                        # Check if we're updating or creating
                        if tc_id and int(tc_id) in incoming_tc_ids:
                            # UPDATE existing test case
                            try:
                                tc_instance = model_class.objects.get(id=tc_id, question=question)
                                
                                if tc_type == 'mcqtestcase':
                                    options = tc_data.get('options', '')
                                    if isinstance(options, list):
                                        options = json.dumps(options)
                                    tc_instance.options = options
                                    
                                    # Handle correct field
                                    correct = tc_data.get('correct')
                                    if correct is not None:
                                        if isinstance(correct, list):
                                            tc_instance.correct = json.dumps(correct)
                                        else:
                                            tc_instance.correct = correct
                                
                                elif tc_type == 'stdiobasedtestcase':
                                    tc_instance.expected_input = tc_data.get('expected_input', '')
                                    tc_instance.expected_output = tc_data.get('expected_output', '')
                                    tc_instance.weight = float(tc_data.get('weight', 1.0))
                                    tc_instance.hidden = tc_data.get('hidden', False)
                                
                                elif tc_type == 'standardtestcase':
                                    tc_instance.test_case = tc_data.get('test_case', '')
                                    tc_instance.weight = float(tc_data.get('weight', 1.0))
                                    tc_instance.hidden = tc_data.get('hidden', False)
                                    tc_instance.test_case_args = tc_data.get('test_case_args', '')
                                
                                elif tc_type == 'integertestcase':
                                    tc_instance.correct = tc_data.get('correct')
                                
                                elif tc_type == 'stringtestcase':
                                    tc_instance.correct = tc_data.get('correct', '')
                                    tc_instance.string_check = tc_data.get('string_check', 'lower')
                                
                                elif tc_type == 'floattestcase':
                                    tc_instance.correct = tc_data.get('correct')
                                    tc_instance.error_margin = tc_data.get('error_margin', 0.0)
                                
                                elif tc_type == 'arrangetestcase':
                                    options = tc_data.get('options', '')
                                    if isinstance(options, list):
                                        options = json.dumps(options)
                                    tc_instance.options = options
                                
                                elif tc_type == 'uploadtestcase':
                                    tc_instance.description = tc_data.get('description', '')
                                    tc_instance.required = tc_data.get('required', True)
                                
                                tc_instance.save()
                                
                            except model_class.DoesNotExist:
                                print(f"Test case with id {tc_id} not found, will create new one")
                                tc_id = None  # Force creation
                        
                        # CREATE new test case if no ID or ID not found
                        if not tc_id or int(tc_id) not in incoming_tc_ids:
                            create_data = {'question': question, 'type': tc_type}
                            
                            if tc_type == 'mcqtestcase':
                                options = tc_data.get('options', '')
                                if isinstance(options, list):
                                    options = json.dumps(options)
                                create_data['options'] = options
                                
                                correct = tc_data.get('correct')
                                if correct is not None:
                                    if isinstance(correct, list):
                                        create_data['correct'] = json.dumps(correct)
                                    else:
                                        create_data['correct'] = correct
                            
                            elif tc_type == 'stdiobasedtestcase':
                                create_data.update({
                                    'expected_input': tc_data.get('expected_input', ''),
                                    'expected_output': tc_data.get('expected_output', ''),
                                    'weight': float(tc_data.get('weight', 1.0)),
                                    'hidden': tc_data.get('hidden', False)
                                })
                            
                            elif tc_type == 'standardtestcase':
                                create_data.update({
                                    'test_case': tc_data.get('test_case', ''),
                                    'weight': float(tc_data.get('weight', 1.0)),
                                    'hidden': tc_data.get('hidden', False),
                                    'test_case_args': tc_data.get('test_case_args', '')
                                })
                            
                            elif tc_type == 'integertestcase':
                                create_data['correct'] = tc_data.get('correct')
                            
                            elif tc_type == 'stringtestcase':
                                create_data.update({
                                    'correct': tc_data.get('correct', ''),
                                    'string_check': tc_data.get('string_check', 'lower')
                                })
                            
                            elif tc_type == 'floattestcase':
                                create_data.update({
                                    'correct': tc_data.get('correct'),
                                    'error_margin': tc_data.get('error_margin', 0.0)
                                })
                            
                            elif tc_type == 'arrangetestcase':
                                options = tc_data.get('options', '')
                                if isinstance(options, list):
                                    options = json.dumps(options)
                                create_data['options'] = options
                            
                            elif tc_type == 'uploadtestcase':
                                create_data.update({
                                    'description': tc_data.get('description', ''),
                                    'required': tc_data.get('required', True)
                                })
                            
                            model_class.objects.create(**create_data)
                            
                    except Exception as e:
                        print(f"Error updating/creating test case: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
        
        # Reload question to get updated test cases
        question.refresh_from_db()
        serializer = QuestionSerializer(question, context={'request': request})
        return Response(serializer.data)
        
    except Question.DoesNotExist:
        return Response(
            {'error': 'Question not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to update question', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def teacher_delete_question(request, question_id):
    """Delete a question"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        question = Question.objects.get(id=question_id)
        
        # Verify ownership
        if question.user != user:
            return Response(
                {'error': 'You do not have permission to delete this question'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete question (cascade will delete test cases)
        question.delete()
        
        return Response({
            'message': 'Question deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Question.DoesNotExist:
        return Response(
            {'error': 'Question not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to delete question', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

from yaksh.file_utils import extract_files
from django.http import HttpResponse
import zipfile
import os


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_upload_questions(request):
    """Bulk upload questions from YAML or ZIP file"""
    user = request.user
    
    if not is_moderator(user):
        return Response(
            {'error': 'You are not allowed to upload questions'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    questions_file = request.FILES['file']
    file_extension = questions_file.name.split('.')[-1].lower()
    
    try:
        ques = Question()
        
        if file_extension == "zip":
            # Handle ZIP file with YAML and associated files
            files, extract_path = extract_files(questions_file)
            message = ques.read_yaml(extract_path, user, files)
        elif file_extension in ["yaml", "yml"]:
            # Handle standalone YAML file
            questions = questions_file.read()
            message = ques.load_questions(questions, user)
        else:
            return Response(
                {'error': 'Please upload a ZIP file or YAML file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_question_template(request):
    """Download YAML template for question format"""
    user = request.user
    
    if not is_moderator(user):
        return Response(
            {'error': 'You are not allowed to access this resource'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        template_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "yaksh", 
            "fixtures",
            "demo_questions.zip"
        )
        
        if not os.path.exists(template_path):
            return Response(
                {'error': 'Template file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        yaml_file = zipfile.ZipFile(template_path, 'r')
        template_yaml = yaml_file.open('questions_dump.yaml', 'r')
        
        response = HttpResponse(template_yaml, content_type='text/yaml')
        response['Content-Disposition'] = 'attachment; filename="questions_dump.yaml"'
        return response
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )        



# ============================================================
#  QUESTION-TO-QUIZ MANAGEMENT APIs
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_get_quiz_questions(request, quiz_id):
    """Get all questions in a quiz"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        
        # Verify ownership
        if quiz.creator != user:
            return Response(
                {'error': 'You do not have permission to access this quiz'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create question paper
        question_paper, created = QuestionPaper.objects.get_or_create(quiz=quiz)
        
        # Get fixed questions in order
        fixed_questions = []
        all_fixed_questions = list(question_paper.fixed_questions.all())
        
        if question_paper.fixed_question_order:
            # Use order if available
            question_ids = [qid.strip() for qid in question_paper.fixed_question_order.split(',') if qid.strip()]
            question_map = {str(q.id): q for q in all_fixed_questions}
            
            # Add questions in order
            for qid in question_ids:
                if qid in question_map:
                    q = question_map[qid]
                    fixed_questions.append({
                        'id': q.id,
                        'summary': q.summary,
                        'type': q.type,
                        'points': q.points,
                        'order': len(fixed_questions) + 1
                    })
            
            # Add any questions not in the order string (shouldn't happen, but safety check)
            ordered_ids = set(question_ids)
            for q in all_fixed_questions:
                if str(q.id) not in ordered_ids:
                    fixed_questions.append({
                        'id': q.id,
                        'summary': q.summary,
                        'type': q.type,
                        'points': q.points,
                        'order': len(fixed_questions) + 1
                    })
        else:
            # No order specified, use all questions in their current order
            for q in all_fixed_questions:
                fixed_questions.append({
                    'id': q.id,
                    'summary': q.summary,
                    'type': q.type,
                    'points': q.points,
                    'order': len(fixed_questions) + 1
                })
        
        # Get random question sets
        random_sets = []
        for qset in question_paper.random_questions.all():
            random_sets.append({
                'id': qset.id,
                'marks': qset.marks,
                'num_questions': qset.num_questions,
                'questions_count': qset.questions.count()
            })
        
        return Response({
            'quiz_id': quiz.id,
            'question_paper_id': question_paper.id,
            'fixed_questions': fixed_questions,
            'random_questions': random_sets,
            'total_marks': question_paper.total_marks,
            'shuffle_questions': question_paper.shuffle_questions
        }, status=status.HTTP_200_OK)
        
    except Quiz.DoesNotExist:
        return Response(
            {'error': 'Quiz not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_add_question_to_quiz(request, quiz_id):
    """Add a question to quiz's question paper"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        question_id = request.data.get('question_id')
        fixed = request.data.get('fixed', True)
        
        if not question_id:
            return Response(
                {'error': 'question_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify ownership
        if quiz.creator != user:
            return Response(
                {'error': 'You do not have permission to modify this quiz'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        question = Question.objects.get(id=question_id)
        
        # Get or create question paper
        question_paper, created = QuestionPaper.objects.get_or_create(quiz=quiz)
        
        if fixed:
            # Add to fixed questions
            if question not in question_paper.fixed_questions.all():
                question_paper.fixed_questions.add(question)
                
                # Update order
                if question_paper.fixed_question_order:
                    question_paper.fixed_question_order += f",{question_id}"
                else:
                    question_paper.fixed_question_order = str(question_id)
                
                question_paper.update_total_marks()
                question_paper.save()
        else:
            # For random questions, need to create/update QuestionSet
            marks = request.data.get('marks', question.points)
            num_questions = request.data.get('num_questions', 1)
            question_set_id = request.data.get('question_set_id')
            
            if question_set_id:
                qset = QuestionSet.objects.get(id=question_set_id)
            else:
                qset = QuestionSet.objects.create(
                    marks=marks,
                    num_questions=num_questions
                )
                question_paper.random_questions.add(qset)
            
            if question not in qset.questions.all():
                qset.questions.add(question)
                qset.save()
        
        return Response({
            'message': 'Question added to quiz successfully',
            'question_id': question_id
        }, status=status.HTTP_200_OK)
        
    except Quiz.DoesNotExist:
        return Response(
            {'error': 'Quiz not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Question.DoesNotExist:
        return Response(
            {'error': 'Question not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to add question to quiz', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def teacher_remove_question_from_quiz(request, quiz_id, question_id):
    """Remove a question from quiz's question paper"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        
        # Verify ownership
        if quiz.creator != user:
            return Response(
                {'error': 'You do not have permission to modify this quiz'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        question_paper = QuestionPaper.objects.filter(quiz=quiz).first()
        if not question_paper:
            return Response(
                {'error': 'Question paper not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        question = Question.objects.get(id=question_id)
        
        # Remove from fixed questions
        if question in question_paper.fixed_questions.all():
            question_paper.fixed_questions.remove(question)
            
            # Update order
            if question_paper.fixed_question_order:
                order_list = question_paper.fixed_question_order.split(',')
                order_list = [qid for qid in order_list if qid != str(question_id)]
                question_paper.fixed_question_order = ','.join(order_list)
            
            question_paper.update_total_marks()
            question_paper.save()
        
        # Also check random question sets
        for qset in question_paper.random_questions.all():
            if question in qset.questions.all():
                qset.questions.remove(question)
                qset.save()
                # Delete question set if empty
                if qset.questions.count() == 0:
                    question_paper.random_questions.remove(qset)
                    qset.delete()
        
        return Response({
            'message': 'Question removed from quiz successfully'
        }, status=status.HTTP_200_OK)
        
    except Quiz.DoesNotExist:
        return Response(
            {'error': 'Quiz not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to remove question from quiz', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def teacher_reorder_quiz_questions(request, quiz_id):
    """Reorder questions in quiz"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        
        # Verify ownership
        if quiz.creator != user:
            return Response(
                {'error': 'You do not have permission to modify this quiz'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        question_paper = QuestionPaper.objects.filter(quiz=quiz).first()
        if not question_paper:
            return Response(
                {'error': 'Question paper not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        question_order = request.data.get('question_order', [])
        if question_order:
            # Validate all question IDs belong to this question paper
            question_ids = [str(qid) for qid in question_order]
            valid_questions = question_paper.fixed_questions.filter(
                id__in=question_ids
            )
            
            if valid_questions.count() != len(question_ids):
                return Response(
                    {'error': 'Some question IDs are invalid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            question_paper.fixed_question_order = ','.join(question_ids)
            question_paper.save()
        
        return Response({
            'message': 'Question order updated successfully'
        }, status=status.HTTP_200_OK)
        
    except Quiz.DoesNotExist:
        return Response(
            {'error': 'Quiz not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to reorder questions', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
#  ENROLLMENT MANAGEMENT APIs
# ============================================================



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_get_course_enrollments(request, course_id):
    """Get all enrollments for a course (enrolled, pending, rejected) with user details."""
    user = request.user
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    # Enrolled students with progress/grade
    enrolled = []
    for student in course.get_enrolled():
        try:
            cs = CourseStatus.objects.get(course=course, user=student)
            progress = cs.percent_completed
            grade = cs.grade
        except CourseStatus.DoesNotExist:
            progress = 0
            grade = None
        data = SimpleUserSerializer(student).data
        data['progress'] = progress
        data['grade'] = grade
        enrolled.append(data)

    # Pending requests
    requested = [SimpleUserSerializer(u).data for u in course.get_requests()]

    # Rejected students
    rejected = [SimpleUserSerializer(u).data for u in course.get_rejected()]

    return Response({
        'course_id': course.id,
        'course_name': course.name,
        'enrolled': enrolled,
        'pending_requests': requested,
        'rejected': rejected,
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_approve_enrollment(request, course_id):
    """
    Approve one or more users (from requested or rejected) for enrollment.
    Accepts: { "user_ids": [1,2,3] }
    """
    user = request.user
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
    user_ids = request.data.get('user_ids', [])
    if not user_ids:
        return Response({'error': 'No user_ids provided'}, status=status.HTTP_400_BAD_REQUEST)
    users = User.objects.filter(id__in=user_ids)
    enrolled_users = []
    for student in users:
        course.requests.remove(student)
        course.rejected.remove(student)
        course.students.add(student)
        CourseStatus.objects.get_or_create(course=course, user=student)
        enrolled_users.append(SimpleUserSerializer(student).data)
    return Response({'success': True, 'enrolled': enrolled_users}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_reject_enrollment(request, course_id):
    """
    Reject one or more users (from requested or enrolled).
    Accepts: { "user_ids": [1,2,3] }
    """
    user = request.user
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
    user_ids = request.data.get('user_ids', [])
    if not user_ids:
        return Response({'error': 'No user_ids provided'}, status=status.HTTP_400_BAD_REQUEST)
    users = User.objects.filter(id__in=user_ids)
    rejected_users = []
    for student in users:
        course.requests.remove(student)
        course.students.remove(student)
        course.rejected.add(student)
        rejected_users.append(SimpleUserSerializer(student).data)
    return Response({'success': True, 'rejected': rejected_users}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_remove_enrollment(request, course_id):
    """
    Remove one or more users from enrolled list.
    Accepts: { "user_ids": [1,2,3] }
    """
    user = request.user
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
    user_ids = request.data.get('user_ids', [])
    if not user_ids:
        return Response({'error': 'No user_ids provided'}, status=status.HTTP_400_BAD_REQUEST)
    users = User.objects.filter(id__in=user_ids)
    removed_users = []
    for student in users:
        course.students.remove(student)
        removed_users.append(SimpleUserSerializer(student).data)
    return Response({'success': True, 'removed': removed_users}, status=status.HTTP_200_OK)


# ============================================================
#  TEACHER/TA MANAGEMENT APIs
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def teacher_search_teachers(request, course_id):
    """Search for teachers/TAs to add to a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify teacher owns the course
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to access this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get search query from GET or POST
        search_query = request.GET.get('query') or request.data.get('query') or request.data.get('uname')
        
        if not search_query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search for users matching the query
        # Exclude: current user, superusers, course creator, and already added teachers
        existing_teacher_ids = list(course.teachers.values_list('id', flat=True))
        
        teachers = User.objects.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        ).exclude(
            Q(id=user.id) |
            Q(is_superuser=True) |
            Q(id=course.creator.id) |
            Q(id__in=existing_teacher_ids)
        )
        
        # Serialize teacher data
        teachers_data = []
        for teacher in teachers:
            try:
                profile = teacher.profile
                teachers_data.append({
                    'id': teacher.id,
                    'username': teacher.username,
                    'first_name': teacher.first_name,
                    'last_name': teacher.last_name,
                    'email': teacher.email,
                    'institute': profile.institute if hasattr(profile, 'institute') else '',
                    'department': profile.department if hasattr(profile, 'department') else '',
                    'position': profile.position if hasattr(profile, 'position') else '',
                    'is_moderator': profile.is_moderator if hasattr(profile, 'is_moderator') else False
                })
            except Profile.DoesNotExist:
                # Include users without profile but with basic info
                teachers_data.append({
                    'id': teacher.id,
                    'username': teacher.username,
                    'first_name': teacher.first_name,
                    'last_name': teacher.last_name,
                    'email': teacher.email,
                    'institute': '',
                    'department': '',
                    'position': '',
                    'is_moderator': False
                })
        
        return Response({
            'success': True,
            'count': len(teachers_data),
            'teachers': teachers_data
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_get_course_teachers(request, course_id):
    """Get list of current teachers/TAs for a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify teacher owns the course
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to access this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all teachers
        teachers = course.get_teachers()
        
        # Serialize teacher data
        teachers_data = []
        for teacher in teachers:
            try:
                profile = teacher.profile
                teachers_data.append({
                    'id': teacher.id,
                    'username': teacher.username,
                    'first_name': teacher.first_name,
                    'last_name': teacher.last_name,
                    'email': teacher.email,
                    'institute': profile.institute if hasattr(profile, 'institute') else '',
                    'department': profile.department if hasattr(profile, 'department') else '',
                    'position': profile.position if hasattr(profile, 'position') else '',
                    'is_moderator': profile.is_moderator if hasattr(profile, 'is_moderator') else False
                })
            except Profile.DoesNotExist:
                teachers_data.append({
                    'id': teacher.id,
                    'username': teacher.username,
                    'first_name': teacher.first_name,
                    'last_name': teacher.last_name,
                    'email': teacher.email,
                    'institute': '',
                    'department': '',
                    'position': '',
                    'is_moderator': False
                })
        
        return Response({
            'course_id': course.id,
            'course_name': course.name,
            'count': len(teachers_data),
            'teachers': teachers_data
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_add_teachers(request, course_id):
    """Add teachers/TAs to a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify teacher owns the course
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to modify this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get teacher IDs from request
        teacher_ids = request.data.get('teacher_ids', [])
        if not teacher_ids:
            return Response(
                {'error': 'teacher_ids is required and cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get teacher users
        teachers = User.objects.filter(id__in=teacher_ids)
        
        if teachers.count() != len(teacher_ids):
            return Response(
                {'error': 'Some teacher IDs are invalid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add as moderators (sets is_moderator=True on their profiles)
        try:
            add_as_moderator(teachers)
        except Http404 as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add teachers to course
        course.add_teachers(*teachers)
        
        # Serialize added teachers
        added_teachers = []
        for teacher in teachers:
            added_teachers.append({
                'id': teacher.id,
                'username': teacher.username,
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'email': teacher.email
            })
        
        return Response({
            'success': True,
            'message': f'Successfully added {len(added_teachers)} teacher(s) to the course',
            'teachers_added': added_teachers
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to add teachers', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def teacher_remove_teachers(request, course_id):
    """Remove teachers/TAs from a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify teacher owns the course
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to modify this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get teacher IDs from request (support both DELETE body and POST data)
        teacher_ids = request.data.get('teacher_ids', [])
        if not teacher_ids:
            return Response(
                {'error': 'teacher_ids is required and cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get teacher users
        teachers = User.objects.filter(id__in=teacher_ids)
        
        if teachers.count() == 0:
            return Response(
                {'error': 'No valid teachers found to remove'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove teachers from course
        course.remove_teachers(*teachers)
        
        # Serialize removed teachers
        removed_teachers = []
        for teacher in teachers:
            removed_teachers.append({
                'id': teacher.id,
                'username': teacher.username,
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'email': teacher.email
            })
        
        return Response({
            'success': True,
            'message': f'Successfully removed {len(removed_teachers)} teacher(s) from the course',
            'teachers_removed': removed_teachers
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to remove teachers', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
#  LEARNING UNIT ORDERING APIs
# ============================================================

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def teacher_reorder_module_units(request, module_id):
    """Reorder learning units within a module"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        module = LearningModule.objects.get(id=module_id)
        
        # Verify teacher owns the course - find course that contains this module
        course = Course.objects.filter(learning_module=module).first()
        if not course or (course.creator != user and user not in course.teachers.all()):
            return Response(
                {'error': 'You do not have permission to modify this module'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        unit_orders = request.data.get('unit_orders', [])
        if not unit_orders:
            return Response(
                {'error': 'unit_orders is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update order for each unit
        for unit_order in unit_orders:
            unit_id = unit_order.get('unit_id')
            order = unit_order.get('order')
            
            if unit_id is None or order is None:
                continue
            
            # Try to find as lesson
            try:
                lesson = Lesson.objects.get(id=unit_id, learning_module=module)
                lesson.order = order
                lesson.save()
            except Lesson.DoesNotExist:
                # Try to find as quiz
                try:
                    quiz = Quiz.objects.get(id=unit_id, learning_module=module)
                    # Get the learning unit for this quiz
                    learning_unit = LearningUnit.objects.filter(
                        quiz=quiz, learning_module=module
                    ).first()
                    if learning_unit:
                        learning_unit.order = order
                        learning_unit.save()
                except Quiz.DoesNotExist:
                    continue
        
        return Response({
            'message': 'Unit order updated successfully'
        }, status=status.HTTP_200_OK)
        
    except LearningModule.DoesNotExist:
        return Response(
            {'error': 'Module not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to reorder units', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def teacher_reorder_course_modules(request, course_id):
    """Reorder modules within a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify teacher owns the course
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to modify this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        module_orders = request.data.get('module_orders', [])
        if not module_orders:
            return Response(
                {'error': 'module_orders is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update order for each module
        for module_order in module_orders:
            module_id = module_order.get('module_id')
            order = module_order.get('order')
            
            if module_id is None or order is None:
                continue
            
            try:
                module = LearningModule.objects.get(id=module_id)
                # Verify module belongs to course
                if module in course.learning_module.all():
                    module.order = order
                    module.save()
            except LearningModule.DoesNotExist:
                continue
        
        return Response({
            'message': 'Module order updated successfully'
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to reorder modules', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
#  COURSE ANALYTICS APIs
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_get_course_analytics(request, course_id):
    """Get comprehensive analytics for a course"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify teacher owns the course
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to access this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get enrolled students
        enrolled_students = course.students.all()
        total_students = enrolled_students.count()
        
        # Get course statuses for progress calculation
        course_statuses = CourseStatus.objects.filter(course=course)
        
        # Calculate completion rate
        completed_count = course_statuses.filter(percent_completed=100).count()
        completion_rate = (completed_count / total_students * 100) if total_students > 0 else 0
        
        # Calculate average score
        avg_score = course_statuses.aggregate(
            avg=Avg('percentage', output_field=FloatField())
        )['avg'] or 0
        
        # Module statistics
        modules = course.get_learning_modules()
        module_stats = []
        for module in modules:
            # Get units from the module (reverse relationship)
            module_units = module.learning_unit.all()
            total_units = module_units.count()
            
            if total_units == 0:
                continue
            
            # Count students who completed all units in this module
            students_completed = 0
            # Get all unit IDs for this module
            module_unit_ids = list(module.learning_unit.values_list('id', flat=True))
            
            for student in enrolled_students:
                try:
                    cs = CourseStatus.objects.get(course=course, user=student)
                    # Filter completed units that belong to this module
                    completed_units_count = cs.completed_units.filter(id__in=module_unit_ids).count()
                    if completed_units_count == total_units:
                        students_completed += 1
                except CourseStatus.DoesNotExist:
                    continue
            
            module_completion_rate = (students_completed / total_students * 100) if total_students > 0 else 0
            
            module_stats.append({
                'module_id': module.id,
                'module_name': module.name,
                'completion_rate': round(module_completion_rate, 2),
                'students_completed': students_completed,
                'total_units': total_units
            })
        
        # Quiz statistics
        quizzes = course.get_quizzes()
        quiz_stats = []
        for quiz in quizzes:
            # Get all answer papers for this quiz
            answer_papers = AnswerPaper.objects.filter(
                question_paper__quiz=quiz,
                course=course,
                status='completed'
            )
            
            total_attempts = answer_papers.count()
            
            if total_attempts > 0:
                # Calculate average score
                avg_score_quiz = answer_papers.aggregate(
                    avg=Avg('percent', output_field=FloatField())
                )['avg'] or 0
                
                # Calculate pass rate
                passed_count = answer_papers.filter(passed=True).count()
                pass_rate = (passed_count / total_attempts * 100) if total_attempts > 0 else 0
                
                # Get question paper for total questions
                try:
                    question_paper = QuestionPaper.objects.get(quiz=quiz)
                    total_questions = question_paper.fixed_questions.count()
                except QuestionPaper.DoesNotExist:
                    total_questions = 0
                
                quiz_stats.append({
                    'quiz_id': quiz.id,
                    'quiz_name': quiz.description,
                    'total_attempts': total_attempts,
                    'average_score': round(avg_score_quiz, 2),
                    'pass_rate': round(pass_rate, 2),
                    'total_questions': total_questions
                })
        
        # Top students (by course completion percentage)
        top_students_data = []
        for cs in course_statuses.order_by('-percentage')[:5]:
            student = cs.user
            top_students_data.append({
                'user_id': student.id,
                'username': student.username,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'score': round(cs.percentage, 2),
                'grade': cs.grade or 'N/A',
                'completion': cs.percent_completed
            })
        
        # Question statistics (for quizzes in this course)
        question_stats = []
        for quiz in quizzes:
            try:
                question_paper = QuestionPaper.objects.get(quiz=quiz)
                questions = question_paper.fixed_questions.all()
                
                for question in questions:
                    # Get all answer papers that attempted this question
                    answer_papers_with_q = AnswerPaper.objects.filter(
                        question_paper=question_paper,
                        course=course,
                        questions=question,
                        status='completed'
                    )
                    
                    total_attempts_q = answer_papers_with_q.count()
                    
                    if total_attempts_q > 0:
                        # Count correct answers (simplified - check if marks > 0)
                        correct_attempts = answer_papers_with_q.filter(
                            answers__question=question,
                            answers__correct=True
                        ).distinct().count()
                        
                        # Calculate average score for this question
                        question_answers = Answer.objects.filter(
                            answerpaper__in=answer_papers_with_q,
                            question=question
                        )
                        avg_question_score = question_answers.aggregate(
                            avg=Avg('marks', output_field=FloatField())
                        )['avg'] or 0
                        
                        question_stats.append({
                            'question_id': question.id,
                            'summary': question.summary,
                            'quiz_id': quiz.id,
                            'quiz_name': quiz.description,
                            'average_score': round(avg_question_score, 2),
                            'attempts': total_attempts_q,
                            'correct_attempts': correct_attempts
                        })
            except QuestionPaper.DoesNotExist:
                continue
        
        # Enrollment trends (last 30 days)
        # Note: Since ManyToManyField doesn't track enrollment dates by default,
        # we'll show the total enrolled count for each day (simplified)
        enrollment_trends = []
        today = timezone.now().date()
        total_enrolled = course.students.count()
        for i in range(29, -1, -1):
            date = today - timedelta(days=i)
            # For now, show total enrolled (can be enhanced with enrollment tracking later)
            enrollment_trends.append({
                'date': date.isoformat(),
                'enrolled': total_enrolled
            })
        
        return Response({
            'course_id': course.id,
            'course_name': course.name,
            'total_students': total_students,
            'enrolled_students': total_students,
            'completion_rate': round(completion_rate, 2),
            'average_score': round(avg_score, 2),
            'module_stats': module_stats,
            'quiz_stats': quiz_stats,
            'top_students': top_students_data,
            'question_statistics': question_stats[:20],  # Limit to top 20
            'enrollment_trends': enrollment_trends
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to get analytics', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
#  SEND MAIL APIs
# ============================================================


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_send_mail(request, course_id):
    try:
        user = request.user
        # if not user.is_teacher:
        #     return Response({'error': 'Only teachers can perform this action'}, 
        #                   status=status.HTTP_403_FORBIDDEN)

        course = get_object_or_404(Course, pk=course_id)
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response({'error': 'This course does not belong to you'}, 
                          status=status.HTTP_403_FORBIDDEN)

        data = request.data
        subject = data.get('subject')
        body = data.get('body')
        recipient_ids = data.get('recipients', []) # List of user IDs

        if not subject or not body:
            return Response({'error': 'Subject and Body are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if not recipient_ids:
            return Response({'error': 'At least one recipient is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Filter recipients to ensure they exist
        users = User.objects.filter(id__in=recipient_ids)
        recipients = [u.email for u in users if u.email]
        
        # Handle attachments if any (standard Django request.FILES)
        attachments = request.FILES.getlist('email_attach')

        # Send mail using the utility function
        # Message returned is a success string or error string
        message = send_bulk_mail(subject, body, recipients, attachments)

        if "Error" in message:
             return Response({'error': message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': message}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_quizzes_grouped(request):
    """Get all quizzes grouped by course for the teacher"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get all courses created by or where user is a teacher
    courses = Course.objects.filter(
        Q(creator=user) | Q(teachers=user),
        is_trial=False
    ).distinct().order_by('-created_on')
    
    response_data = []
    
    for course in courses:
        # Get all quizzes for this course
        # Structure: Course -> LearningModule -> LearningUnit(quiz)
        quizzes_data = []
        
        modules = course.learning_module.all().order_by('order')
        for module in modules:
            # Filter for quiz units
            quiz_units = module.learning_unit.filter(type='quiz').order_by('order')
            
            for unit in quiz_units:
                if unit.quiz:
                    quiz = unit.quiz
                    
                    # Calculate stats for the quiz
                    # Total attempts (unique students)
                    total_attempts = AnswerPaper.objects.filter(
                        question_paper__quiz=quiz,
                        course=course
                    ).values('user').distinct().count()
                    
                    quizzes_data.append({
                        'id': quiz.id,
                        'name': quiz.description or f"Quiz {quiz.id}",
                        'module_id': module.id,
                        'module_name': module.name,
                        'unit_order': unit.order,
                        'duration': quiz.duration,
                        'attempts': total_attempts,
                        'start_date': quiz.start_date_time,
                        'active': quiz.active,
                        'is_exercise': quiz.is_exercise,
                        'created_at': quiz.start_date_time # Using start time as proxy for creation or relevance
                    })
        
        if quizzes_data:
            response_data.append({
                'course_id': course.id,
                'course_name': course.name,
                'course_code': course.code,
                'quizzes': quizzes_data
            })
            
    return Response(response_data, status=status.HTTP_200_OK)


class GradingSystemListCreateView(generics.ListCreateAPIView):
    queryset = GradingSystem.objects.all()
    serializer_class = GradingSystemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class GradingSystemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GradingSystem.objects.all()
    serializer_class = GradingSystemSerializer
    permission_classes = [permissions.IsAuthenticated]





# --- Course Forum Views  ---
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` or `creator` attribute.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Instance must have an attribute named `creator`.
        return obj.creator == request.user or is_moderator(request.user)

# --- Course Forum Views ---

class ForumPostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_course(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, pk=course_id)
        user = self.request.user
        # Strict enrollment check
        if not (course.is_student(user) or course.is_teacher(user) or course.is_creator(user) or is_moderator(user)):
             raise PermissionDenied("You are not enrolled in this course.")
        return course

    def get_queryset(self):
        course = self.get_course()
        course_ct = ContentType.objects.get_for_model(Course)
        
        # We retrieve both correctly tagged posts AND posts that might correspond to this ID 
        # but are missing the ContentType tag (legacy data support)
        # WARNING: Ideally we should migrate the data, but this allows viewing the old broken posts
        return Post.objects.filter(
            target_id=course.id, 
            active=True
        ).filter(
            Q(target_ct=course_ct) | Q(target_ct__isnull=True)
        ).order_by('-modified_at')

    def perform_create(self, serializer):
        course = self.get_course()
        course_ct = ContentType.objects.get_for_model(Course)
        # Handle Anonymous posts
        is_anonymous = self.request.data.get('anonymous') == 'true' or self.request.data.get('anonymous') == True
        
        serializer.save(
            creator=self.request.user, 
            target_id=course.id, 
            target_ct=course_ct, 
            active=True,
            anonymous=is_anonymous
        )

class ForumPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        # Relaxed filtering to allow Deleting/Getting the legacy (null CT) posts too
        return Post.objects.filter(target_id=course_id, active=True)

class ForumCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        # Check if user has access to the course of this post (if linked)
        # This is a bit expensive but necessary for security
        return Comment.objects.filter(post_field_id=post_id, active=True).order_by('created_at')

    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, pk=post_id)
        
        # Security: Check if user is enrolled in the course this post belongs to
        if post.target_ct and post.target_ct.model == 'course':
             course = Course.objects.get(id=post.target_id)
             user = self.request.user
             if not (course.is_student(user) or course.is_teacher(user) or course.is_creator(user) or is_moderator(user)):
                 raise PermissionDenied("You do not have permission to comment in this course.")

        is_anonymous = self.request.data.get('anonymous') == 'true' or self.request.data.get('anonymous') == True
        serializer.save(creator=self.request.user, post_field_id=post_id, active=True, anonymous=is_anonymous)

class ForumCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'

    def get_queryset(self):
        return Comment.objects.filter(active=True)

# --- Lesson Forum Views ---

# ...existing code...
# --- Lesson Forum Views ---

class LessonForumPostListView(generics.ListAPIView):
    """
    Lists all lesson discussion threads for a specific COURSE.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_course(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, pk=course_id)
        user = self.request.user
        # Strict enrollment check
        if not (course.is_student(user) or course.is_teacher(user) or course.is_creator(user) or is_moderator(user)):
             raise PermissionDenied("You are not enrolled in this course.")
        return course

    def get_queryset(self):
        # We override list() to handle the list return, but get_queryset serves for structure
        return Post.objects.none()

    def list(self, request, *args, **kwargs):
        course = self.get_course()
        posts = course.get_lesson_posts() # Returns a list of Post objects
        
        # Deduplicate posts (Fix for lessons appearing in multiple units causing duplicates)
        unique_posts = []
        seen_ids = set()
        for post in posts:
            if post.id not in seen_ids:
                unique_posts.append(post)
                seen_ids.add(post.id)
                
        serializer = self.get_serializer(unique_posts, many=True)
        return Response(serializer.data)

class LessonForumPostDetailView(generics.RetrieveDestroyAPIView):
    """
    Retrieves the SINGLE discussion post for a specific LESSON in a COURSE context.
    Auto-creates it if it doesn't exist (on GET).
    Allows Teachers/Creators to delete (soft-delete) the post.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    # No lookup_field needed as we override get_object

    def get_object(self):
        from rest_framework.exceptions import PermissionDenied
        course_id = self.kwargs['course_id']
        lesson_id = self.kwargs['lesson_id']
        
        course = get_object_or_404(Course, pk=course_id)
        user = self.request.user
        if not (course.is_student(user) or course.is_teacher(user) or course.is_creator(user) or is_moderator(user)):
             raise PermissionDenied("You are not enrolled in this course.")

        lesson = get_object_or_404(Lesson, pk=lesson_id)
        lesson_ct = ContentType.objects.get_for_model(Lesson)

        # Match yaksh logic: Get or Create
        post = Post.objects.filter(
                target_ct=lesson_ct,
                target_id=lesson.id,
                active=True
            ).order_by('-created_at').first()
            
        if not post:
            if self.request.method == 'GET':
                title = lesson.name
                post = Post.objects.create(
                    target_ct=lesson_ct,
                    target_id=lesson.id,
                    active=True,
                    title=title,
                    creator=user,
                    description=f'Discussion on {title} lesson',
                )
            else:
                 raise Http404("Post not found")
        return post

    def perform_destroy(self, instance):
        from rest_framework.exceptions import PermissionDenied
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, pk=course_id)
        user = self.request.user
        
        # Only creators/teachers (or moderators) can delete the lesson forum post
        if not (course.is_creator(user) or course.is_teacher(user) or is_moderator(user)):
            raise PermissionDenied("Only a course creator or a teacher can delete the post.")
            
        instance.active = False
        instance.save()
        # Soft delete associated comments
        instance.comment.filter(active=True).update(active=False)

class LessonForumCommentListCreateView(generics.ListCreateAPIView):
    """
    List or Create comments for a specific LESSON.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, pk=course_id)
        user = self.request.user
        if not (course.is_student(user) or course.is_teacher(user) or course.is_creator(user) or is_moderator(user)):
             raise PermissionDenied("You are not enrolled in this course.")

        lesson_id = self.kwargs['lesson_id']
        lesson_ct = ContentType.objects.get_for_model(Lesson)
        post = Post.objects.filter(target_ct=lesson_ct, target_id=lesson_id, active=True).first()
        if not post:
             return Comment.objects.none()
        return Comment.objects.filter(post_field=post, active=True).order_by('created_at')

    def perform_create(self, serializer):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, pk=course_id)
        user = self.request.user
        if not (course.is_student(user) or course.is_teacher(user) or course.is_creator(user) or is_moderator(user)):
             raise PermissionDenied("You are not enrolled in this course.")
             
        lesson_id = self.kwargs['lesson_id']
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        lesson_ct = ContentType.objects.get_for_model(Lesson)
        title = lesson.name
        
        # Ensure post exists
        post, created = Post.objects.get_or_create(
            target_ct=lesson_ct,
            target_id=lesson.id,
            active=True,
            defaults={
                'title': title,
                'creator': user,
                'description': f'Discussion on {title} lesson'
            }
        )
        
        is_anonymous = self.request.data.get('anonymous') == 'true' or self.request.data.get('anonymous') == True
        serializer.save(creator=user, post_field=post, active=True, anonymous=is_anonymous)


class LessonForumCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'

    def get_queryset(self):
        # We can add course check here if we want strict read security on single comments
        # But generally identifying by ID and relying on IsOwnerOrReadOnly for writes is standard
        return Comment.objects.filter(active=True)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.active = False
        instance.save()






# ============================================================
#  DEMO COURSE API
# ============================================================

class CreateDemoCourseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """API endpoint to create a demo course for the user."""
        user = request.user
        if not is_moderator(user):
            return Response({"detail": "You are not allowed to view this page"}, status=status.HTTP_403_FORBIDDEN)
        demo_course = Course()
        success = demo_course.create_demo(user)
        if success:
            msg = "Created Demo course successfully"
        else:
            msg = "Demo course already created"
        return Response({"message": msg}, status=status.HTTP_200_OK)        

# ============================================================
# QUIZ APIs
# ============================================================


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_start_quiz(request, questionpaper_id, module_id, course_id, attempt_num=None):
    """
    Start or resume a quiz. Returns quiz intro or first question.
    Handles both students and teachers (trial mode).
    
    GET: Check if can start (returns intro page data)
    POST: Actually start the quiz (create answerpaper, return first question)
    """
    user = request.user
    
    # Check conditions - Get question paper
    try:
        quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
    except QuestionPaper.DoesNotExist:
        return Response({
            'error': 'Quiz not found, please contact your instructor/administrator.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if quiz has questions
    if not quest_paper.has_questions():
        return Response({
            'error': 'Quiz does not have questions, please contact your instructor/administrator.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get course, module, unit
    try:
        course = Course.objects.get(id=course_id)
        learning_module = course.learning_module.get(id=module_id)
        learning_unit = learning_module.learning_unit.get(quiz=quest_paper.quiz.id)
    except (Course.DoesNotExist, LearningModule.DoesNotExist, LearningUnit.DoesNotExist) as e:
        return Response({
            'error': 'Course, module, or unit not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if trial course (teacher testing mode)
    is_trial_mode = course.is_trial and is_moderator(user)
    
    # Validation checks (skip for trial mode)
    if not is_trial_mode:
        # Unit module active status
        if not learning_module.active:
            return Response({
                'error': f'Module {learning_module.name} is not active'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Unit module prerequisite check
        if learning_module.has_prerequisite():
            if not learning_module.is_prerequisite_complete(user, course):
                return Response({
                    'error': f'You have not completed the module previous to {learning_module.name}'
                }, status=status.HTTP_403_FORBIDDEN)
        
        if learning_module.check_prerequisite_passes:
            if not learning_module.is_prerequisite_passed(user, course):
                return Response({
                    'error': f'You have not successfully passed the module previous to {learning_module.name}'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Is user enrolled in the course
        if not course.is_enrolled(user):
            return Response({
                'error': f'You are not enrolled in {course.name} course'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # If course is active and not expired
        if not course.active or not course.is_active_enrollment():
            return Response({
                'error': f'{course.name} is either expired or not active'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Is quiz active and not expired
        if quest_paper.quiz.is_expired() or not quest_paper.quiz.active:
            return Response({
                'error': f'{quest_paper.quiz.description} is either expired or not active'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Prerequisite check and passing criteria for quiz
        if learning_unit.has_prerequisite():
            if not learning_unit.is_prerequisite_complete(user, learning_module, course):
                return Response({
                    'error': 'You have not completed the previous Lesson/Quiz/Exercise'
                }, status=status.HTTP_403_FORBIDDEN)
    
    from yaksh.views import _update_unit_status
    try:
        _update_unit_status(course_id, user, learning_unit)
    except CourseStatus.MultipleObjectsReturned:
        # Handle duplicate CourseStatus records
        course_status = CourseStatus.objects.filter(
            user=user, course_id=course_id
        ).order_by('id').first()
        
        # Delete duplicates
        CourseStatus.objects.filter(
            user=user, course_id=course_id
        ).exclude(id=course_status.id).delete()
        
        # Retry update
        _update_unit_status(course_id, user, learning_unit)
    
    # Check if any previous attempt
    last_attempt = AnswerPaper.objects.get_user_last_attempt(
        quest_paper, user, course_id
    )
    
        # If previous attempt is in progress, resume it
    if last_attempt and last_attempt.is_attempt_inprogress():
        current_q = last_attempt.current_question()
        
        if not current_q:
            return Response({
                'error': 'No questions available in this quiz'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Serialize question data with full details
        from api.serializers import QuestionSerializer
        question_serializer = QuestionSerializer(current_q)
        
        return Response({
            'status': 'resume',  # Changed from 'resume' to 'started'
            'message': 'Resuming previous attempt',  # Changed message
            'answerpaper_id': last_attempt.id,
            'attempt_number': last_attempt.attempt_number,
            'questionpaper_id': questionpaper_id,
            'module_id': module_id,
            'course_id': course_id,
            'current_question': question_serializer.data,  # Full question with test_cases and files
            'questions_answered': last_attempt.questions_answered.count(),
            'questions_unanswered': last_attempt.questions_unanswered.count(),
            'time_left': last_attempt.time_left(),
            'is_trial_mode': is_trial_mode,
        }, status=status.HTTP_200_OK)
    
    # Determine attempt number
    if last_attempt:
        attempt_number = last_attempt.attempt_number + 1
    else:
        attempt_number = 1
    
    # Check if allowed to start
    can_attempt, msg = quest_paper.can_attempt_now(user, course_id)
    if not can_attempt:
        return Response({
            'error': msg,
            'can_attempt': False
        }, status=status.HTTP_403_FORBIDDEN)
    
    # GET request: Return intro page data (don't create answerpaper yet)
    if request.method == 'GET':
        if attempt_num is None and not quest_paper.quiz.is_exercise:
            return Response({
                'status': 'intro',
                'quiz': {
                    'id': quest_paper.quiz.id,
                    'description': quest_paper.quiz.description,
                    'duration': quest_paper.quiz.duration,
                    'is_exercise': quest_paper.quiz.is_exercise,
                    'instructions': quest_paper.quiz.instructions,
                    'attempts_allowed': quest_paper.quiz.attempts_allowed,
                    'time_between_attempts': quest_paper.quiz.time_between_attempts,
                },
                'questionpaper': {
                    'id': quest_paper.id,
                    'total_marks': quest_paper.total_marks,
                    'total_questions': quest_paper.get_total_questions(),
                },
                'course': {
                    'id': course.id,
                    'name': course.name,
                },
                'module': {
                    'id': learning_module.id,
                    'name': learning_module.name,
                },
                'attempt_number': attempt_number,
                'is_trial_mode': is_trial_mode,
                'is_moderator': is_moderator(user),
            }, status=status.HTTP_200_OK)
    
    # POST request: Create answerpaper and start quiz
    if request.method == 'POST':
        # RECHECK if any attempt is in progress (in case of race conditions)
        last_attempt = AnswerPaper.objects.get_user_last_attempt(
            quest_paper, user, course_id
        )
        
        # If previous attempt is STILL in progress, resume it (don't create new one)
        if last_attempt and last_attempt.is_attempt_inprogress():
            current_q = last_attempt.current_question()
            
            if not current_q:
                return Response({
                    'error': 'No questions available in this quiz'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Serialize question data
            from api.serializers import QuestionSerializer
            question_serializer = QuestionSerializer(current_q)
            
            return Response({
                'status': 'started',  # Changed from 'resume' to match your desired response
                'message': 'Quiz started successfully',  # Changed message
                'answerpaper_id': last_attempt.id,
                'attempt_number': last_attempt.attempt_number,
                'questionpaper_id': questionpaper_id,
                'module_id': module_id,
                'course_id': course_id,
                'current_question': question_serializer.data,
                'questions_answered': last_attempt.questions_answered.count(),
                'questions_unanswered': last_attempt.questions_unanswered.count(),
                'time_left': last_attempt.time_left(),
                'is_trial_mode': is_trial_mode,
            }, status=status.HTTP_201_CREATED)  # Return 201 to match new quiz start
        
                # Get IP address
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        # Check if user has profile
        if not hasattr(user, 'profile'):
            return Response({
                'error': 'You do not have a profile and cannot take the quiz!'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new answerpaper with race condition handling
        try:
            new_paper = quest_paper.make_answerpaper(user, ip, attempt_number, course_id)
        except IntegrityError:
            # Race condition: Another request already created the answerpaper
            # Fetch the newly created answerpaper and return it
            last_attempt = AnswerPaper.objects.get_user_last_attempt(
                quest_paper, user, course_id
            )
            
            if last_attempt and last_attempt.is_attempt_inprogress():
                current_q = last_attempt.current_question()
                
                if not current_q:
                    return Response({
                        'error': 'No questions available in this quiz'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Serialize question data
                from api.serializers import QuestionSerializer
                question_serializer = QuestionSerializer(current_q)
                
                return Response({
                    'status': 'started',
                    'message': 'Quiz started successfully',
                    'answerpaper_id': last_attempt.id,
                    'attempt_number': last_attempt.attempt_number,
                    'questionpaper_id': questionpaper_id,
                    'module_id': module_id,
                    'course_id': course_id,
                    'current_question': question_serializer.data,
                    'questions_answered': last_attempt.questions_answered.count(),
                    'questions_unanswered': last_attempt.questions_unanswered.count(),
                    'time_left': last_attempt.time_left(),
                    'is_trial_mode': is_trial_mode,
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Failed to create or retrieve answerpaper'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if answerpaper was created successfully
        if new_paper.status == 'inprogress':
            current_q = new_paper.current_question()
            
            if not current_q:
                return Response({
                    'error': 'No questions available in this quiz'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Serialize question data
            from api.serializers import QuestionSerializer
            question_serializer = QuestionSerializer(current_q)
            
            return Response({
                'status': 'started',
                'message': 'Quiz started successfully',
                'answerpaper_id': new_paper.id,
                'attempt_number': new_paper.attempt_number,
                'questionpaper_id': questionpaper_id,
                'module_id': module_id,
                'course_id': course_id,
                'current_question': question_serializer.data,
                'questions_answered': new_paper.questions_answered.count(),
                'questions_unanswered': new_paper.questions_unanswered.count(),
                'time_left': new_paper.time_left(),
                'is_trial_mode': is_trial_mode,
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'You have already finished the quiz!',
                'status': new_paper.status
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def api_quit_quiz(request, attempt_num, module_id, questionpaper_id, course_id):
    """
    API endpoint to quit a quiz.
    GET: Retrieve quit information
    POST: Mark quiz as quit and return result
    """
    try:
        paper = AnswerPaper.objects.get(
            user=request.user,
            attempt_number=attempt_num,
            question_paper_id=questionpaper_id,
            course_id=course_id
        )
        
        if request.method == 'POST':
            # Get optional reason from request body
            reason = request.data.get('reason', None)
            
            # Mark the paper as quit if it's not already completed
            if paper.status == 'inprogress':
                paper.status = 'quit'
                paper.save()
            
            return Response({
                'message': reason or 'You have quit the quiz.',
                'paper': {
                    'id': paper.id,
                    'status': paper.status,
                    'attempt_number': paper.attempt_number,
                    'marks_obtained': paper.marks_obtained,
                    'percent': paper.percent,
                    'questions_answered': paper.questions_answered.count(),
                    'questions_unanswered': paper.questions_unanswered.count(),
                },
                'course_id': course_id,
                'module_id': module_id,
                'questionpaper_id': questionpaper_id
            }, status=status.HTTP_200_OK)
        
        else:  # GET request
            return Response({
                'paper': {
                    'id': paper.id,
                    'status': paper.status,
                    'attempt_number': paper.attempt_number,
                    'marks_obtained': paper.marks_obtained,
                    'percent': paper.percent,
                },
                'course_id': course_id,
                'module_id': module_id
            }, status=status.HTTP_200_OK)
            
    except AnswerPaper.DoesNotExist:
        return Response(
            {'error': 'Answer paper not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )  

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_complete_quiz(request, attempt_num=None, module_id=None, 
                      questionpaper_id=None, course_id=None):
    """
    API endpoint to complete/submit a quiz.
    GET: Retrieve completion information
    POST: Mark quiz as completed and return result with updated marks
    
    Handles two cases:
    1. Without parameters (error case)
    2. With all parameters (normal completion)
    """
    user = request.user
    
    # Handle error case (no parameters)
    if questionpaper_id is None:
        reason = request.data.get('reason') if request.method == 'POST' else request.GET.get('reason')
        message = reason or "An Unexpected Error occurred. Please contact your instructor/administrator."
        return Response({
            'error': True,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Normal completion flow with all parameters
    try:
        # Validate that the question paper exists
        try:
            q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        except QuestionPaper.DoesNotExist:
            return Response({
                'error': 'An Unexpected Error occurred. Please contact your instructor/administrator.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the answer paper
        try:
            paper = AnswerPaper.objects.get(
                user=user,
                question_paper=q_paper,
                attempt_number=attempt_num,
                course_id=course_id
            )
        except AnswerPaper.DoesNotExist:
            return Response({
                'error': 'Answer paper not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get course and learning module
        course = Course.objects.get(id=course_id)
        learning_module = course.learning_module.get(id=module_id)
        learning_unit = learning_module.learning_unit.get(quiz=q_paper.quiz)
        
        if request.method == 'POST':
            # Get optional reason from request body
            reason = request.data.get('reason', None)
            
            # Update marks and set end time
            paper.update_marks()
            paper.set_end_time(timezone.now())
            
            message = reason or "Quiz has been submitted"
            
            # Prepare response data
            response_data = {
                'message': message,
                'paper': {
                    'id': paper.id,
                    'status': paper.status,
                    'attempt_number': paper.attempt_number,
                    'marks_obtained': paper.marks_obtained,
                    'percent': paper.percent,
                    'questions_answered': paper.questions_answered.count(),
                    'questions_unanswered': paper.questions_unanswered.count(),
                    'start_time': paper.start_time,
                    'end_time': paper.end_time,
                    'time_taken': str(paper.time_taken) if paper.time_taken else None,
                },
                'course_id': int(course_id),
                'module_id': int(module_id),
                'learning_unit': {
                    'id': learning_unit.id,
                    'order': learning_unit.order,
                    'type': learning_unit.type,
                },
                'quiz': {
                    'id': q_paper.quiz.id,
                    'description': q_paper.quiz.description,
                },
            }
            
            # Add moderator flag if user is moderator
            if is_moderator(user):
                response_data['user_type'] = 'moderator'
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        else:  # GET request - retrieve completion info without updating
            return Response({
                'paper': {
                    'id': paper.id,
                    'status': paper.status,
                    'attempt_number': paper.attempt_number,
                    'marks_obtained': paper.marks_obtained,
                    'percent': paper.percent,
                    'questions_answered': paper.questions_answered.count(),
                    'questions_unanswered': paper.questions_unanswered.count(),
                    'start_time': paper.start_time,
                    'end_time': paper.end_time,
                },
                'course_id': int(course_id),
                'module_id': int(module_id),
                'learning_unit': {
                    'id': learning_unit.id,
                    'order': learning_unit.order,
                },
            }, status=status.HTTP_200_OK)
            
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except LearningModule.DoesNotExist:
        return Response(
            {'error': 'Learning module not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except LearningUnit.DoesNotExist:
        return Response(
            {'error': 'Learning unit not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )    

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def api_check_answer(request, q_id, attempt_num, module_id, questionpaper_id, course_id):
    """
    API endpoint to check/submit an answer for a question.
    POST: Submit answer and get validation result
    GET: Get current question state (for re-display)
    """
    user = request.user
    
    try:
        # Get the answer paper
        paper = AnswerPaper.objects.get(
            user=user,
            attempt_number=attempt_num,
            question_paper_id=questionpaper_id,
            course_id=course_id
        )
    except AnswerPaper.DoesNotExist:
        return Response({
            'error': 'Answer paper not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get the current question
    try:
        current_question = Question.objects.get(pk=q_id)
    except Question.DoesNotExist:
        return Response({
            'error': 'Question not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Helper function to validate answer
    def is_valid_answer(answer):
        if ((current_question.type == "mcc" or current_question.type == "arrange") and not answer):
            return False
        elif answer is None or not str(answer):
            return False
        return True
    
    # GET request - return current question state
    if request.method == 'GET':
        from api.serializers import QuestionSerializer
        question_serializer = QuestionSerializer(current_question)
        
        # Get previous answers if any
        previous_answers = paper.get_previous_answers(current_question)
        last_attempt = previous_answers[0].answer if previous_answers else None
        
        return Response({
            'question': question_serializer.data,
            'paper': {
                'id': paper.id,
                'status': paper.status,
                'time_left': paper.time_left(),
                'questions_answered': paper.questions_answered.count(),
                'questions_unanswered': paper.questions_unanswered.count(),
            },
            'last_attempt': last_attempt,
            'course_id': int(course_id),
            'module_id': int(module_id),
        }, status=status.HTTP_200_OK)
    
    # POST request - submit and check answer
    if request.method == 'POST':
        # Check if time is up or quiz completed
        if paper.time_left() <= -10 or paper.status == "completed":
            return Response({
                'error': 'Your time is up!',
                'time_up': True,
                'should_complete': True,
                'course_id': int(course_id),
                'module_id': int(module_id),
                'attempt_num': attempt_num,
                'questionpaper_id': int(questionpaper_id),
            }, status=status.HTTP_403_FORBIDDEN)
        
        user_answer = None
        
        # Parse answer based on question type
        try:
            if current_question.type in ['mcq', 'mcc']:
                answer_input = request.data.get('answer')
                
                # Retrieve the multiple options from the DB by sorting them out to match UI order
                test_cases = sorted(current_question.get_test_cases(), key=lambda x: x.id)
                
                if current_question.type == 'mcq':
                    user_answer = None
                    for tc in test_cases:
                        try:
                            # FOSSEE stores it strictly arrayified in JSON
                            opt_val = json.loads(tc.options)
                            opt_text = opt_val[0] if isinstance(opt_val, list) and opt_val else str(tc.options)
                        except Exception:
                            opt_text = str(tc.options)
                            
                        if opt_text == answer_input:
                            user_answer = str(tc.id)
                            break
                            
                elif current_question.type == 'mcc':
                    answer_input = answer_input if isinstance(answer_input, list) else [answer_input]
                    user_answer = []
                    for tc in test_cases:
                        try:
                            opt_val = json.loads(tc.options)
                            opt_text = opt_val[0] if isinstance(opt_val, list) and opt_val else str(tc.options)
                        except Exception:
                            opt_text = str(tc.options)
                            
                        if opt_text in answer_input:
                            user_answer.append(str(tc.id))

            
            elif current_question.type == 'integer':
                try:
                    user_answer = int(request.data.get('answer'))
                except (ValueError, TypeError):
                    return Response({
                        'error': 'Please enter an Integer Value',
                        'question_id': current_question.id
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            elif current_question.type == 'float':
                try:
                    user_answer = float(request.data.get('answer'))
                except (ValueError, TypeError):
                    return Response({
                        'error': 'Please enter a Float Value',
                        'question_id': current_question.id
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            elif current_question.type == 'string':
                user_answer = str(request.data.get('answer', ''))
            
            elif current_question.type == 'arrange':
                answer_str = request.data.get('answer', '')
                user_indices = []
                if isinstance(answer_str, str):
                    user_indices = [int(ids) for ids in answer_str.split(',') if ids.strip()]
                elif isinstance(answer_str, list):
                    user_indices = [int(ids) for ids in answer_str]
                
                # Map 1-based frontend indices to actual ArrangeTestCase IDs
                if user_indices:
                    # FIX: Use Python's sorted() instead of Django's order_by()
                    actual_test_cases = sorted(current_question.get_test_cases(), key=lambda x: x.id)
                    
                    user_answer = []
                    for idx in user_indices:
                        list_idx = idx - 1  # Convert 1-based to 0-based
                        if 0 <= list_idx < len(actual_test_cases):
                            user_answer.append(actual_test_cases[list_idx].id)
                else:
                    user_answer = []
            
            elif current_question.type == 'upload':
                # Handle file upload
                uploaded_files = request.FILES.getlist('assignment')
                if not uploaded_files:
                    return Response({
                        'error': 'Please upload assignment file',
                        'question_id': current_question.id
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Delete existing uploads for this question
                AssignmentUpload.objects.filter(
                    assignmentQuestion_id=current_question.id,
                    answer_paper_id=paper.id
                ).delete()
                
                # Create new uploads
                uploads_to_create = []
                for fname in uploaded_files:
                    fname._name = fname._name.replace(" ", "_")
                    uploads_to_create.append(AssignmentUpload(
                        assignmentQuestion_id=current_question.id,
                        assignmentFile=fname,
                        answer_paper_id=paper.id
                    ))
                AssignmentUpload.objects.bulk_create(uploads_to_create)
                
                user_answer = 'ASSIGNMENT UPLOADED'
                new_answer = Answer(
                    question=current_question,
                    answer=user_answer,
                    correct=False,
                    error=json.dumps([])
                )
                new_answer.save()
                paper.answers.add(new_answer)
                next_q = paper.add_completed_question(current_question.id)
                
                # Return success with next question
                from api.serializers import QuestionSerializer
                next_question_data = QuestionSerializer(next_q).data if next_q else None
                
                return Response({
                    'success': True,
                    'message': 'Assignment uploaded successfully',
                    'next_question': next_question_data,
                    'paper': {
                        'questions_answered': paper.questions_answered.count(),
                        'questions_unanswered': paper.questions_unanswered.count(),
                    }
                }, status=status.HTTP_200_OK)
            
            else:
                # Default: code or other types
                user_answer = request.data.get('answer')
        
        except Exception as e:
            return Response({
                'error': f'Error parsing answer: {str(e)}',
                'question_id': current_question.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate answer
        if not is_valid_answer(user_answer):
            return Response({
                'error': 'Please submit a valid answer.',
                'question_id': current_question.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update answer
        if (current_question in paper.get_questions_answered() and 
            current_question.type not in ['code', 'upload']):
            new_answer = paper.get_latest_answer(current_question.id)
            new_answer.answer = user_answer
            new_answer.correct = False
        else:
            new_answer = Answer(
                question=current_question,
                answer=user_answer,
                correct=False,
                error=json.dumps([])
            )
        
        new_answer.save()
        uid = new_answer.id
        paper.answers.add(new_answer)
        
        # Validate the answer
        json_data = current_question.consolidate_answer_data(
            user_answer, user
        ) if current_question.type == 'code' else None
        
        result = paper.validate_answer(
            user_answer, current_question, json_data, uid
        )
        
        # Handle code question asynchronously
        if current_question.type == 'code':
            if paper.time_left() <= 0 and not paper.question_paper.quiz.is_exercise:
                # Time is up for code question - get result synchronously
                url = f'{SERVER_HOST_NAME}:{SERVER_POOL_PORT}'
                result_details = get_result_from_code_server(url, uid, block=True)
                result = json.loads(result_details.get('result'))
                
                # Update paper with result
                from yaksh.views import _update_paper
                next_question, error_message, paper = _update_paper(
                    request, uid, result
                )
                
                from api.serializers import QuestionSerializer
                next_question_data = QuestionSerializer(next_question).data if next_question else None
                
                return Response({
                    'success': result.get('success', False),
                    'result': result,
                    'error_message': error_message,
                    'next_question': next_question_data,
                    'paper': {
                        'marks_obtained': paper.marks_obtained,
                        'questions_answered': paper.questions_answered.count(),
                        'questions_unanswered': paper.questions_unanswered.count(),
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Return result status for async processing
                return Response({
                    'status': 'processing',
                    'answer_id': uid,
                    'result': result,
                    'message': 'Code is being evaluated'
                }, status=status.HTTP_200_OK)
        
        else:
            # Non-code question - process immediately
            from yaksh.views import _update_paper
            next_question, error_message, paper = _update_paper(
                request, uid, result
            )
            
            from api.serializers import QuestionSerializer
            next_question_data = QuestionSerializer(next_question).data if next_question else None
            
            return Response({
                'success': result.get('success', False),
                'result': result,
                'error_message': error_message,
                'next_question': next_question_data,
                'paper': {
                    'marks_obtained': paper.marks_obtained,
                    'questions_answered': paper.questions_answered.count(),
                    'questions_unanswered': paper.questions_unanswered.count(),
                    'time_left': paper.time_left(),
                },
                'answer_id': uid
            }, status=status.HTTP_200_OK)
    
    return Response({
        'error': 'Method not allowed'
    }, status=status.HTTP_405_METHOD_NOT_ALLOWED)                      

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_skip_question(request, q_id, attempt_num, module_id, questionpaper_id, 
                      course_id, next_q=None):
    """
    API endpoint to skip a question
    GET: Returns the next question to skip to
    POST: Saves code answer with skipped flag (for code questions only) then returns next question
    """
    user = request.user
    
    # Get the answer paper
    try:
        paper = AnswerPaper.objects.get(
            user=user,
            attempt_number=attempt_num,
            question_paper_id=questionpaper_id,
            course_id=course_id
        )
    except AnswerPaper.DoesNotExist:
        return Response({
            'error': 'Answer paper not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get current question
    try:
        question = Question.objects.get(pk=q_id)
    except Question.DoesNotExist:
        return Response({
            'error': 'Question not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Update start time if it's an exercise
    if paper.question_paper.quiz.is_exercise:
        paper.start_time = timezone.now()
        paper.save()
    
    # Handle POST request for code questions
    if request.method == 'POST' and question.type == 'code':
        # Only save if no correct answer exists
        if not paper.answers.filter(question=question, correct=True).exists():
            user_code = request.data.get('answer', '')
            new_answer = Answer(
                question=question,
                answer=user_code,
                correct=False,
                skipped=True,
                error=json.dumps([])
            )
            new_answer.save()
            paper.answers.add(new_answer)
    
    # Determine next question
    if next_q is not None:
        try:
            next_question = Question.objects.get(pk=next_q)
        except Question.DoesNotExist:
            return Response({
                'error': 'Next question not found'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        next_question = paper.next_question(q_id)
    
    # Serialize next question
    from api.serializers import QuestionSerializer
    
    if next_question:
        question_data = QuestionSerializer(next_question).data
        
        # Get previous answers for the next question if any
        previous_answers = paper.get_previous_answers(next_question)
        last_attempt = previous_answers[0].answer if previous_answers else None
        
        return Response({
            'success': True,
            'question': question_data,
            'paper': {
                'id': paper.id,
                'status': paper.status,
                'time_left': paper.time_left(),
                'questions_answered': paper.questions_answered.count(),
                'questions_unanswered': paper.questions_unanswered.count(),
            },
            'last_attempt': last_attempt,
            'course_id': int(course_id),
            'module_id': int(module_id),
        }, status=status.HTTP_200_OK)
    else:
        # No more questions - quiz is complete
        return Response({
            'success': True,
            'completed': True,
            'message': 'No more questions available',
            'course_id': int(course_id),
            'module_id': int(module_id),
            'attempt_num': attempt_num,
            'questionpaper_id': int(questionpaper_id),
        }, status=status.HTTP_200_OK)


# ============================================================
#  GRADING APIs
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_grading_courses(request):
    """
    Get list of courses for grading (Level 1) - Only includes quizzes, no lessons
    Equivalent to: /manage/gradeuser/
    """
    user = request.user
    
    if not is_moderator(user):
        return Response(
            {'error': 'You are not allowed to access this page'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    courses = Course.objects.filter(
        Q(creator=user) | Q(teachers=user), 
        is_trial=False
    ).order_by("-active").distinct()
    
    # Pagination
    page = request.query_params.get('page', 1)
    paginator = Paginator(courses, 30)
    
    try:
        courses_page = paginator.page(page)
    except:
        courses_page = paginator.page(1)
    
    # Use specialized grading serializer (quizzes only)
    serializer = GradingCourseSerializer(courses_page, many=True)
    
    return Response({
        'courses': serializer.data,
        'total_pages': paginator.num_pages,
        'current_page': courses_page.number,
        'has_next': courses_page.has_next(),
        'has_previous': courses_page.has_previous()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_quiz_users(request, quiz_id, course_id):
    """
    Get list of users who attempted a quiz (Level 2)
    Equivalent to: /manage/gradeuser/<quiz_id>/<course_id>/
    """
    user = request.user
    
    if not is_moderator(user):
        return Response(
            {'error': 'You are not allowed to access this page'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        course = Course.objects.get(id=course_id)
        
        if not course.is_creator(user) and not course.is_teacher(user):
            return Response(
                {'error': 'This course does not belong to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        questionpaper_id = QuestionPaper.objects.filter(
            quiz_id=quiz_id
        ).values("id")
        
        user_details = AnswerPaper.objects.get_users_for_questionpaper(
            questionpaper_id, course_id
        )
        
        has_quiz_assignments = AssignmentUpload.objects.filter(
            answer_paper__course_id=course_id,
            answer_paper__question_paper_id__in=questionpaper_id
        ).exists()
        
        # Serialize user details
        users_data = []
        for user_detail in user_details:
            # user_detail is a dict with keys: user__id, user__first_name, user__last_name
            user_id = user_detail['user__id']
            user_obj = User.objects.select_related('profile').get(id=user_id)
            users_data.append({
                'id': user_obj.id,
                'username': user_obj.username,
                'email': user_obj.email,
                'first_name': user_obj.first_name,
                'last_name': user_obj.last_name,
                'roll_number': user_obj.profile.roll_number if hasattr(user_obj, 'profile') else None
            })
        
        return Response({
            'quiz': {
                'id': quiz.id,
                'description': quiz.description,
                'duration': quiz.duration
            },
            'course': {
                'id': course.id,
                'name': course.name
            },
            'users': users_data,
            'has_quiz_assignments': has_quiz_assignments
        })
        
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_user_attempts(request, quiz_id, user_id, course_id):
    """
    Get all attempts of a user for a quiz (Level 3)
    Equivalent to: /manage/gradeuser/<quiz_id>/<user_id>/<course_id>/
    """
    current_user = request.user
    
    if not is_moderator(current_user):
        return Response(
            {'error': 'You are not allowed to access this page'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        course = Course.objects.get(id=course_id)
        student = User.objects.get(id=user_id)
        
        if not course.is_creator(current_user) and not course.is_teacher(current_user):
            return Response(
                {'error': 'This course does not belong to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        questionpaper_id = QuestionPaper.objects.filter(
            quiz_id=quiz_id
        ).values("id")
        
        attempts = AnswerPaper.objects.get_user_all_attempts(
            questionpaper_id, user_id, course_id
        )
        
        if not attempts:
            return Response({'error': 'No attempts found for this user'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        has_user_assignments = AssignmentUpload.objects.filter(
            answer_paper__course_id=course_id,
            answer_paper__question_paper_id__in=questionpaper_id,
            answer_paper__user_id=user_id
        ).exists()
        
        # Get all users for quiz (for navigation)
        user_details = AnswerPaper.objects.get_users_for_questionpaper(
            questionpaper_id, course_id
        )
        
        users_data = []
        for user_detail in user_details:
            # user_detail is a dict with keys: user__id, user__first_name, user__last_name
            users_data.append({
                'id': user_detail['user__id'],
                'username': '',  # Not available in get_users_for_questionpaper
                'first_name': user_detail['user__first_name'],
                'last_name': user_detail['user__last_name'],
            })
        
        serializer = UserAttemptSerializer(attempts, many=True)
        
        return Response({
            'quiz': {
                'id': quiz.id,
                'description': quiz.description
            },
            'course': {
                'id': course.id,
                'name': course.name
            },
            'student': {
                'id': student.id,
                'username': student.username,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'email': student.email
            },
            'attempts': serializer.data,
            'has_user_assignments': has_user_assignments,
            'users': users_data
        })
        
    except (Quiz.DoesNotExist, Course.DoesNotExist, User.DoesNotExist):
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_grade_user_attempt(request, quiz_id, user_id, attempt_number, course_id):
    """
    Get or update grades for a specific attempt (Level 4)
    GET: Equivalent to: /manage/gradeuser/<quiz_id>/<user_id>/<attempt_number>/<course_id>/
    POST: Submit grades for the attempt
    """
    current_user = request.user
    
    if not is_moderator(current_user):
        return Response(
            {'error': 'You are not allowed to access this page'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        course = Course.objects.get(id=course_id)
        student = User.objects.get(id=user_id)
        
        if not course.is_creator(current_user) and not course.is_teacher(current_user):
            return Response(
                {'error': 'This course does not belong to you'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use values_list with flat=True to get list of IDs
        questionpaper_id = QuestionPaper.objects.filter(
            quiz_id=quiz_id
        ).values_list("id", flat=True)
        
        # Check if question paper exists
        if not questionpaper_id:
            return Response(
                {'error': 'No question paper found for this quiz'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'GET':
            # Get the specific attempt data
            data = AnswerPaper.objects.get_user_data(
                student, questionpaper_id, course_id, attempt_number
            )
            
            # Check if user has any attempts
            if not data or not data.get('papers'):
                return Response(
                    {'error': 'No attempt found for this user'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            attempts = AnswerPaper.objects.get_user_all_attempts(
                questionpaper_id, user_id, course_id
            )
            
            has_user_assignments = AssignmentUpload.objects.filter(
                answer_paper__course_id=course_id,
                answer_paper__question_paper_id__in=questionpaper_id,
                answer_paper__user_id=user_id
            ).exists()
            
            has_quiz_assignments = AssignmentUpload.objects.filter(
                answer_paper__course_id=course_id,
                answer_paper__question_paper_id__in=questionpaper_id
            ).exists()
            
            # Get all users for navigation
            user_details = AnswerPaper.objects.get_users_for_questionpaper(
                questionpaper_id, course_id
            )
            
            users_data = []
            for user_detail in user_details:
                # user_detail is a dict with keys: user__id, user__first_name, user__last_name
                users_data.append({
                    'id': user_detail['user__id'],
                    'username': '',  # Not available in get_users_for_questionpaper
                    'first_name': user_detail['user__first_name'],
                    'last_name': user_detail['user__last_name'],
                })
            
            # Format the data for frontend
            papers_data = []
            for paper in data['papers']:
                questions_data = []
                total_marks = 0.0
                for question, answers in paper.get_question_answers().items():
                    question_data = QuestionSerializer(question).data
                    total_marks += float(question_data.get('points', 0) or 0)
                    answer_data = None
                    if answers and answers[0] is not None:
                        if isinstance(answers[0], dict) and answers[0].get('answer'):
                            ans_obj = answers[0]['answer']
                            answer_data = {
                                'id': ans_obj.id,
                                'answer_content': ans_obj.answer,
                                'marks': ans_obj.marks,
                                'correct': ans_obj.correct,
                                'error': ans_obj.error,
                                'skipped': getattr(ans_obj, 'skipped', False)
                            }
                    if answer_data is None:
                        answer_data = {
                            'id': None,
                            'answer_content': None,
                            'marks': 0.0,
                            'correct': False,
                            'error': None,
                            'skipped': True
                        }
                    questions_data.append({
                        'question': question_data,
                        'answer': answer_data
                    })
                papers_data.append({
                    'id': paper.id,
                    'marks_obtained': paper.marks_obtained,
                    'total_marks': total_marks,
                    'percent': paper.percent,
                    'status': paper.status,
                    'comments': paper.comments,
                    'questions': questions_data
                })
            
            return Response({
                'quiz': {
                    'id': quiz.id,
                    'description': quiz.description,
                    'duration': quiz.duration
                },
                'course': {
                    'id': course.id,
                    'name': course.name
                },
                'student': {
                    'id': student.id,
                    'username': student.username,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'email': student.email
                },
                'papers': papers_data,
                'attempts': UserAttemptSerializer(attempts, many=True).data,
                'has_user_assignments': has_user_assignments,
                'has_quiz_assignments': has_quiz_assignments,
                'users': users_data
            })
        
        elif request.method == 'POST':
            # Update grades
            data = AnswerPaper.objects.get_user_data(
                student, questionpaper_id, course_id, attempt_number
            )
            
            # Check if user has any attempts
            if not data or not data.get('papers'):
                return Response(
                    {'error': 'No attempt found for this user'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            papers = data['papers']
            grades_data = request.data.get('grades', [])
            paper_comments = request.data.get('comments', '')
            
            for paper in papers:
                for question, answers in paper.get_question_answers().items():
                    # Find the marks for this question
                    for grade in grades_data:
                        if grade.get('question_id') == question.id:
                            marks = float(grade.get('marks', 0))
                            if answers and answers[0] and isinstance(answers[0], dict) and answers[0].get('answer'):
                                answer = answers[0]['answer']
                                answer.set_marks(marks)
                                answer.save()
                            break
                
                paper.update_marks()
                paper.comments = paper_comments or 'No comments'
                paper.save()
            
            # Update course status
            course_status = CourseStatus.objects.filter(
                course_id=course.id, user_id=student.id
            )
            if course_status.exists():
                course_status.first().set_grade()
            
            return Response({
                'message': 'Student data saved successfully',
                'success': True
            })
            
            
    except (Quiz.DoesNotExist, Course.DoesNotExist, User.DoesNotExist):
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)
    except IndexError:
        return Response({'error': 'No attempts for this paper'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ============================================================
#  REGRADING APIs
# ============================================================

# Imports for regrade functionality
from yaksh.tasks import regrade_papers
try:
    from online_test.celery_settings import app
except (ImportError, ModuleNotFoundError):
    app = None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_regrade(request, course_id, questionpaper_id, question_id=None, answerpaper_id=None):
    """
    API Endpoint to trigger regrading via Celery task.
    Handles regrading by:
    1. Quiz (QuestionPaper)
    2. User (AnswerPaper)
    3. Specific Question (Question + AnswerPaper)
    """
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    
    # Permission Check: User must be a Moderator OR (Creator AND Teacher) of the course
    has_permission = is_moderator(user) or (course.is_creator(user) and course.is_teacher(user))
    
    if not has_permission:
        return Response(
            {'error': 'You are not allowed to perform this action.'},
            status=status.HTTP_403_FORBIDDEN
        )
        
    questionpaper = get_object_or_404(QuestionPaper, pk=questionpaper_id)
    quiz = questionpaper.quiz
    
    data = {
        "user_id": user.id,
        "course_id": course_id,
        "questionpaper_id": questionpaper_id,
        "question_id": question_id,
        "answerpaper_id": answerpaper_id,
        "quiz_id": quiz.id,
        "quiz_name": quiz.description,
        "course_name": course.name
    }
    
    # Check if Celery is alive
    is_celery_alive = False
    if app:
        try:
            # app.control.ping() returns a list of worker responses if alive
            if app.control.ping():
                is_celery_alive = True
        except Exception:
            pass

    if is_celery_alive:
        regrade_papers.delay(data)
        msg = f"{quiz.description} is submitted for re-evaluation. You will receive a notification for the re-evaluation status."
        return Response({'message': msg}, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': "Unable to submit for regrade. Celery worker not reachable. Please contact admin."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# ============================================================
# MONITOR QUIZ APIs
# ============================================================


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monitor_papers(request, quiz_id=None, course_id=None, attempt_number=1):
    """
    API to monitor progress of papers.
    If IDs are provided, returns stats for that specific quiz/course.
    If IDs are missing, returns a list of monitorable quizzes for the user.
    """
    user = request.user
    if not is_moderator(user):
        return Response({'error': 'You are not allowed to view this page!'}, status=status.HTTP_403_FORBIDDEN)

    # === LIST VIEW: No valid IDs provided ===
    if quiz_id is None or course_id is None:
        courses = Course.objects.filter(Q(creator=user) | Q(teachers=user)).distinct()
        data = []
        for course in courses:
            module_ids = course.learning_module.values_list('id', flat=True)
            unit_ids = LearningUnit.objects.filter(
                learning_unit__id__in=module_ids, 
                type='quiz'
            ).values_list('id', flat=True)
            quizzes = Quiz.objects.filter(
                learningunit__id__in=unit_ids
            ).distinct().values('id', 'description')
            if quizzes:
                data.append({
                    'course': {
                        'id': course.id, 
                        'name': course.name, 
                        'code': course.code
                    },
                    'quizzes': list(quizzes)
                })
        return Response(data, status=status.HTTP_200_OK)

    # === DETAIL VIEW: IDs provided ===
    course = get_object_or_404(Course, id=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)

    quiz = get_object_or_404(Quiz, id=quiz_id)
    q_paper = QuestionPaper.objects.filter(
        quiz__is_trial=False, 
        quiz_id=quiz_id
    ).distinct().last()
    if not q_paper:
        return Response({
            'error': 'No valid Question Paper found for this quiz.'
        }, status=status.HTTP_404_NOT_FOUND)

    # FIX: Always get all attempt numbers for this course and question paper
    attempt_numbers = list(
        AnswerPaper.objects.filter(
            question_paper_id=q_paper.id,
            course_id=course.id
        ).values_list('attempt_number', flat=True).distinct()
    )

    questions_count = 0
    questions_attempted = {}
    completed_papers = 0
    inprogress_papers = 0

    try:
        attempt_number = int(attempt_number)
    except (ValueError, TypeError):
        attempt_number = 1

    papers = AnswerPaper.objects.filter(
        question_paper_id=q_paper.id, 
        course_id=course_id,
        attempt_number=attempt_number
    ).order_by('user__first_name')

    if papers.exists():
        questions_count = q_paper.get_questions_count()
        questions_attempted = AnswerPaper.objects.get_questions_attempted(
            papers.values_list("id", flat=True)
        ) or {}
        completed_papers = papers.filter(status="completed").count()
        inprogress_papers = papers.filter(status="inprogress").count()

    serializer_context = {
        'request': request,
        'questions_attempted': questions_attempted
    }
    serializer = MonitorAnswerPaperSerializer(papers, many=True, context=serializer_context)

    return Response({
        'quiz': {
            'id': quiz.id,
            'description': quiz.description,
            'duration': quiz.duration,
            'total_marks': q_paper.total_marks
        },
        'course': {
            'id': course.id,
            'name': course.name, 
            'code': course.code
        },
        'stats': {
            'total_papers': papers.count(),
            'completed_papers': completed_papers,
            'inprogress_papers': inprogress_papers,
            'questions_count': questions_count
        },
        'attempt_numbers': attempt_numbers,
        'current_attempt': attempt_number,
        'papers': serializer.data
    })

# ============================================================
#  OTHER QUIZ MENU APIs
# ============================================================


import pandas as pd
from django.http import HttpResponse



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def show_statistics(request, questionpaper_id, course_id, attempt_number=None):
    """
    API to show statistics for a specific question paper attempt.
    """
    user = request.user
    if not is_moderator(user):
        return Response({'error': 'You are not allowed to view this page'}, status=status.HTTP_403_FORBIDDEN)

    course = get_object_or_404(Course, id=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)

    try:
        q_paper = get_object_or_404(QuestionPaper, pk=questionpaper_id)
    except QuestionPaper.DoesNotExist:
         return Response({'error': 'Question Paper not found'}, status=status.HTTP_404_NOT_FOUND)

    quiz = q_paper.quiz
    attempt_numbers = AnswerPaper.objects.get_attempt_numbers(questionpaper_id, course_id)
    
    response_data = {
        'quiz': {
            'id': quiz.id,
            'description': quiz.description
        },
        'course_id': course_id,
        'questionpaper_id': questionpaper_id,
        'attempts': list(attempt_numbers)
    }

    if attempt_number is None:
        return Response(response_data)
        
    try:
        attempt_number = int(attempt_number)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid attempt number'}, status=status.HTTP_400_BAD_REQUEST)

    if not AnswerPaper.objects.has_attempt(questionpaper_id, attempt_number, course_id):
         response_data['message'] = "No answerpapers found for this attempt"
         return Response(response_data)

    total_attempt = AnswerPaper.objects.get_count(questionpaper_id, attempt_number, course_id)
    
    # helper method returns dictionary: {QuestionObject: (total, correct, percent, per_tc_ans)}
    raw_stats = AnswerPaper.objects.get_question_statistics(
        questionpaper_id, attempt_number, course_id
    )
    
    # Serialize the statistics
    stats_list = []
    for question, data in raw_stats.items():
        stats_list.append({
            'question': {
                'id': question.id,
                'summary': question.summary,
                'type': question.type,
                'points': question.points
            },
            'total_attempts': data[0],
            'correct_attempts': data[1],
            'correct_percentage': data[2],
            'per_testcase_stats': data[3]
        })

    response_data.update({
        'total_attempts_count': total_attempt,
        'current_attempt': attempt_number,
        'statistics': stats_list
    })
    
    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download_quiz_csv(request, course_id, quiz_id):
    """
    API to download CSV report for a quiz attempt.
    Expects 'attempt_number' in POST body.
    """
    user = request.user
    if not is_moderator(user):
        return Response({'error': 'You are not allowed to view this page!'}, status=status.HTTP_403_FORBIDDEN)
        
    course = get_object_or_404(Course, id=course_id)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'The quiz does not belong to your course'}, status=status.HTTP_403_FORBIDDEN)
        
    quiz = get_object_or_404(Quiz, id=quiz_id)
    question_paper = quiz.questionpaper_set.last()
    
    if not question_paper:
         return Response({'error': 'No question paper found for this quiz'}, status=status.HTTP_404_NOT_FOUND)

    attempt_number = request.data.get('attempt_number')
    if not attempt_number:
        return Response({'error': 'Attempt number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    questions = question_paper.get_question_bank()
    
    answerpapers = AnswerPaper.objects.select_related(
        "user", "question_paper"
    ).prefetch_related('answers').filter(
        course_id=course_id, 
        question_paper_id=question_paper.id,
        attempt_number=attempt_number
    ).order_by("user__first_name")
    
    if not answerpapers.exists():
        return Response(
            {'error': f'No papers found for attempt {attempt_number}'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    que_summaries = [
        (f"Q-{que.id}-{que.summary}-{que.points}-marks", que.id,
            f"Q-{que.id}-{que.summary}-comments"
            )
        for que in questions
    ]
    
    # Base user data
    user_data = list(answerpapers.values(
        "user__username", "user__first_name", "user__last_name",
        "user__profile__roll_number", "user__profile__institute",
        "user__profile__department", "marks_obtained",
        "question_paper__total_marks", "percent", "status"
    ))
    
    # Append per-question scores
    for idx, ap in enumerate(answerpapers):
        que_data = ap.get_per_question_score(que_summaries)
        if que_data:
            user_data[idx].update(que_data)
            
    df = pd.DataFrame(user_data)
    
    response = HttpResponse(content_type='text/csv')
    filename = f"{course.name.replace(' ', '_')}-{quiz.description.replace(' ', '_')}-attempt-{attempt_number}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    df.to_csv(response, index=False)
    return response



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_marks(request, course_id, questionpaper_id):
    """
    API to upload marks CSV for a question paper.
    """
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    
    # Permission check
    if not (course.is_teacher(user) or course.is_creator(user)):
        return Response({'error': 'You are not allowed to perform this action!'}, status=status.HTTP_403_FORBIDDEN)
        
    question_paper = get_object_or_404(QuestionPaper, pk=questionpaper_id)
    quiz = question_paper.quiz

    if 'csv_file' not in request.FILES:
        return Response({'error': 'Please upload a CSV file.'}, status=status.HTTP_400_BAD_REQUEST)
        
    csv_file = request.FILES['csv_file']
    is_csv_file, _ = is_csv(csv_file)
    
    if not is_csv_file:
         return Response({'error': 'The file uploaded is not a CSV file.'}, status=status.HTTP_400_BAD_REQUEST)

    # Prepare data for Celery task
    try:
        csv_content = csv_file.read().decode('utf-8').splitlines()
    except UnicodeDecodeError:
        return Response({'error': 'File encoding error. Please upload a UTF-8 encoded CSV.'}, status=status.HTTP_400_BAD_REQUEST)

    data = {
        "course_id": course_id, 
        "questionpaper_id": questionpaper_id,
        "csv_data": csv_content,
        "user_id": user.id
    }
    
    # Check Celery status
    is_celery_alive = False
    if app:
        try:
             if app.control.ping():
                is_celery_alive = True
        except Exception:
            pass

    if is_celery_alive:
        update_user_marks.delay(data)
        msg = f"{quiz.description} is submitted for marks update. You will receive a notification for the update status"
        return Response({'message': msg}, status=status.HTTP_200_OK)
    else:
        return Response({'error': "Unable to submit for marks update. Please check with admin"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_data(request, user_id, questionpaper_id=None, course_id=None):
    """
    API to fetch detailed user data for a specific question paper attempt.
    """
    current_user = request.user
    if not is_moderator(current_user):
        return Response({'error': 'You are not allowed to view this page!'}, status=status.HTTP_403_FORBIDDEN)

    target_user = get_object_or_404(User, id=user_id)
    
    # If course_id provided, verify instructor permissions
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
        if not (course.is_creator(current_user) or course.is_teacher(current_user)):
             return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)

    # get_user_data returns a dictionary with 'user', 'profile', 'papers' (queryset), etc.
    data = AnswerPaper.objects.get_user_data(target_user, questionpaper_id, course_id)
    
    # Data serialization
    papers_data = []
    if 'papers' in data:
        papers = data['papers']
        # We can use MonitorAnswerPaperSerializer or a simpler one
        for paper in papers:
            papers_data.append({
                'id': paper.id,
                'attempt_number': paper.attempt_number,
                'start_time': paper.start_time,
                'end_time': paper.end_time,
                'status': paper.status,
                'marks_obtained': paper.marks_obtained,
                'passed': paper.passed,
                'percent': paper.percent,
                'user_ip': paper.user_ip
            })

    response_data = {
        'user': {
            'id': target_user.id,
            'username': target_user.username,
            'first_name': target_user.first_name,
            'last_name': target_user.last_name,
            'email': target_user.email,
             # Add profile info if needed
            'roll_number': getattr(target_user.profile, 'roll_number', '') if hasattr(target_user, 'profile') else ''
        },
        'course_id': course_id,
        'questionpaper_id': questionpaper_id,
        'papers': papers_data
    }
    
    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extend_time(request, paper_id):
    """
    API to extend time for an answer paper.
    """
    user = request.user
    if not is_moderator(user):
        return Response({'error': 'You are not allowed to perform this action'}, status=status.HTTP_403_FORBIDDEN)

    anspaper = get_object_or_404(AnswerPaper, pk=paper_id)
    course = anspaper.course
    
    if not (course.is_creator(user) or course.is_teacher(user)):
        return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)

    extra_time = request.data.get('extra_time')
    
    if extra_time is None:
        return Response({'error': 'Please provide extra_time'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        extra_time = float(extra_time)
    except ValueError:
        return Response({'error': 'Invalid time format'}, status=status.HTTP_400_BAD_REQUEST)

    anspaper.set_extra_time(extra_time)
    
    msg = f'Extra {extra_time} minutes given to {anspaper.user.get_full_name()}'
    return Response({'message': msg}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def allow_special_attempt(request, user_id, course_id, quiz_id):
    """
    API to grant a special attempt to a student.
    """
    user = request.user
    if not is_moderator(user):
        return Response({'error': 'You are not allowed to perform this action'}, status=status.HTTP_403_FORBIDDEN)

    course = get_object_or_404(Course, pk=course_id)
    if not (course.is_creator(user) or course.is_teacher(user)):
        return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)

    quiz = get_object_or_404(Quiz, pk=quiz_id)
    student = get_object_or_404(User, pk=user_id)

    if not course.is_enrolled(student):
         return Response({'error': 'The student is not enrolled for this course'}, status=status.HTTP_400_BAD_REQUEST)

    micromanager, created = MicroManager.objects.get_or_create(
        course=course, student=student, quiz=quiz
    )
    micromanager.manager = user
    micromanager.save()

    msg = ""
    status_code = status.HTTP_200_OK

    if (not micromanager.is_special_attempt_required() or
            micromanager.is_last_attempt_inprogress()):
        name = student.get_full_name()
        msg = f'{name} can attempt normally. No special attempt required!'
        status_code = status.HTTP_200_OK # Info, not error
    elif micromanager.can_student_attempt():
        msg = f'{student.get_full_name()} already has a special attempt!'
        status_code = status.HTTP_200_OK # Info
    else:
        micromanager.allow_special_attempt()
        msg = f'A special attempt is provided to {student.get_full_name()}!'

    return Response({
        'message': msg,
        'micromanager_id': micromanager.id
    }, status=status_code)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def special_start(request, micromanager_id=None):
    """
    API for a student to start a special attempt.
    """
    user = request.user
    micromanager = get_object_or_404(MicroManager, pk=micromanager_id, student=user)
    course = micromanager.course
    quiz = micromanager.quiz
    module = course.get_learning_module(quiz)
    
    # Normally question_paper is linked to quiz
    # Logic from legacy: get_object_or_404(QuestionPaper, quiz=quiz)
    # This might fail if multiple QPs exist? Usually OneToOne or FK. 
    # Legacy uses .get() via shortcut so implies single QP or validation elsewhere.
    # Assuming standard flow where one non-trial QP is active or just 'quiz.questionpaper_set.first()'
    # Legacy code: get_object_or_404(QuestionPaper, quiz=quiz) implies uniqueness.
    
    try:
        quest_paper = QuestionPaper.objects.filter(quiz=quiz, quiz__is_trial=False).last()
        if not quest_paper:
             # Fallback
             quest_paper = get_object_or_404(QuestionPaper, quiz=quiz)
    except MultipleObjectsReturned:
        quest_paper = QuestionPaper.objects.filter(quiz=quiz).last()

    if not course.is_enrolled(user):
        return Response({'error': f'You are not enrolled in {course.name} course'}, status=status.HTTP_403_FORBIDDEN)

    if not micromanager.can_student_attempt():
         return Response({'error': f'Your special attempts are exhausted for {quiz.description}'}, status=status.HTTP_403_FORBIDDEN)

    last_attempt = AnswerPaper.objects.get_user_last_attempt(
        quest_paper, user, course.id)

    # If last attempt is in progress, resume it (this logic exists in legacy)
    # But this route is 'special_start', implying creation of new attempt usually?
    # Legacy logic: if inprogress, return show_question (resume).
    
    if last_attempt and last_attempt.is_attempt_inprogress():
        # Resume logic: In API, we just return the attempt details so frontend can navigate.
        return Response({
            'message': 'Resuming existing attempt',
            'attempt_id': last_attempt.id,
            'status': 'resumed',
            'course_id': course.id,
            'module_id': module.id if module else None,
            'quiz_id': quiz.id
        })

    # Start new special attempt
    attempt_num = micromanager.get_attempt_number()
    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    new_paper = quest_paper.make_answerpaper(user, ip, attempt_num, course.id, special=True)
    micromanager.increment_attempts_utilised()
    
    return Response({
        'message': 'Special attempt started',
        'attempt_id': new_paper.id,
        'status': 'started',
        'course_id': course.id,
        'module_id': module.id if module else None,
        'quiz_id': quiz.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_special_attempt(request, micromanager_id):
    """
    API to revoke a special attempt.
    """
    user = request.user
    if not is_moderator(user):
        return Response({'error': 'You are not allowed to perform this action'}, status=status.HTTP_403_FORBIDDEN)

    micromanager = get_object_or_404(MicroManager, pk=micromanager_id)
    course = micromanager.course
    
    if not (course.is_creator(user) or course.is_teacher(user)):
        return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)

    micromanager.revoke_special_attempt()
    msg = f'Revoked special attempt for {micromanager.student.get_full_name()}'
    
    return Response({'message': msg}, status=status.HTTP_200_OK)



# ============================================================
#  DESIGN COURSE TAB APIs
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_design_course(request, course_id):
    user = request.user
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

    if not is_moderator(user):
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
    if not course.is_creator(user) and not course.is_teacher(user):
        return Response({'error': 'This course does not belong to you'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "POST":
        action = request.data.get("action")
        if action == "add":
            add_values = request.data.get("module_list", [])
            to_add_list = []
            if add_values:
                ordered_modules = course.get_learning_modules()
                start_val = ordered_modules.last().order + 1 if ordered_modules.exists() else 1
                for order, value in enumerate(add_values, start_val):
                    module, created = LearningModule.objects.get_or_create(id=int(value))
                    module.order = order
                    module.save()
                    to_add_list.append(module)
                course.learning_module.add(*to_add_list)
                return Response({'message': "Modules added successfully"})
            else:
                return Response({'error': "Please select at least one module"}, status=400)

        elif action == "change":
            order_list = request.data.get("ordered_list", "")
            if order_list:
                order_list = order_list.split(",")
                for order in order_list:
                    learning_unit, learning_order = order.split(":")
                    if learning_order:
                        learning_module = course.learning_module.get(id=learning_unit)
                        learning_module.order = learning_order
                        learning_module.save()
                return Response({'message': "Changed order successfully"})
            else:
                return Response({'error': "Please select at least one module"}, status=400)

        elif action == "remove":
            remove_values = request.data.get("delete_list", [])
            if remove_values:
                course.learning_module.remove(*remove_values)
                return Response({'message': "Modules removed successfully"})
            else:
                return Response({'error': "Please select at least one module"}, status=400)

        elif action == "change_prerequisite_completion":
            unit_list = request.data.get("check_prereq", [])
            if unit_list:
                for unit in unit_list:
                    learning_module = course.learning_module.get(id=unit)
                    learning_module.toggle_check_prerequisite()
                    learning_module.save()
                return Response({'message': "Changed prerequisite check successfully"})
            else:
                return Response({'error': "Please select at least one module"}, status=400)

        elif action == "change_prerequisite_passing":
            unit_list = request.data.get("check_prereq_passes", [])
            if unit_list:
                for unit in unit_list:
                    learning_module = course.learning_module.get(id=unit)
                    learning_module.toggle_check_prerequisite_passes()
                    learning_module.save()
                return Response({'message': "Changed prerequisite check successfully"})
            else:
                return Response({'error': "Please select at least one module"}, status=400)

        return Response({'error': "Invalid action"}, status=400)

    # GET: Return current course design info
    added_learning_modules = course.get_learning_modules()
    all_learning_modules = LearningModule.objects.filter(creator=user, is_trial=False)
    learning_modules = set(all_learning_modules) - set(added_learning_modules)
    # You can serialize these as needed, e.g.:
    from api.serializers import LearningModuleSerializer
    return Response({
        'added_learning_modules': LearningModuleSerializer(added_learning_modules, many=True).data,
        'learning_modules': LearningModuleSerializer(list(learning_modules), many=True).data,
        'course': course.id,
        'is_design_course': True
    })


# ============================================================
#  COURSE MD UPLOAD/DOWNLOAD APIs
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_download_course_md(request, course_id):
    """Download course structure as Markdown ZIP file"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized to access this page'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify teacher owns the course
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to download this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Import here to avoid circular imports
        from upload.utils import write_course_to_file
        
        curr_dir = os.getcwd()
        zip_file_buffer = BytesIO()
        
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                os.chdir(tmpdirname)
                write_course_to_file(course_id)
                
                # Create ZIP file
                with ZipFile(zip_file_buffer, 'w') as zip_file:
                    for foldername, subfolders, filenames in os.walk(tmpdirname):
                        for filename in filenames:
                            file_path = os.path.join(foldername, filename)
                            arcname = os.path.relpath(file_path, tmpdirname)
                            zip_file.write(file_path, arcname)
                
                zip_file_buffer.seek(0)
                
                # Create HTTP response with ZIP file
                response = HttpResponse(
                    zip_file_buffer.read(),
                    content_type='application/zip'
                )
                response['Content-Disposition'] = f'attachment; filename="course_{course_id}.zip"'
                return response
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Error while generating course file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            os.chdir(curr_dir)
            
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_upload_course_md(request, course_id):
    """Upload course structure from Markdown ZIP file"""
    user = request.user
    
    if not _check_teacher_permission(user):
        return Response(
            {'error': 'You are not authorized to access this page'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Verify teacher owns the course
        if course.creator != user and user not in course.teachers.all():
            return Response(
                {'error': 'You do not have permission to upload to this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if file is provided
        course_upload_file = request.FILES.get('course_upload_md')
        if not course_upload_file:
            return Response(
                {'error': 'No file provided. Please upload a ZIP file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file extension
        file_extension = os.path.splitext(course_upload_file.name)[1][1:].lower()
        if file_extension != 'zip':
            return Response(
                {'error': 'Please upload a ZIP file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import here to avoid circular imports
        from upload.utils import upload_course
        
        curr_dir = os.getcwd()
        upload_status = False
        msg = None
        
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Extract ZIP file
                with ZipFile(course_upload_file, 'r') as zip_file:
                    zip_file.extractall(tmpdirname)
                
                # Find toc.yml file (it might be in a subdirectory)
                toc_path = None
                for root, dirs, files in os.walk(tmpdirname):
                    if 'toc.yml' in files:
                        toc_path = root
                        break
                
                if not toc_path:
                    return Response(
                        {'error': 'toc.yml file not found in the ZIP archive. Please ensure your ZIP file contains a toc.yml file.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Change to directory containing toc.yml and process
                os.chdir(toc_path)
                upload_status, msg = upload_course(user)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            # Provide more helpful error messages
            if 'duplicate' in error_msg.lower() or 'duplicate' in (msg or '').lower():
                return Response(
                    {
                        'error': msg or error_msg,
                        'details': 'The uploaded file contains duplicate module IDs. Please check your toc.yml and module files to ensure each module has a unique ID, or remove the ID field from modules you want to create as new.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': f'Error parsing file structure: {error_msg}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        finally:
            os.chdir(curr_dir)
        
        if upload_status:
            return Response(
                {'success': True, 'message': 'MD File successfully uploaded to course'},
                status=status.HTTP_200_OK
            )
        else:
            # Provide more context for validation errors
            error_details = {}
            if msg:
                if 'duplicate' in msg.lower():
                    error_details = {
                        'error': msg,
                        'details': 'Your uploaded file contains duplicate IDs. To fix this:\n'
                                   '1. If you want to update existing modules: Ensure each module has a unique ID that matches an existing module in the course.\n'
                                   '2. If you want to create new modules: Remove the "id" field from the module metadata in the Markdown files.\n'
                                   '3. Check your toc.yml file to ensure no module appears twice.'
                    }
                elif 'not belong' in msg.lower() or 'relationship' in msg.lower():
                    error_details = {
                        'error': msg,
                        'details': 'The IDs in your uploaded file do not match the course structure. Please ensure:\n'
                                   '1. Module IDs belong to the current course.\n'
                                   '2. Lesson/Quiz IDs belong to their respective modules.\n'
                                   '3. Or remove IDs to create new items instead of updating existing ones.'
                    }
                else:
                    error_details = {'error': msg}
            
            return Response(
                error_details if error_details else {'error': 'Failed to upload course MD file'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_test_quiz(request, mode, quiz_id, course_id):
    """
    Creates a trial quiz/course/module sandbox for moderators.
    Equivalent to the monolith's test_quiz view.
    """
    user = request.user
    
    # Check if the user is a teacher/moderator
    if not _check_teacher_permission(user):
        return Response({'error': 'Permission denied. Only teachers can test quizzes.'}, status=status.HTTP_403_FORBIDDEN)
        
    godmode = (mode == "godmode")
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)

    # If it's a regular user test (usermode) and the quiz is expired/inactive, block it.
    if (quiz.is_expired() or not quiz.active) and not godmode:
        return Response(
            {'error': f'"{quiz.description}" is either expired or inactive.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

        # Create the isolated sandbox database objects
    trial_questionpaper, trial_course, trial_module = test_mode(
        user, godmode, None, quiz_id, course_id
    )
    
    # ------------------ ADD THIS LINE HERE ------------------
    # Force the duplicate sandbox paper to sum its cloned question point counts!
    # Without this, empty "0.0" totals trigger a ZeroDivisionError at submission.
    trial_questionpaper.update_total_marks()
    # --------------------------------------------------------

    # The trial question paper is linked to a new trial quiz.
    trial_quiz = trial_questionpaper.quiz

    # Instead of an HTTP redirect, we return the IDs of the sandbox objects.
    # The React frontend can then route to the quiz taker page with these trial IDs.
    return Response({
        'message': 'Trial sandbox created successfully',
        'trial_course_id': trial_course.id,
        'trial_quiz_id': trial_quiz.id,
        'trial_module_id': trial_module.id,
        'trial_questionpaper_id': trial_questionpaper.id
    }, status=status.HTTP_201_CREATED)        



