from rest_framework import serializers

from yaksh.models import Course, Lesson


class PostObjectRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        if isinstance(value, Course):
            return 'Course: ' + value.name
        elif isinstance(value, Lesson):
            return 'Lesson: ' + value.name
        raise Exception('Unexpected type of tagged object')


class UserRelatedSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return value.username
