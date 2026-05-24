from rest_framework import serializers
from yaksh.models import (
    Question, Quiz, QuestionPaper, AnswerPaper, Answer, Course,
    LearningModule, LearningUnit, Lesson, CourseStatus,
    Badge, UserBadge, BadgeProgress, UserStats, DailyActivity, UserActivity, Post, Comment, User, Profile,
    QuestionSet, AssignmentUpload
)
from grades.models import GradingSystem, GradeRange
from notifications_plugin.models import Notification
from taggit.models import Tag




class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    message_uid = serializers.CharField(source='message.uid', read_only=True)
    sender_name = serializers.CharField(source='message.creator.get_full_name', read_only=True)
    sender_username = serializers.CharField(source='message.creator.username', read_only=True)
    summary = serializers.CharField(source='message.summary', read_only=True)
    description = serializers.CharField(source='message.description', read_only=True)
    message_type = serializers.CharField(source='message.message_type', read_only=True)
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'message_uid', 'sender_name', 'sender_username',
            'summary', 'description', 'message_type', 
            'timestamp', 'read', 'time_since'
        ]
        read_only_fields = ['message_uid', 'timestamp']
    
    def get_time_since(self, obj):
        """Get human-readable time since notification was created"""
        from django.utils.timesince import timesince
        return timesince(obj.timestamp)





class GradeRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeRange
        fields = ['id', 'lower_limit', 'upper_limit', 'grade', 'description']
        read_only_fields = ['id']



class GradingSystemSerializer(serializers.ModelSerializer):
    grade_ranges = GradeRangeSerializer(many=True, source='graderange_set')

    class Meta:
        model = GradingSystem
        fields = ['id', 'name', 'description', 'grade_ranges', 'creator']
        read_only_fields = ['id', 'creator']

    def create(self, validated_data):
        grade_ranges_data = validated_data.pop('graderange_set')
        grading_system = GradingSystem.objects.create(**validated_data)
        for gr in grade_ranges_data:
            GradeRange.objects.create(system=grading_system, **gr)
        return grading_system

    def update(self, instance, validated_data):
        grade_ranges_data = validated_data.pop('graderange_set', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if grade_ranges_data is not None:
            instance.graderange_set.all().delete()
            for gr in grade_ranges_data:
                GradeRange.objects.create(system=instance, **gr)
        return instance

class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['uid', 'creator', 'created_at', 'modified_at', 'target_ct', 'target_id', 'target']

    def get_author(self, obj):
        # If the requester is the creator, show their name even if anon (so they know it's theirs)
        # Or if they are a moderator
        request = self.context.get('request')
        user = request.user if request else None
        
        if obj.anonymous:
            # If user is the creator or a moderator, reveal the name
            # Otherwise, hide it
            if user and (obj.creator == user or user.groups.filter(name='moderator').exists()):
                return obj.creator.get_full_name() or obj.creator.username
            return "Anonymous"
        
        return obj.creator.get_full_name() or obj.creator.username

    def get_is_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.creator == request.user
        return False

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['uid', 'creator', 'created_at', 'modified_at', 'post_field']

    def get_author(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        if obj.anonymous:
            if user and (obj.creator == user or user.groups.filter(name='moderator').exists()):
                 return obj.creator.get_full_name() or obj.creator.username
            return "Anonymous"
        
        return obj.creator.get_full_name() or obj.creator.username

    def get_is_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.creator == request.user
        return False

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with nested user fields"""
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_moderator = serializers.BooleanField(read_only=True)
    email_verified = serializers.BooleanField(source='is_email_verified', read_only=True)
    teacher_courses_count = serializers.SerializerMethodField()
    teacher_students_count = serializers.SerializerMethodField()
    student_enrolled_count = serializers.SerializerMethodField()
    student_completed_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = [
            'user_id', 'username', 'email', 'first_name', 'last_name',
            'roll_number', 'institute', 'department', 'position',
            'bio', 'phone', 'city', 'country', 'linkedin', 'github',
            'display_name', 'timezone', 'is_moderator', 'email_verified',
            'teacher_courses_count', 'teacher_students_count',
            'student_enrolled_count', 'student_completed_count'
        ]
        read_only_fields = ['user_id', 'username', 'is_moderator', 'email_verified',
                            'teacher_courses_count', 'teacher_students_count',
                            'student_enrolled_count', 'student_completed_count']
    
    def validate_email(self, value):
        """Validate that email is unique"""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
    def update(self, instance, validated_data):
        """Update both User and Profile models"""
        user_data = validated_data.pop('user', {})
        user = instance.user
        
        # Update User fields
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        if 'email' in user_data:
            user.email = user_data['email']
        user.save()
        
        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

    def get_teacher_courses_count(self, obj):
        try:
            return Course.objects.filter(creator=obj.user).count()
        except Exception:
            return 0

    def get_teacher_students_count(self, obj):
        try:
            courses = Course.objects.filter(creator=obj.user)
            return User.objects.filter(students__in=courses).distinct().count()
        except Exception:
            return 0

    def get_student_enrolled_count(self, obj):
        try:
            return Course.objects.filter(students=obj.user).count()
        except Exception:
            return 0

    def get_student_completed_count(self, obj):
        try:
            return CourseStatus.objects.filter(user=obj.user, percent_completed__gte=100).count()
        except Exception:
            return 0

class QuestionSerializer(serializers.ModelSerializer):
    test_cases = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    def to_bool(self, val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() == "true"
        return bool(val)  

    def get_test_cases(self, obj):
        try:
            tc_list = obj.get_test_cases_as_dict()
            
            # Bundle multiple ArrangeTestCase options into a single array for React
            if obj.type == 'arrange' and tc_list:
                arrange_options = [tc.get('options') for tc in tc_list if tc.get('type') == 'arrangetestcase']
                if arrange_options:
                    # Keep the first testcase structure and replace options with the array
                    first_tc = tc_list[0].copy()
                    first_tc['options'] = arrange_options
                    return [first_tc]

            # Bundle MCQ/MCC into a single test case for React
            if obj.type in ['mcq', 'mcc'] and tc_list:
                mcq_tcs = [tc for tc in tc_list if tc.get('type') == 'mcqtestcase']
                if mcq_tcs:
                    first_tc = mcq_tcs[0].copy()
                    options_array = []
                    correct_data = [] if obj.type == 'mcc' else 0
                    
                    for idx, tc in enumerate(mcq_tcs):
                        # FOSSEE stores options as JSON '["Option text"]'
                        try:
                            # Safely extract option string
                            opt_val = tc.get('options', '[]')
                            if isinstance(opt_val, str) and opt_val.startswith('['):
                                opt_val = json.loads(opt_val)
                            opt_text = opt_val[0] if isinstance(opt_val, list) and opt_val else str(opt_val)
                        except Exception:
                            opt_text = str(tc.get('options', ''))
                            
                        options_array.append(opt_text)
                        
                        if tc.get('correct') or tc.get('correct') == 'True':
                            if obj.type == 'mcc':
                                correct_data.append(idx)
                            else:
                                correct_data = idx
                                
                    first_tc['options'] = options_array
                    first_tc['correct'] = correct_data
                    return [first_tc]        
                    
            return tc_list
        except Exception:
            return []

    def get_files(self, obj):  
        import os
        from yaksh.models import FileUpload
        files = []
        request = self.context.get('request')  # Get request from context
        for f in FileUpload.objects.filter(question=obj):
            # Build absolute URL if request is available
            if request and hasattr(f.file, 'url'):
                file_url = request.build_absolute_uri(f.file.url)
            else:
                file_url = f.file.url if hasattr(f.file, "url") else ""
            
            files.append({
                "id": f.id,
                "name": os.path.basename(f.file.name),
                "url": file_url,
                "extract": f.extract,
                "hide": f.hide,
            })
        return files

    def update(self, instance, validated_data):
        # Update Question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update FileUpload extract/hide if files data is present
        files_data = self.initial_data.get("files")
        if files_data:
            from yaksh.models import FileUpload
            for file_data in files_data:
                file_id = file_data.get("id")
                if file_id is not None:
                    try:
                        file_obj = FileUpload.objects.get(id=file_id, question=instance)
                        # Coerce to bool in case frontend sends as string
                        extract = file_data.get("extract")
                        hide = file_data.get("hide")
                        if extract is not None:
                            file_obj.extract = str(extract).lower() == "true" if isinstance(extract, str) else bool(extract)
                        if hide is not None:
                            file_obj.hide = str(hide).lower() == "true" if isinstance(hide, str) else bool(hide)
                        file_obj.save()
                    except FileUpload.DoesNotExist:
                        continue
        return instance    

    class Meta:
        model = Question
        fields = '__all__'


class QuizSerializer(serializers.ModelSerializer):
    questionpaper_id = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = '__all__'
        
    def get_questionpaper_id(self, obj):
        # Dynamically fetch the attached Question Paper ID
        qp = obj.questionpaper_set.first()
        if qp:
            return qp.id
        # Fallback logic in case of legacy data
        if obj.question_paper:
            return obj.question_paper.id
        return None


class QuestionPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionPaper
        fields = '__all__'


class QuestionPaperDetailSerializer(serializers.ModelSerializer):
    fixed_questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionPaper
        fields = '__all__'


class AnswerPaperSerializer(serializers.ModelSerializer):

    questions = QuestionSerializer(many=True)

    class Meta:
        model = AnswerPaper
        fields = '__all__'


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'


class LearningUnitSerializer(serializers.ModelSerializer):

    quiz = QuizSerializer()
    lesson = LessonSerializer()

    class Meta:
        model = LearningUnit
        fields = '__all__'


class LearningModuleSerializer(serializers.ModelSerializer):

    learning_unit = LearningUnitSerializer(many=True)

    class Meta:
        model = LearningModule
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):

    learning_module = LearningModuleSerializer(many=True)

    class Meta:
        model = Course
        exclude = (
            'teachers',
            'rejected',
            'requests',
            'students',
            'grading_system',
            'view_grade',
        )


###############################################################################
# Badge & Achievement Serializers
###############################################################################

class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for Badge model"""
    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon', 'color', 'badge_type', 
                 'criteria_type', 'criteria_value']


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for earned badges with badge details"""
    badge = BadgeSerializer(read_only=True)
    earned_date = serializers.DateTimeField(format="%b %d, %Y")
    
    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'earned_date']


class BadgeProgressSerializer(serializers.ModelSerializer):
    """Serializer for badge progress tracking"""
    badge = BadgeSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()
    
    def get_progress_percentage(self, obj):
        return obj.progress_percentage()
    
    def get_steps(self, obj):
        return {
            'completed': obj.current_progress,
            'total': obj.badge.criteria_value
        }
    
    class Meta:
        model = BadgeProgress
        fields = ['id', 'badge', 'current_progress', 'progress_percentage', 'steps']


###############################################################################
# Stats & Activity Serializers
###############################################################################

class UserStatsSerializer(serializers.ModelSerializer):
    """Serializer for user statistics"""
    learning_hours = serializers.SerializerMethodField()
    
    def get_learning_hours(self, obj):
        hours = int(obj.total_learning_hours)
        minutes = int((obj.total_learning_hours - hours) * 60)
        return f"{hours}h {minutes}m"
    
    class Meta:
        model = UserStats
        fields = ['total_challenges_solved', 'challenges_this_week', 
                 'challenges_this_month', 'current_streak', 'longest_streak',
                 'learning_hours', 'last_activity_date']


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activity feed"""
    time = serializers.SerializerMethodField()
    
    def get_time(self, obj):
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.timestamp
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    
    class Meta:
        model = UserActivity
        fields = ['id', 'activity_type', 'title', 'description', 'icon', 
                 'color', 'badge_name', 'time', 'timestamp']


###############################################################################
# Enhanced Course Serializers for Student Dashboard
###############################################################################

class CourseProgressSerializer(serializers.ModelSerializer):
    """Enhanced course serializer with student progress"""
    progress = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    instructor = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    next_lesson = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    
    def get_progress(self, obj):
        user = self.context.get('user')
        if not user:
            return 0
        
        try:
            course_status = CourseStatus.objects.get(user=user, course=obj)
            # Count total learning units across all modules
            total_units = 0
            for module in obj.learning_module.all():
                total_units += module.learning_unit.count()
            
            if total_units == 0:
                return 0
            
            completed_units = course_status.completed_units.count()
            return int((completed_units / total_units) * 100)
        except CourseStatus.DoesNotExist:
            return 0
    
    def get_lessons(self, obj):
        total = 0
        completed = 0
        
        user = self.context.get('user')
        if user:
            try:
                course_status = CourseStatus.objects.get(user=user, course=obj)
                completed = course_status.completed_units.filter(type='lesson').count()
            except CourseStatus.DoesNotExist:
                pass
        
        for module in obj.learning_module.all():
            total += module.learning_unit.filter(type='lesson').count()
        
        return {'completed': completed, 'total': total}
    
    def get_instructor(self, obj):
        creator = obj.creator
        return f"{creator.first_name} {creator.last_name}" if creator.first_name else creator.username
    
    def get_color(self, obj):
        # Assign colors based on course id for variety
        colors = ['indigo', 'blue', 'purple', 'pink', 'cyan', 'green', 'orange']
        return colors[obj.id % len(colors)]
    
    def get_next_lesson(self, obj):
        user = self.context.get('user')
        if not user:
            return None
        
        try:
            course_status = CourseStatus.objects.get(user=user, course=obj)
            if course_status.current_unit and course_status.current_unit.type == 'lesson':
                return course_status.current_unit.lesson.name
        except (CourseStatus.DoesNotExist, AttributeError):
            pass
        
        # Get first lesson
        for module in obj.learning_module.order_by('order'):
            first_lesson = module.learning_unit.filter(type='lesson').order_by('order').first()
            if first_lesson:
                return first_lesson.lesson.name
        
        return None
    
    def get_is_enrolled(self, obj):
        user = self.context.get('user')
        if not user:
            return False
        return obj.students.filter(id=user.id).exists()
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'progress', 'lessons', 'instructor', 'color', 
                 'next_lesson', 'is_enrolled', 'code', 'created_on']

class CourseCatalogSerializer(serializers.ModelSerializer):
    """Serializer for course catalog with enrollment info"""
    instructor = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    modules = LearningModuleSerializer(source='learning_module', many=True, read_only=True)
    instructions = serializers.CharField(read_only=True)
    start_date = serializers.DateTimeField(source='start_enroll_time', read_only=True)
    end_date = serializers.DateTimeField(source='end_enroll_time', read_only=True)
    enrollment = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()  # NEW FIELD

    def get_enrollment(self, obj):
        if not obj.is_active_enrollment():
            return "No Enrollment Allowed"
        return obj.enrollment
    
    def get_enrollment_status(self, obj):
        """
        Get detailed enrollment status for the current user.
        Returns:
        - "enrolled" : User is enrolled (show Start/Continue button)
        - "request_pending" : User has requested enrollment
        - "request_rejected" : User's request was rejected
        - "can_enroll_open" : User can enroll (open enrollment)
        - "can_enroll_request" : User can request enrollment
        - "no_enrollment_allowed" : Enrollment period has ended
        - "inactive_course" : Course is not active
        """
        user = self.context.get('user')
        if not user:
            request = self.context.get('request')
            if request:
                user = request.user
        
        if not user or not user.is_authenticated:
            return "unauthenticated"
        
        # Check if course is active
        if not obj.active:
            return "inactive_course"
        
        # Check if user is already enrolled
        if obj.students.filter(id=user.id).exists():
            return "enrolled"
        
        # Check if user has pending request
        if obj.requests.filter(id=user.id).exists():
            return "request_pending"
        
        # Check if user was rejected
        if obj.rejected.filter(id=user.id).exists():
            return "request_rejected"
        
        # Check if enrollment is active
        if not obj.is_active_enrollment():
            return "no_enrollment_allowed"
        
        # Check enrollment method
        if obj.is_self_enroll():
            return "can_enroll_open"
        else:
            return "can_enroll_request"
    
    def get_instructor(self, obj):
        creator = obj.creator
        return f"Prof. {creator.first_name} {creator.last_name}" if creator.first_name else f"Prof. {creator.username}"
    
    def get_level(self, obj):
        # You can add a level field to Course model or compute it
        return "Intermediate"
    
    def get_rating(self, obj):
        # Placeholder - implement rating system later
        return 4.5
    
    def get_students_count(self, obj):
        return obj.students.count()
    
    def get_duration(self, obj):
        # Estimate based on modules/lessons
        total_lessons = 0
        for module in obj.learning_module.all():
            total_lessons += module.learning_unit.filter(type='lesson').count()
        hours = total_lessons * 2  # Estimate 2 hours per lesson
        return f"{hours} hours"
    
    def get_progress(self, obj):
        user = self.context.get('user')
        if not user:
            return 0
        
        try:
            course_status = CourseStatus.objects.get(user=user, course=obj)
            total_units = sum(module.learning_unit.count() for module in obj.learning_module.all())
            
            if total_units == 0:
                return 0
            
            completed_units = course_status.completed_units.count()
            return int((completed_units / total_units) * 100)
        except CourseStatus.DoesNotExist:
            return 0
    
    def get_color(self, obj):
        colors = ['cyan', 'blue', 'orange', 'green', 'purple', 'indigo', 'pink']
        return colors[obj.id % len(colors)]
    
    def get_is_enrolled(self, obj):
        user = self.context.get('user')
        if not user:
            # If called primarily from a context where request is available (like viewset)
            request = self.context.get('request')
            if request:
                user = request.user
        
        if user and user.is_authenticated:
            return obj.students.filter(id=user.id).exists()
        return False
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'instructor', 'level', 'rating', 'students_count', 
            'duration', 'progress', 'color', 'is_enrolled', 'code', 
            'modules', 'instructions', 'start_date', 'end_date', 'enrollment',
            'enrollment_status', 'active' 
        ]


###############################################################################
# Enhanced Lesson & Module Serializers
###############################################################################

class LessonDetailSerializer(serializers.ModelSerializer):
    """Detailed lesson serializer with video and files"""
    video_url = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    course_id = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    module_id = serializers.SerializerMethodField()
    module_name = serializers.SerializerMethodField()
    
    def get_video_url(self, obj):
        if obj.video_path:
            return obj.video_path
        return None
    
    def get_files(self, obj):
        request = self.context.get('request')
        files = obj.get_files()
        
        result = []
        for f in files:
            if not f.file:
                continue
            
            # Construct absolute URL if request is available, otherwise use default url
            file_url = request.build_absolute_uri(f.file.url) if request else f.file.url
            
            result.append({
                'id': f.id, 
                'url': file_url,
                'name': f.file.name.split('/')[-1]  # Clean display name without folder path
            })
            
        return result
        
    def get_course_id(self, obj):
        # course_id is already passed from the view via context
        course_id = self.context.get('course_id')
        if course_id:
            return course_id
            
        # Fallback if accessed elsewhere without course_id in context
        from yaksh.models import LearningUnit, Course
        learning_unit = LearningUnit.objects.filter(lesson=obj).first()
        if learning_unit:
            course = Course.objects.filter(learning_module__learning_unit=learning_unit).first()
            if course:
                return course.id
        return None

    def get_course_name(self, obj):
        course = self.context.get('course')
        if course:
            return course.name
            
        course_id = self.context.get('course_id')
        from yaksh.models import LearningUnit, Course
        
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                return course.name
            except Course.DoesNotExist:
                pass
                
        # Fallback
        learning_unit = LearningUnit.objects.filter(lesson=obj).first()
        if learning_unit:
            course = Course.objects.filter(learning_module__learning_unit=learning_unit).first()
            if course:
                return course.name
        return None
        
    def get_module_id(self, obj):
        # Find the module containing this lesson's learning unit
        from yaksh.models import LearningUnit, LearningModule
        learning_unit = LearningUnit.objects.filter(lesson=obj).first()
        if learning_unit:
            module = LearningModule.objects.filter(learning_unit=learning_unit).first()
            if module:
                return module.id
        return None
        
    def get_module_name(self, obj):
        # Find the module containing this lesson's learning unit
        from yaksh.models import LearningUnit, LearningModule
        learning_unit = LearningUnit.objects.filter(lesson=obj).first()
        if learning_unit:
            module = LearningModule.objects.filter(learning_unit=learning_unit).first()
            if module:
                return module.name
        return None
    
    def get_is_completed(self, obj):
        user = self.context.get('user')
        course = self.context.get('course')
        course_id = self.context.get('course_id')

        if course and not course_id:
            course_id = course.id
        
        if not user or not course_id:
            return False
        
        try:
            course_status = CourseStatus.objects.get(user=user, course_id=course_id)
            # Find the learning unit for this lesson
            learning_unit = LearningUnit.objects.filter(
                lesson=obj,
                learning_unit__learning_module__id=course_id
            ).first()
            
            if learning_unit:
                return course_status.completed_units.filter(id=learning_unit.id).exists()
        except CourseStatus.DoesNotExist:
            pass
        
        return False
    
    class Meta:
        model = Lesson
        fields = ['id', 'name', 'description', 'html_data', 'video_url', 
                 'video_file', 'files', 'is_completed', 'active', 
                 'course_id', 'course_name', 'module_id', 'module_name']

class LearningUnitDetailSerializer(serializers.ModelSerializer):
    """Detailed learning unit with quiz or lesson data"""
    lesson = LessonDetailSerializer(read_only=True)
    quiz = QuizSerializer(read_only=True)
    status = serializers.SerializerMethodField()
    
    def get_status(self, obj):
        user = self.context.get('user')
        course = self.context.get('course')
        course_id = self.context.get('course_id')
        
        if not user:
            return "not_attempted"

        if course:
            return obj.get_completion_status(user, course)

        if course_id:
            try:
                from yaksh.models import Course
                course = Course.objects.get(id=course_id)
                return obj.get_completion_status(user, course)
            except:
                pass
            
        return "not_attempted"
    
    class Meta:
        model = LearningUnit
        fields = ['id', 'order', 'type', 'lesson', 'quiz', 'status', 'check_prerequisite']


        
class LearningModuleDetailSerializer(serializers.ModelSerializer):
    """Detailed module serializer with units and progress"""
    units = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    def get_units(self, obj):
        units = obj.get_learning_units()
        serializer = LearningUnitDetailSerializer(
            units, many=True, context=self.context
        )
        return serializer.data
    
    def get_progress(self, obj):
        user = self.context.get('user')
        course = self.context.get('course')
        course_id = self.context.get('course_id')
        
        # Fallback if course object not passed but ID is
        if not course and course_id:
             try:
                 course = Course.objects.get(id=course_id)
             except Course.DoesNotExist:
                 pass
        
        if user and course:
            return obj.get_module_complete_percent(course, user)
        
        return 0
    
    class Meta:
        model = LearningModule
        fields = ['id', 'name', 'description', 'order', 'units', 'progress', 
                 'check_prerequisite', 'active']



class LearningModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningModule
        fields = '__all__' 


class MinimalLearningUnitSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    check_prerequisite = serializers.BooleanField()
    # Add a custom method field for is_exercise
    is_exercise = serializers.SerializerMethodField()

    def get_display_name(self, obj):
        # Restored original logic to prevent NameError
        if obj.type == "quiz" and obj.quiz:
            return f"{obj.quiz.description} (quiz)"
        elif obj.type == "lesson" and obj.lesson:
            return f"{obj.lesson.name} (lesson)"
        return ""

    def get_is_exercise(self, obj):
        if obj.type == 'quiz' and obj.quiz:
            return obj.quiz.is_exercise
        return False

    class Meta:
        model = LearningUnit
        fields = ['id', 'type', 'order', 'display_name', 'check_prerequisite', 'is_exercise']


#class SimpleUserSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = User
#        fields = ['id', 'username', 'email', 'first_name', 'last_name']

# Grading Serializers
class SimpleUserSerializer(serializers.ModelSerializer):
    """Serializer for user basic info"""
    roll_number = serializers.CharField(source='profile.roll_number', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'roll_number']


class AnswerDetailSerializer(serializers.ModelSerializer):
    """Detailed answer serializer for grading"""
    question = QuestionSerializer(read_only=True)
    
    class Meta:
        model = Answer
        fields = ['id', 'question', 'answer', 'marks', 'error', 'correct', 'skipped']


class AnswerPaperGradingSerializer(serializers.ModelSerializer):
    """AnswerPaper serializer for grading interface"""
    user = SimpleUserSerializer(read_only=True)
    answers = AnswerDetailSerializer(many=True, read_only=True)
    question_paper = QuestionPaperSerializer(read_only=True)
    
    class Meta:
        model = AnswerPaper
        fields = ['id', 'user', 'question_paper', 'answers', 'marks_obtained', 
                 'percent', 'status', 'attempt_number', 'comments', 'start_time', 
                 'end_time']


class UserAttemptSerializer(serializers.ModelSerializer):
    """Serializer for user attempts list"""
    user = SimpleUserSerializer(read_only=True)
    
    class Meta:
        model = AnswerPaper
        fields = ['id', 'user', 'attempt_number', 'marks_obtained', 'status', 
                 'start_time', 'end_time']


class GradeUpdateSerializer(serializers.Serializer):
    """Serializer for updating grades"""
    question_id = serializers.IntegerField()
    marks = serializers.FloatField()
    comments = serializers.CharField(required=False, allow_blank=True)

# Specialized Grading Serializers (Quizzes Only - No Lessons)
class QuizOnlyLearningUnitSerializer(serializers.ModelSerializer):
    """Learning unit serializer that only includes quiz units for grading"""
    quiz = QuizSerializer(read_only=True)
    
    class Meta:
        model = LearningUnit
        fields = ['id', 'quiz', 'order', 'type', 'check_prerequisite']
    
    def to_representation(self, instance):
        """Only serialize quiz units, skip lesson units"""
        if instance.type != 'quiz':
            return None
        return super().to_representation(instance)


class QuizOnlyLearningModuleSerializer(serializers.ModelSerializer):
    """Learning module serializer that only includes quiz units"""
    learning_unit = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningModule
        fields = ['id', 'name', 'description', 'order', 'check_prerequisite', 
                 'check_prerequisite_passes', 'html_data', 'active', 'learning_unit']
    
    def get_learning_unit(self, obj):
        """Filter to only include quiz units"""
        quiz_units = obj.learning_unit.filter(type='quiz').order_by('order')
        serializer = QuizOnlyLearningUnitSerializer(quiz_units, many=True)
        # Filter out None values (from lesson units)
        return [unit for unit in serializer.data if unit is not None]


class GradingCourseSerializer(serializers.ModelSerializer):
    """Specialized course serializer for grading - only includes quizzes"""
    learning_module = QuizOnlyLearningModuleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'enrollment', 'active', 'code', 'hidden', 
                 'created_on', 'is_trial', 'instructions', 'start_enroll_time', 
                 'end_enroll_time', 'creator', 'learning_module'] 


class MonitorAnswerPaperSerializer(serializers.ModelSerializer):
    """Serializer for monitoring answer papers"""
    user = SimpleUserSerializer(read_only=True)
    questions_attempted_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AnswerPaper
        fields = [
            'id', 'user', 'status', 'start_time', 'end_time', 
            'marks_obtained', 'user_ip', 'questions_attempted_count', 
            'passed', 'percent'
        ]

    def get_questions_attempted_count(self, obj):
        # Expects 'questions_attempted' dict in context
        return self.context.get('questions_attempted', {}).get(obj.id, 0)                 


class StudentDashboardLearningModuleSerializer(serializers.ModelSerializer):
    """Simple serializer for course content listing"""
    class Meta:
        model = LearningModule
        fields = ['id', 'name']

class StudentDashboardCourseSerializer(serializers.ModelSerializer):
    completion_percentage = serializers.SerializerMethodField()
    instructor = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    start_date = serializers.DateTimeField(source='start_enroll_time', read_only=True)
    end_date = serializers.DateTimeField(source='end_enroll_time', read_only=True)
    description = serializers.CharField(source='instructions', read_only=True)
    course_content = StudentDashboardLearningModuleSerializer(source='learning_module', many=True, read_only=True)
    # Add new fields below as needed:
    lessons = serializers.SerializerMethodField()
    recent_activities = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    instructor_email = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'code', 'start_date', 'end_date', 'active', 
            'description', 'completion_percentage', 'instructor', 'instructor_email',
            'is_enrolled', 'course_content', 'lessons', 'recent_activities', 'badges'
        ]

    def get_completion_percentage(self, obj):
        if 'completion_percentages' in self.context:
            return self.context['completion_percentages'].get(obj.id)
        user = self.context.get('user')
        if user and obj.is_enrolled(user):
            return obj.get_completion_percent(user)
        return None

    def get_instructor(self, obj):
        return obj.creator.get_full_name() if obj.creator else ""

    def get_instructor_email(self, obj):
        return obj.creator.email if obj.creator else ""

    def get_is_enrolled(self, obj):
        user = self.context.get('user')
        return obj.is_enrolled(user) if user else False

    def get_lessons(self, obj):
        user = self.context.get('user')
        lessons = []
        for module in obj.learning_module.all():
            for unit in module.learning_unit.all():
                if unit.lesson:
                    lessons.append({
                        "id": unit.lesson.id,
                        "name": unit.lesson.name,
                        "completed": unit.lesson.is_completed_by(user) if hasattr(unit.lesson, "is_completed_by") else False
                    })
        return lessons

    def get_recent_activities(self, obj):
        user = self.context.get('user')
        activities = UserActivity.objects.filter(
            user=user, related_course_id=obj.id
        ).order_by('-timestamp')[:5]
        return UserActivitySerializer(activities, many=True).data

    def get_badges(self, obj):
        user = self.context.get('user')
        # Remove badge__course=obj if Badge does not have a course field
        badges = UserBadge.objects.filter(user=user)
        return UserBadgeSerializer(badges, many=True).data
        



class CourseWithCompletionSerializer(serializers.Serializer):
    data = CourseCatalogSerializer()
    completion_percentage = serializers.FloatField(allow_null=True)      


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class QuestionSetSerializer(serializers.ModelSerializer):
    # This renders the many-to-many relationship using full Question objects mapping
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionSet
        fields = '__all__'      



class StudentAnswerPaperSerializer(serializers.ModelSerializer):
    """Minimal nested serializer for returning answer paper data to students."""
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = AnswerPaper
        fields = [
            'id', 'user', 'question_paper', 'attempt_number', 
            'start_time', 'end_time', 'status', 'marks_obtained', 
            'questions', 'percent'
        ]  # Removed percent_completed and time_left, added percent


class ViewAnswerPaperResponseSerializer(serializers.Serializer):
    """Wrapper serializer for the view_answerpaper response."""
    quiz = QuizSerializer(read_only=True)
    course_id = serializers.IntegerField(read_only=True)
    has_user_assignments = serializers.BooleanField(read_only=True)
    
    # Nested data object matching get_user_data structure
    data = serializers.SerializerMethodField()

    def get_data(self, obj):
        user = obj.get('user')
        papers = obj.get('papers')
        return {
            'user': SimpleUserSerializer(user).data if user else None,
            'profile': ProfileSerializer(user.profile).data if hasattr(user, 'profile') else None,
            'papers': StudentAnswerPaperSerializer(papers, many=True).data,
            'questionpaperid': obj.get('questionpaper_id')
        }        
