from django.test import TestCase
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from yaksh.models import User, Profile, Course
from forum.models import Post, Comment


class PostModelTestCases(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            username='bart',
            password='bart',
            email='bart@test.com'
        )
        Profile.objects.create(
            user=self.user1,
            roll_number=1,
            institute='IIT',
            department='Chemical',
            position='Student'
        )

        self.user2 = User.objects.create(
            username='dart',
            password='dart',
            email='dart@test.com'
        )
        Profile.objects.create(
            user=self.user2,
            roll_number=2,
            institute='IIT',
            department='Chemical',
            position='Student'
        )

        self.user3 = User.objects.create(
            username='user3',
            password='user3',
            email='user3@test.com'
        )
        Profile.objects.create(
            user=self.user3,
            roll_number=3,
            is_moderator=True,
            department='Chemical',
            position='Teacher'
        )

        self.course = Course.objects.create(
            name='Python Course',
            enrollment='Enroll Request',
            creator=self.user3
        )
        course_ct = ContentType.objects.get_for_model(self.course)
        self.post1 = Post.objects.create(
            title='Post 1',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.user1,
            description='Post 1 description'
        )
        self.comment1 = Comment.objects.create(
            post_field=self.post1,
            creator=self.user2,
            description='Post 1 comment 1'
        )
        self.comment2 = Comment.objects.create(
            post_field=self.post1,
            creator=self.user3,
            description='Post 1 user3 comment 2'
        )

    def test_get_last_comment(self):
        last_comment = self.post1.get_last_comment()
        self.assertEquals(last_comment.description, 'Post 1 user3 comment 2')

    def test_get_comments_count(self):
        count = self.post1.get_comments_count()
        self.assertEquals(count, 2)

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.course.delete()
        self.post1.delete()
