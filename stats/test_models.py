from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from stats.models import TrackLesson, LessonLog
from yaksh.models import Course, Lesson, LearningModule, LearningUnit


class TrackLessonTestCase(TestCase):
    def setUp(self):
        creator = User.objects.create(username='creator', password='test',
                                      email='test1@test.com')
        self.student = User.objects.create(username='student', password='test',
                                           email='test2@test.com')
        self.course = Course.objects.create(
            name="Test Course", enrollment="Enroll Request", creator=creator
        )
        learning_module = LearningModule.objects.create(
            name='LM', description='module', creator=creator
        )
        self.lesson = Lesson.objects.create(
            name='Lesson', description='Video Lesson', creator=creator
        )
        learning_unit = LearningUnit.objects.create(order=1, type='lesson',
                                                    lesson=self.lesson)
        learning_module.learning_unit.add(learning_unit)
        learning_module.save()
        self.course.learning_module.add(learning_module)
        self.course.students.add(self.student)
        self.course.save()
        self.tracker = TrackLesson.objects.create(user=self.student,
                                                  course=self.course,
                                                  lesson=self.lesson)
        LessonLog.objects.create(track=self.tracker)
        self.last_access_time = timezone.now()
        LessonLog.objects.create(track=self.tracker,
                                 last_access_time=self.last_access_time)

    def tearDown(self):
        User.objects.all().delete()
        Course.objects.all().delete()
        Lesson.objects.all().delete()
        LearningUnit.objects.all().delete()
        LearningModule.objects.all().delete()
        LessonLog.objects.all().delete()
        TrackLesson.objects.all().delete()

    def test_track_lesson(self):
        # Given
        tracker = self.tracker

        # Then
        self.assertEqual(tracker.user, self.student)
        self.assertEqual(tracker.course, self.course)
        self.assertEqual(tracker.lesson, self.lesson)
        self.assertEqual(tracker.current_time, '00:00:00')
        self.assertEqual(tracker.video_duration, '00:00:00')
        self.assertFalse(tracker.watched)

    def test_log_counter(self):
        # Given
        tracker = self.tracker
        expected_count = 2

        # When
        counts = tracker.get_log_counter()

        # Then
        self.assertEqual(counts, expected_count)

    def test_get_current_time(self):
        # Given
        tracker = self.tracker
        expected_time = '00:00:00'

        # When
        current_time = tracker.get_current_time()

        # Then
        self.assertEqual(current_time, expected_time)

    def test_get_video_duration(self):
        # Given
        tracker = self.tracker
        expected_duration = '00:00:00'

        # When
        duration = tracker.get_video_duration()

        # Then
        self.assertEqual(duration, expected_duration)

    def test_set_current_time(self):
        # Given
        tracker = self.tracker
        ctime = timezone.now()

        # When
        tracker.set_current_time(ctime.strftime('%H:%M:%S'))
        tracker.save()
        updated_time = tracker.get_current_time()

        # Then
        self.assertEqual(updated_time, ctime.strftime('%H:%M:%S'))

        # Given
        time_now = timezone.now()
        invalid_ctime = ctime - timezone.timedelta(seconds=100)

        # When
        tracker.set_current_time(invalid_ctime.strftime('%H:%M:%S'))
        tracker.save()
        old_time = tracker.get_current_time()

        # Then
        self.assertEqual(old_time, ctime.strftime('%H:%M:%S'))

    def test_get_percentage_complete(self):
        # Given
        tracker = self.tracker
        expected_percentage = 0

        # When
        percentage = tracker.get_percentage_complete()

        # Then
        self.assertEqual(percentage, expected_percentage)

        # Given
        expected_percentage = 75

        # When
        tracker.set_current_time('00:03:00')
        tracker.video_duration = '00:04:00'
        tracker.save()
        percentage = tracker.get_percentage_complete()

        # Then
        self.assertEqual(percentage, expected_percentage)

    def test_get_last_access_time(self):
        # Given
        tracker = self.tracker
        expected_time = self.last_access_time

        # When
        time = tracker.get_last_access_time()

        # Then
        self.assertEqual(time, expected_time)

    def test_set_get_watched(self):
        # Given
        tracker = self.tracker

        # When
        tracker.set_watched()

        # Then
        self.assertFalse(tracker.get_watched())

        # Given
        tracker = self.tracker

        # When
        tracker.set_current_time('00:03:55')
        tracker.video_duration = '00:04:00'
        tracker.save()
        tracker.set_watched()

        # Then
        self.assertTrue(tracker.get_watched())

    def test_time_spent(self):
        # Given
        tracker = self.tracker
        expected_time = '00:02:00'

        # When
        tracker.video_duration = '00:04:00'
        tracker.save()
        time = tracker.time_spent()

        # Then
        self.assertTrue(expected_time, time)
