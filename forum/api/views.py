from django.contrib.contenttypes.models import ContentType

from rest_framework.decorators import api_view
from rest_framework.response import Response

from forum.models import Post
from yaksh.models import Course, Lesson
from .serializers import PostSerializer


@api_view(['GET'])
def post_list(request, course_id):
    if request.method == 'GET':
        course = Course.objects.get(id=course_id)
        course_ct = ContentType.objects.get_for_model(course)
        posts = Post.objects.filter(target_ct=course_ct, target_id=course.id, active=True)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

