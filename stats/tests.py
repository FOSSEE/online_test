# Python Imports
import json

# Django Imports
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse

# Local Imports
from stats.models import TrackLesson
from yaksh.models import Course, Lesson, LearningUnit, LearningModule


class TestTrackLesson(TestCase):
    def setUp(self):
        self.client = Client()
        self.mod_group, created = Group.objects.get_or_create(name='moderator')
        self.user_plaintext_pass = 'demo'
        self.user = User.objects.create_user(
            username='demo_user',
            password=self.user_plaintext_pass,
            first_name='first_name',
            last_name='last_name',
            email='demo@test.com',
        )

        # Create Student
        self.student_plaintext_pass = 'demo_student'
        self.student = User.objects.create_user(
            username='demo_student',
            password=self.student_plaintext_pass,
            first_name='student_first_name',
            last_name='student_last_name',
            email='demo_student@test.com'
        )

        # Add to moderator group
        self.mod_group.user_set.add(self.user)

        self.course = Course.objects.create(
            name="Test_course",
            enrollment="Open Enrollment", creator=self.user
        )
        self.lesson = Lesson.objects.create(
            name="Test_lesson", description="test description",
            creator=self.user)
        self.learning_unit = LearningUnit.objects.create(
            order=0, type="lesson", lesson=self.lesson
        )
        self.learning_module = LearningModule.objects.create(
            order=0, name="Test_module", description="Demo module",
            check_prerequisite=False, creator=self.user
            )
        self.learning_module.learning_unit.add(self.learning_unit.id)
        self.track = TrackLesson.objects.create(
            user_id=self.student.id, course_id=self.course.id,
            lesson_id=self.lesson.id
        )

    def tearDown(self):
        self.client.logout()
        self.mod_group.delete()
        self.user.delete()
        self.student.delete()
        self.course.delete()
        self.learning_unit.delete()
        self.learning_module.delete()

    def test_add_video_track(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # Student not enrolled in the course fails to add the tracking
        response = self.client.post(
            reverse('stats:add_tracker',
                    kwargs={"tracker_id": self.track.id}),
                data={'video_duration': '00:05:00'}
            )
        self.assertEqual(response.status_code, 404)

        self.course.students.add(self.student.id)
        # No current time given in the post data
        response = self.client.post(
            reverse('stats:add_tracker',
                    kwargs={"tracker_id": self.track.id}),
                data={'video_duration': '00:05:00'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json().get('success'))

        # Valid post data
        response = self.client.post(
            reverse('stats:add_tracker',
                    kwargs={"tracker_id": self.track.id}),
                data={'video_duration': '00:05:00',
                      'current_video_time': '00:01:00'}
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('success'))

    def test_disallow_student_view_tracking(self):
        self.client.login(
            username=self.student.username,
            password=self.student_plaintext_pass
        )

        # Fails to view the lesson data for student
        response = self.client.get(
            reverse('stats:view_lesson_watch_stats',
                    kwargs={"course_id": self.course.id,
                            "lesson_id": self.lesson.id})
                )
        self.assertEqual(response.status_code, 404)

    def test_allow_moderator_view_tracking(self):
        self.client.login(
            username=self.user.username,
            password=self.user_plaintext_pass
        )
        # Course creator can view the lesson data
        response = self.client.get(
            reverse('stats:view_lesson_watch_stats',
                    kwargs={"course_id": self.course.id,
                            "lesson_id": self.lesson.id})
                )
        response_data = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data.get('total'), 1)
        expected_tracker = list(TrackLesson.objects.filter(
            user_id=self.student.id, course_id=self.course.id,
            lesson_id=self.lesson.id))
        obtained_tracker = list(response_data.get(
            'objects').object_list)
        self.assertEqual(obtained_tracker, expected_tracker)

