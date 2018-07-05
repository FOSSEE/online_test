from django.test import TestCase
from grades.models import GradingSystem


class GradingSystemTestCase(TestCase):
    def setUp(self):
        GradingSystem.objects.create(name='unusable')

    def test_get_grade(self):
        # Given
        grading_system = GradingSystem.objects.get(name='default')
        expected_grades = {0: 'F', 31: 'F', 49: 'P', 55: 'C', 60: 'B', 80: 'A',
                           95: 'A+', 100: 'A+', 100.5: 'A+', 101: None,
                           109: None}
        for marks in expected_grades.keys():
            # When
            grade = grading_system.get_grade(marks)
            # Then
            self.assertEqual(expected_grades.get(marks), grade)

    def test_grade_system_unusable(self):
        # Given
        # System with out ranges
        grading_system = GradingSystem.objects.get(name='unusable')
        # When
        grade = grading_system.get_grade(29)
        # Then
        self.assertIsNone(grade)
