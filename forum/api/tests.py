from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType

from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status


from yaksh.models import Course
from forum.models import Post, Comment


class TestPost(APITestCase):
    def setUp(self):
        self.mod_group = Group.objects.create(name='moderator')
        self.student_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_pass,
            first_name='Tony',
            last_name='Stark',
            email='tony@starkenterprises.com'
        )

        self.mod_user_pass = 'demo'
        self.mod_user = User.objects.create_user(
            username='mod_user',
            password=self.mod_user_pass,
            first_name='first_name',
            last_name='last_name',
            email='mod_user@test.com'
        )

        self.course = Course.objects.create(
            name='Python Course',
            enrollment='Enroll Request',
            creator=self.mod_user
        )

        course_ct = ContentType.objects.get_for_model(self.course)

        self.post = Post.objects.create(
            title="Post1",
            description="Post 1 description",
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )

    def test_view_course_forum_anonymously(self):
        url = reverse('forum_api:course_post_list', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(url)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_view_course_forum(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        url = reverse('forum_api:course_post_list', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_new_post_valid_post_data(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_list', kwargs={
            'course_id': self.course.id
        })
        data = {
            "title": "Post 1",
            "description": "Post 1 description",
            "creator": self.student.id,
            "target_id": self.course.id
        }
        response = self.client.post(url, data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_new_post_invalid_post_data(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_list', kwargs={
            'course_id': self.course.id
        })
        data = {
            "title": "Post 1",
            "description": "Post 1 description",
            "target_id": self.course.id
        }
        response = self.client.post(url, data)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_new_post_invalid_post_data_empty_fields(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_list', kwargs={
            'course_id': self.course.id
        })
        data = {
            "title": "",
            "description": "",
            "creator": "",
            "target_id": ""
        }
        response = self.client.post(url, data)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_hide_post(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_detail', kwargs={
            'course_id': self.course.id,
            'post_id': self.post.id
        })
        data = {
            "title": "Post1",
            "description": "Post 1 description",
            "target_id": self.course.id,
            "creator": self.student.id,
            "active": False
        }
        response = self.client.put(url, data)
        self.assertEqual(status.HTTP_200_OK, response.status_code)


    def tearDown(self):
        self.mod_user.delete()
        self.student.delete()
        self.course.delete()
        self.mod_group.delete()
        self.post.delete()


class TestPostComment(APITestCase):
    def setUp(self):
        self.mod_group = Group.objects.create(name='moderator')
        self.student_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_pass,
            first_name='Tony',
            last_name='Stark',
            email='tony@starkenterprises.com'
        )

        self.mod_user_pass = 'demo'
        self.mod_user = User.objects.create_user(
            username='mod_user',
            password=self.mod_user_pass,
            first_name='first_name',
            last_name='last_name',
            email='mod_user@test.com'
        )

        self.course = Course.objects.create(
            name='Python Course',
            enrollment='Enroll Request',
            creator=self.mod_user
        )

        course_ct = ContentType.objects.get_for_model(self.course)

        self.post = Post.objects.create(
            title="Post1",
            description="Post 1 description",
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )

        self.comment = Comment.objects.create(
            post_field=self.post,
            description='post 1 comment',
            creator=self.student
        )

    def test_post_comments_view_success_status_code(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_comments', kwargs={
            'course_id': self.course.id,
            'post_id': self.post.id
        })
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_post_comment_valid_post_data(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_comments', kwargs={
            'course_id': self.course.id,
            'post_id': self.post.id
        })
        data = {
            'post_field': self.post.id,
            'description': 'post 1 comment',
            'creator': self.student.id
        }
        response = self.client.post(url, data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_post_comment_invalid_post_data(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_comments', kwargs={
            'course_id': self.course.id,
            'post_id': self.post.id
        })
        data = {
            'post_field': self.post.id,
            'description': 'post 1 comment',
            'creator': ""
        }
        response = self.client.post(url, data)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_post_comments_post_data_empty_fields(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_comments', kwargs={
            'course_id': self.course.id,
            'post_id': self.post.id
        })
        data = {
            'post_field': "",
            'description': "",
            'creator': ""
        }
        response = self.client.post(url, data)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_hide_post_comment(self):
        self.client.login(username=self.student.username, password=self.student_pass)
        self.course.students.add(self.student)
        url = reverse('forum_api:course_post_comment_detail', kwargs={
            'course_id': self.course.id,
            'post_id': self.post.id,
            'comment_id': self.comment.id
        })
        data = {
            'post_field': self.post.id,
            'description': 'post 1 comment',
            'creator': self.student.id,
            'active': False
        }
        response = self.client.put(url, data)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def tearDown(self):
        self.mod_user.delete()
        self.student.delete()
        self.course.delete()
        self.mod_group.delete()
        self.post.delete()
