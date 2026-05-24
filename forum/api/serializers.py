from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from forum.models import Post, Comment
from yaksh.models import Course, Lesson
from .relations import PostObjectRelatedField


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['id', 'description', 'image', 'active', 'anonymous', 'creator',
                  'post_field']


class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(read_only=True, many=True)
    target = PostObjectRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'creator', 'description', 'created_at',
                  'modified_at', 'image', 'active', 'anonymous',
                  'target_id', 'target', 'comments']

    def create(self, validated_data):
        target_id = validated_data.get('target_id')
        post = Post(**validated_data)
        object = Course.objects.get(id=target_id)
        post.target = object
        post.save()
        return post