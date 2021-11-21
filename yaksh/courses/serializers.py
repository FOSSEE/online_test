from re import search
from rest_framework import serializers

# Local imports
from yaksh.courses.models import (
    Course, Module, Lesson, Topic, TableOfContent, Question,
    TestCase, StandardTestCase, StdIOBasedTestCase, McqTestCase,
    HookTestCase, IntegerTestCase, StringTestCase,
    FloatTestCase, ArrangeTestCase, Quiz, QuestionPaper, QuestionSet
)


class ProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    roll_number = serializers.CharField()
    institute = serializers.CharField()
    department = serializers.CharField()
    position = serializers.CharField()
    timezone = serializers.CharField()


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    last_login = serializers.DateTimeField()
    date_joined = serializers.DateTimeField()
    profile = ProfileSerializer()


class CourseSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField()
    is_allotted = serializers.SerializerMethodField('is_allotted_course')    

    class Meta:
        model = Course
        fields = "__all__"

    def is_allotted_course(self, obj):
        user_id = self.context.get("user_id")
        return obj.owner_id != user_id

    def create(self, validated_data):
        course = Course.objects.create(**validated_data)
        if validated_data.get("code"):
            course.hidden = True
            course.save()
        return course

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.enrollment = validated_data.get("enrollment")
        instance.code = validated_data.get("code")
        instance.active = validated_data.get("active")
        if validated_data.get("code"):
            instance.hidden = True
        else:
            instance.hidden = False
        instance.owner = validated_data.get("owner")
        instance.instructions = validated_data.get("instructions")
        instance.start_enroll_time = validated_data.get("start_enroll_time")
        instance.end_enroll_time = validated_data.get("end_enroll_time")
        instance.view_grade = validated_data.get("view_grade")
        instance.save()
        return instance


class UnitSerializer(serializers.RelatedField):

    def to_representation(self, value):
        obj = value.content_object
        if isinstance(obj, Lesson):
            serializer_data = LessonSerializer(
            obj, context=self.context).data
            serializer_data["type"] = "Lesson"
        else:
            serializer_data = QuizSerializer(obj).data
            serializer_data["type"] = "Quiz"
        serializer_data["order"] = value.order
        serializer_data['unit_id'] = value.id
        return serializer_data


class ModuleSerializer(serializers.ModelSerializer):
    units = UnitSerializer(read_only=True, many=True)
    owner_id = serializers.IntegerField()
    course_id = serializers.IntegerField()
    has_units = serializers.ReadOnlyField()

    class Meta:
        model = Module
        fields = ("id", "name", "description", "owner_id", "units",
                  "course_id", "order", "html_data", "active", "has_units")

    def create(self, validated_data):
        module = Module.objects.create(**validated_data)
        return module

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.description = validated_data.get("description")
        instance.active = validated_data.get("active")
        instance.owner_id = validated_data.get("owner_id")
        instance.course_id = validated_data.get("course_id")
        instance.order = validated_data.get("order")
        instance.save()
        return instance


class LessonSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField()

    class Meta:
        model = Lesson
        fields = ("id", "name", "description", "html_data", "owner_id",
                  "active", "video_file", "video_path")

    def create(self, validated_data):
        lesson = Lesson.objects.create(**validated_data)
        return lesson

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.description = validated_data.get("description")
        instance.html_data = validated_data.get("html_data")
        instance.owner_id = validated_data.get("owner_id")
        instance.active = validated_data.get("active")
        instance.video_file = validated_data.get("video_file")
        instance.video_path = validated_data.get("video_path")
        instance.save()
        return instance


class TopicSerializer(serializers.ModelSerializer):

    class Meta:
        model = Topic
        fields = "__all__"

    def create(self, validated_data):
        topic = Topic.objects.create(**validated_data)
        return topic

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.description = validated_data.get("description")
        instance.save()
        return instance


class MCQSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        tc = McqTestCase.objects.create(**validated_data)
        return tc

    class Meta:
        model = McqTestCase
        exclude = ("question",)


class AssertionSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        tc = StandardTestCase.objects.create(**validated_data)
        return tc

    class Meta:
        model = StandardTestCase
        exclude = ("question",)


class StdioSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        tc = StdIOBasedTestCase.objects.create(**validated_data)
        return tc

    class Meta:
        model = StdIOBasedTestCase
        exclude = ("question",)


class HookSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        tc = HookSerializer.objects.create(**validated_data)
        return tc

    class Meta:
        model = HookTestCase
        exclude = ("question",)


class IntegerSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        tc = IntegerTestCase.objects.create(**validated_data)
        return tc

    class Meta:
        model = IntegerTestCase
        exclude = ("question",)


class FloatSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        tc = FloatTestCase.objects.create(**validated_data)
        return tc

    class Meta:
        model = FloatTestCase
        exclude = ("question",)


class StringSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        print(validated_data)
        tc = StringTestCase.objects.create(**validated_data)
        return tc

    class Meta:
        model = StringTestCase
        exclude = ("question",)


class ArrangeSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        tc = ArrangeTestCase.objects.create(**validated_data)
        return tc

    class Meta:
        model = ArrangeTestCase
        exclude = ("question",)


class TestCaseSerializer(serializers.ModelSerializer):
    serializer_mapper = {
        "mcqtestcase": MCQSerializer,
        "standardtestcase": AssertionSerializer,
        "stdiobasedtestcase": StdioSerializer,
        "hooktestcase": HookSerializer,
        "integertestcase": IntegerSerializer,
        "stringtestcase": StringSerializer,
        "floattestcase": FloatSerializer,
        "arrangetestcase": ArrangeSerializer,
    }
    id = serializers.IntegerField(required=False)
    question_id = serializers.IntegerField(required=False)
    options = serializers.CharField(required=False)
    correct_ans = serializers.CharField(required=False)
    correct = serializers.BooleanField(required=False)
    test_case = serializers.CharField(required=False)
    test_case_args = serializers.CharField(required=False, allow_blank=True)
    expected_input = serializers.CharField(required=False, allow_blank=True)
    expected_output = serializers.CharField(required=False)
    hook_code = serializers.CharField(required=False)
    string_check = serializers.CharField(required=False)
    error_margin = serializers.FloatField(required=False)
    weight = serializers.FloatField(required=False)
    hidden = serializers.BooleanField(required=False)
    delete = serializers.BooleanField(required=False)

    def create(self, validated_data):
        tc_type = validated_data.get("type")
        cls = self.serializer_mapper[tc_type]
        created = None
        if tc_type == "mcqtestcase":
            serializer = cls(data=validated_data)
            if serializer.is_valid():
                created = serializer.save()
        elif tc_type == "standardtestcase":
            serializer = cls(data=validated_data)
            if serializer.is_valid():
                created = serializer.save()
        elif tc_type == "stdiobasedtestcase":
            serializer = cls(data=validated_data)
            if serializer.is_valid():
                created = serializer.save()
        elif tc_type == "hooktestcase":
            serializer = cls(data=validated_data)
            if serializer.is_valid():
                created = serializer.save()
        elif tc_type == "integertestcase":
            serializer = cls(data=validated_data)
            if serializer.is_valid():
                created = serializer.save()
        elif tc_type == "stringtestcase":
            serializer = cls(data=validated_data)
            if serializer.is_valid():
                created = serializer.save()
        elif tc_type == "floattestcase":
            serializer = cls(data=validated_data)
            if serializer.is_valid():
                created = serializer.save()
        else:
            serializer = cls(data=validated_data)
            if serializer.is_valid():
                created = serializer.save()
        return created

    def update(self, instance, validated_data):
        tc_type = validated_data.get("type")
        if tc_type == "mcqtestcase":
            mcq_tc = instance.mcqtestcase
            mcq_tc.options = validated_data.get("options")
            mcq_tc.correct = validated_data.get("correct")
            mcq_tc.save()
        elif tc_type == "standardtestcase":
            assert_tc = instance.standardtestcase
            assert_tc.test_case = validated_data.get("test_case")
            assert_tc.test_case_args = validated_data.get("test_case_args")
            assert_tc.weight = validated_data.get("weight")
            assert_tc.hidden = validated_data.get("hidden")
            assert_tc.save()
        elif tc_type == "stdiobasedtestcase":
            stdio_tc = instance.stdiobasedtestcase
            stdio_tc.expected_input = validated_data.get("expected_input")
            stdio_tc.expected_output = validated_data.get("expected_output")
            stdio_tc.weight = validated_data.get("weight")
            stdio_tc.hidden = validated_data.get("hidden")
            stdio_tc.save()
        elif tc_type == "hooktestcase":
            hook_tc = instance.hooktestcase
            hook_tc.hook_code = validated_data.get("hook_code")
            hook_tc.weight = validated_data.get("weight")
            hook_tc.hidden = validated_data.get("hidden")
            hook_tc.save()
        elif tc_type == "integertestcase":
            int_tc = instance.integertestcase
            int_tc.correct_ans = validated_data.get("correct_ans")
            int_tc.save()
        elif tc_type == "stringtestcase":
            string_tc = instance.stringtestcase
            string_tc.correct_ans = validated_data.get("correct_ans")
            string_tc.string_check = validated_data.get("string_check")
            string_tc.save()
        elif tc_type == "floattestcase":
            float_tc = instance.floattestcase
            float_tc.correct_ans = validated_data.get("correct_ans")
            float_tc.error_margin = validated_data.get("error_margin")
            float_tc.save()
        else:
            arrange_tc = instance.arrangetestcase
            arrange_tc.options = validated_data.get("options")
            arrange_tc.save()
        return instance

    def to_representation(self, value):
        cls = self.serializer_mapper[value.type]
        serialized_data = {}
        if value.type == "mcqtestcase":
            serialized_data = cls(value.mcqtestcase).data
        elif value.type == "standardtestcase":
            serialized_data = cls(value.standardtestcase).data
        elif value.type == "stdiobasedtestcase":
            serialized_data = cls(value.stdiobasedtestcase).data
        elif value.type == "hooktestcase":
            serialized_data = cls(value.hooktestcase).data
        elif value.type == "integertestcase":
            serialized_data = cls(value.integertestcase).data
        elif value.type == "stringtestcase":
            serialized_data = cls(value.stringtestcase).data
        elif value.type == "floattestcase":
            serialized_data = cls(value.floattestcase).data
        else:
            serialized_data = cls(value.arrangetestcase).data
        serialized_data["type"] = value.type
        serialized_data["delete"] = False
        return serialized_data

    class Meta:
        model = TestCase
        fields = "__all__"


class QuestionSerializer(serializers.ModelSerializer):
    test_cases = TestCaseSerializer(many=True)

    def __init__(self, *args, **kwargs):
        fields = kwargs.get('context', {}).get("fields", None)
        exclude = kwargs.get('context', {}).get("exclude", None)
        super(QuestionSerializer, self).__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        if exclude is not None:
            for field_name in exclude:
                self.fields.pop(field_name)

    class Meta:
        model = Question
        fields = "__all__"

    def create(self, validated_data):
        test_cases = validated_data.pop("test_cases")
        question = Question.objects.create(**validated_data)
        for tc_data in test_cases:
            tc_data["question_id"] = question.id
            self.updateTestCases(None, tc_data)
        return question

    def update(self, instance, validated_data):
        test_cases = validated_data.pop("test_cases")
        instance.summary = validated_data.get("summary")
        instance.description = validated_data.get("description")
        instance.points = validated_data.get("points")
        instance.language = validated_data.get("language")
        instance.topic = validated_data.get("topic")
        instance.type = validated_data.get("type")
        instance.active = validated_data.get("active")
        instance.snippet = validated_data.get("snippet")
        instance.user = validated_data.get("user")
        instance.partial_grading = validated_data.get("partial_grading")
        instance.grade_assignment_upload = validated_data.get(
                                            "grade_assignment_upload"
                                            )
        instance.min_time = validated_data.get("min_time")
        instance.solution = validated_data.get("solution")
        instance.save()
        for tc_data in test_cases:
            try:
                tc = TestCase.objects.only("id").get(id=tc_data.get("id"))
                if tc_data.get("delete"):
                    tc.delete()
                else:
                    self.updateTestCases(tc, tc_data)
            except TestCase.DoesNotExist:
                tc_data["question_id"] = instance.id
                self.updateTestCases(None, tc_data)
        return instance

    def updateTestCases(self, tc, tc_data):
        serializer = TestCaseSerializer(tc, data=tc_data)
        if serializer.is_valid():
            instance = serializer.save()
            return instance


class TOCSerializer(serializers.ModelSerializer):

    class Meta:
        model = TableOfContent
        exclude = ["object_id",]

    def to_representation(self, value):
        obj = value.content_object
        if isinstance(obj, Topic):
            serializer_data = TopicSerializer(obj).data
        elif isinstance(obj, Question):
            serializer_data = QuestionSerializer(obj).data
        else:
            serializer_data = {}
        serializer_data["toc_id"] = value.id
        serializer_data["ctype"] = value.get_content_display()
        serializer_data["time"] = value.time
        return serializer_data


class QuizSerializer(serializers.ModelSerializer):

    class Meta:
        model = Quiz
        fields = "__all__"

    def create(self, validated_data):
        quiz = Quiz.objects.create(**validated_data)
        QuestionPaper.objects.create(quiz_id=quiz.id)
        return quiz

    def update(self, instance, validated_data):
        instance.start_date_time = validated_data.get("start_date_time")
        instance.end_date_time = validated_data.get("end_date_time")
        instance.duration = validated_data.get("duration")
        instance.active = validated_data.get("active")
        instance.description = validated_data.get("description")
        instance.pass_criteria = validated_data.get("pass_criteria")
        instance.attempts_allowed = validated_data.get("attempts_allowed")
        instance.time_between_attempts = validated_data.get("time_between_attempts")
        instance.is_trial = validated_data.get("is_trial")
        instance.instructions = validated_data.get("instructions")
        instance.view_answerpaper = validated_data.get("view_answerpaper")
        instance.allow_skip = validated_data.get("allow_skip")
        instance.weightage = validated_data.get("weightage")
        instance.is_exercise = validated_data.get("is_exercise")
        instance.owner = validated_data.get("owner")
        instance.save()

        return instance


class EnrollmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    student = UserSerializer()
    course_id = serializers.IntegerField()
    status = serializers.IntegerField()
    created_on = serializers.DateTimeField()


class CourseTeacherSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    teacher = UserSerializer(read_only=True)
    course_id = serializers.IntegerField(read_only=True)


class CourseProgressSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    course_id = serializers.IntegerField()
    user = UserSerializer()
    grade = serializers.CharField()
    percent_completed = serializers.IntegerField()
    unit = serializers.SerializerMethodField('current_unit')

    def current_unit(self, obj):
        unit = obj.current_unit
        NoneType = type(None)
        if not isinstance(unit, NoneType):
            if isinstance(unit.content_object, Lesson):
                return unit.content_object.name
            else:
                return unit.content_object.summary
        else:
            return None


class RandomSetSerializer(serializers.Serializer):
    marks = serializers.FloatField()
    num_questions = serializers.IntegerField()
    questions = QuestionSerializer(
        many=True, context={"fields": ["id", "summary", "points"]}
    )


class QuestionPaperSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    fixed_questions = QuestionSerializer(
        many=True, context={"fields": ["id", "summary", "points"]}
    )
    random_questions = RandomSetSerializer(many=True)
    shuffle_questions = serializers.BooleanField()
    total_marks = serializers.FloatField()
    fixed_question_order = serializers.JSONField()
    shuffle_testcases = serializers.BooleanField()
