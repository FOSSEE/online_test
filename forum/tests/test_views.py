from django.test import TestCase
from django.test import Client
from django.http import Http404
from django.utils import timezone
from django.urls import reverse, resolve
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType

from yaksh.models import Profile, Course
from forum.models import Post, Comment
from forum.forms import CommentForm
from forum.views import course_forum, post_comments


class TestPost(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

        self.student_plaintext_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # moderator
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
        )

    def test_csrf(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(url)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_view_course_forum_denies_anonymous_user(self):
        url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        redirection_url = '/exam/login/?next=/forum/course_forum/{0}/'.format(
            str(self.course.id)
            )
        self.assertRedirects(response, redirection_url)

    def test_view_course_forum(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(url, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/course_forum.html')

    def test_view_course_forum_not_found_status_code(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:course_forum', kwargs={
            'course_id': 99
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_course_forum_url_resolves_course_forum_view(self):
        view = resolve('/forum/course_forum/1/')
        self.assertEqual(view.func, course_forum)

    def test_course_forum_contains_link_to_post_comments_page(self):
        # create a post in setup
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        course_ct = ContentType.objects.get_for_model(self.course)
        post = Post.objects.create(
            title='post 1',
            description='post 1 description',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )
        response = self.client.get(url)
        post_comments_url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': post.uid
        })
        self.assertContains(response, 'href="{0}'.format(post_comments_url))

    def test_new_post_valid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        data = {
            "title": 'Post 1',
            "description": 'Post 1 description',
        }
        response = self.client.post(url, data)
        # This shouldn't be 302. Check where does it redirects.
        course_ct = ContentType.objects.get_for_model(self.course)
        result = Post.objects.filter(title='Post 1',
                                     creator=self.student,
                                     target_ct=course_ct,
                                     target_id=self.course.id)
        self.assertTrue(result.exists())

    def test_new_post_invalid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        data = {}
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)

    def test_new_post_invalid_post_data_empty_fields(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        data = {
            "title": '',
            "description": '',
        }
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)
        self.assertFalse(Post.objects.exists())

    def test_open_created_post_denies_anonymous_user(self):
        course_ct = ContentType.objects.get_for_model(self.course)
        post = Post.objects.create(
            title='post 1',
            description='post 1 description',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )
        url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': post.uid
        })
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        redirection_url = '/exam/login/?next=/forum/{0}/post/{1}/'.format(
                str(self.course.id), str(post.uid)
            )
        self.assertRedirects(response, redirection_url)

    def test_new_post_invalid_post_data(self):
        """
        Invalid post data should not redirect
        The expected behavior is to show form again with validation errors
        """
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        data = {}
        response = self.client.post(url, data)
        form = response.context.get('form')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(form.errors)

    def test_hide_post(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        self.course.students.add(self.user)
        course_ct = ContentType.objects.get_for_model(self.course)
        post = Post.objects.create(
            title='post 1',
            description='post 1 description',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )
        url = reverse('forum:hide_post', kwargs={
            'course_id': self.course.id,
            'uuid': post.uid
        })
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.course.delete()
        self.mod_group.delete()


class TestPostComment(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group = Group.objects.create(name='moderator')

        self.student_plaintext_pass = 'student'
        self.student = User.objects.create_user(
            username='student',
            password=self.student_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='student@test.com'
        )

        Profile.objects.create(
            user=self.student,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='student',
            timezone='UTC'
        )

        # moderator
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com'
        )

        Profile.objects.create(
            user=self.user,
            roll_number=10,
            institute='IIT',
            department='Chemical',
            position='Moderator',
            timezone='UTC'
        )

        self.course = Course.objects.create(
            name="Python Course",
            enrollment="Enroll Request", creator=self.user
        )

        course_ct = ContentType.objects.get_for_model(self.course)
        self.post = Post.objects.create(
            title='post 1',
            description='post 1 description',
            target_ct=course_ct, target_id=self.course.id,
            creator=self.student
        )

    def test_csrf(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        response = self.client.get(url)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_post_comments_view_success_status_code(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_post_comments_view_not_found_status_code(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:post_comments', kwargs={
            'course_id': 99,
            'uuid': '90da38ad-06fa-451b-9e82-5035e839da90'
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_post_comments_url_resolves_post_comments_view(self):
        view = resolve(
            '/forum/1/post/90da38ad-06fa-451b-9e82-5035e839da89/'
        )
        self.assertEquals(view.func, post_comments)

    def test_post_comments_view_contains_link_back_to_course_forum_view(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        comment_url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        course_forum_url = reverse('forum:course_forum', kwargs={
            'course_id': self.course.id
        })
        response = self.client.get(comment_url)
        self.assertContains(response, 'href="{0}"'.format(course_forum_url))

    def test_post_comments_valid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        data = {
            'post_field': self.post,
            'description': 'post 1 comment',
            'creator': self.user,
        }
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 302)
        result = Comment.objects.filter(post_field__uid=self.post.uid)
        self.assertTrue(result.exists())

    def test_post_comments_invalid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        data = {}
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)

    def test_post_comments_post_data_empty_fields(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        data = {
            'post_field': '',
            'description': '',
            'creator': '',
        }
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)
        self.assertFalse(Comment.objects.exists())

    def test_contains_form(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        response = self.client.get(url)
        form = response.context.get('form')
        self.assertIsInstance(form, CommentForm)

    def post_comment_invalid_post_data(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )
        self.course.students.add(self.student)
        url = reverse('forum:post_comments', kwargs={
            'course_id': self.course.id,
            'uuid': self.post.uid
        })
        data = {}
        response = self.client.post(url, data)
        form = response.context.get('form')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(form.errors)

    def test_hide_post_comment(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        self.course.students.add(self.user)
        comment = Comment.objects.create(
            post_field=self.post,
            description='post 1 comment',
            creator=self.user
        )
        url = reverse('forum:hide_comment', kwargs={
            'course_id': self.course.id,
            'uuid': comment.uid
        })
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.course.delete()
        self.mod_group.delete()
