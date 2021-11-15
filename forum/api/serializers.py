from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from forum.models import Post, Comment
from yaksh.courses.models import Course, Lesson
from .relations import PostObjectRelatedField


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'is_superuser', 'username', 'first_name', 'last_name')

class CommentSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['creator'] = UserProfileSerializer(instance.creator).data
        return response

    class Meta:
        model = Comment
        fields = ['id', 'description', 'image', 'active', 'anonymous', 'creator',
                  'post_field', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(read_only=True, many=True)
    target = PostObjectRelatedField(read_only=True)
    image = serializers.ImageField(
        max_length=None, use_url=True, required=False,
    )
    comments_count = serializers.SerializerMethodField('get_comments_count')
    last_comment_by = serializers.SerializerMethodField('get_last_comment')

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['creator'] = UserProfileSerializer(instance.creator).data
        return response

    def get_last_comment(self, obj):
        if obj.comments.exists():
            return obj.get_last_comment().creator.username

    def get_comments_count(self, obj):
        if obj.comments.exists():
            return obj.get_comments_count()
        else:
            return 0

    class Meta:
        model = Post
        fields = ['id', 'title', 'creator', 'description', 'created_at',
                  'modified_at', 'image', 'active', 'anonymous', 'target_ct',
                  'target_id', 'target', 'comments', 'comments_count', 'last_comment_by']
