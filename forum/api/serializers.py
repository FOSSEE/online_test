from django.contrib.auth import get_user_model
from rest_framework import serializers

from forum.models import Post, Comment
from .relations import PostObjectRelatedField, UserRelatedSerializer


class CommentSerializer(serializers.ModelSerializer):
    creator = UserRelatedSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'creator', 'description', 'created_at', 'modified_at',
                  'image', 'active', 'anonymous', 'post_field']


class PostSerializer(serializers.ModelSerializer):
    creator = UserRelatedSerializer(read_only=True)
    target = PostObjectRelatedField(read_only=True)
    comments = CommentSerializer(many=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'creator', 'description', 'created_at',
                  'modified_at', 'image', 'active', 'anonymous', 'target_ct',
                  'target_id', 'target', 'comments']
