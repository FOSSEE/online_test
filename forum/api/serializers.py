from django.contrib.auth import get_user_model
from rest_framework import serializers

from forum.models import Post, Comment
from .relations import PostObjectRelatedField


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['is_superuser', 'username', 'first_name', 'last_name',
                  'is_staff', 'is_active']


class CommentSerializer(serializers.ModelSerializer):
    creator = UserSerializer()
    class Meta:
        model = Comment
        fields = ['id', 'creator', 'description', 'created_at', 'modified_at',
                  'image', 'active', 'anonymous', 'post_field']


class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True)
    creator = UserSerializer()
    target = PostObjectRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'creator', 'description', 'created_at',
                  'modified_at', 'image', 'active', 'anonymous', 'target_ct',
                  'target_id', 'target', 'comments']
