from django.contrib.auth import get_user_model
from rest_framework import serializers

from forum.models import Post, Comment
from .relations import PostObjectRelatedField, UserRelatedSerializer


class PostSerializer(serializers.ModelSerializer):

    target = PostObjectRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'creator', 'description', 'created_at',
                  'modified_at', 'image', 'active', 'anonymous',
                  'target_id', 'target']



class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = '__all__'
