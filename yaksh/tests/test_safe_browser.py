from django.test import TestCase
from django.contrib.auth.models import User

from yaksh.models import Quiz
from yaksh.forms import SafeBrowserForm
from yaksh.forms import QuizForm


class SafeBrowserTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="teacher",
            password="test123"
        )

    def test_create_quiz_with_safe_browser(self):
        quiz = Quiz.objects.create(
            description="Safe Browser Quiz",
            creator=self.user
        )

        form = SafeBrowserForm(
            data={
                "enable_fullscreen": True,
                "enable_camera": True,
                "enable_microphone": True,
                "enable_right_click": True,
                "enable_tab_switch": True,
                "enable_screenshot_detection": True,
                "enable_multiple_face_detection": False,
                "max_violations": 3,
            },
            instance=quiz
        )

        self.assertTrue(form.is_valid())

        saved_quiz = form.save()

        self.assertTrue(saved_quiz.enable_fullscreen)
        self.assertTrue(saved_quiz.enable_camera)
        self.assertTrue(saved_quiz.enable_microphone)
        self.assertTrue(saved_quiz.enable_right_click)
        self.assertTrue(saved_quiz.enable_tab_switch)
        self.assertTrue(saved_quiz.enable_screenshot_detection)
        self.assertEqual(saved_quiz.max_violations, 3)
    def test_invalid_safe_browser_form_does_not_save(self):
        quiz = Quiz.objects.create(
            description="Safe Browser Quiz",
            creator=self.user
    )

        form = SafeBrowserForm(
            data={
                "max_violations": -1
            },
            instance=quiz
        )

        self.assertFalse(form.is_valid())
    def test_invalid_quiz_form_does_not_save(self):
        form = QuizForm(data={})

        self.assertFalse(form.is_valid())