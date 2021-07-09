from rest_framework import serializers

# Local imports
from yaksh.courses.models import Course, Module, Lesson


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
        instance.view_grade = validated_data.get("view_grade")
        instance.save()
        return instance


class GenericField(serializers.RelatedField):

    def to_representation(self, value):
        obj = value.content_object
        if isinstance(obj, Lesson):
            serializer_data = LessonSerializer(obj).data
            serializer_data["order"] = value.order
        else:
            serializer_data = {}
        return serializer_data


class ModuleSerializer(serializers.ModelSerializer):
    units = GenericField(read_only=True, many=True)

    class Meta:
        model = Module
        fields = "__all__"

    def create(self, validated_data):
        module = Module.objects.create(**validated_data)
        return module

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.description = validated_data.get("description")
        instance.active = validated_data.get("active")
        instance.owner_id = validated_data.get("owner")
        instance.course_id = validated_data.get("course")
        instance.order = validated_data.get("order")
        instance.save()
        return instance


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"

    def create(self, validated_data):
        lesson = Lesson.objects.create(**validated_data)
        return lesson

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.description = validated_data.get("description")
        instance.html_data = validated_data.get("html_data")
        instance.owner_id = validated_data.get("owner")
        instance.active = validated_data.get("active")
        instance.video_file = validated_data.get("video_file")
        instance.save()
        return instance
