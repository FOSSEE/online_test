from django.test import SimpleTestCase

from yaksh.models import AnswerPaper, QuestionPaper


class AnswerPaperUpdatePercentTestCase(SimpleTestCase):
    """AnswerPaper._update_percent must handle question paper with 0 marks"""

    def _make_paper(self, total_marks, marks_obtained):
        question_paper = QuestionPaper(total_marks=total_marks)
        ans_paper = AnswerPaper(question_paper=question_paper,
                                marks_obtained=marks_obtained)
        return ans_paper

    def test_zero_total_marks_set_percent_to_zero(self):
        # Given
        paper = self._make_paper(total_marks=0, marks_obtained=0)

        # When
        paper._update_percent()

        # Then
        self.assertEqual(paper.percent, 0)

    def test_percent_calculated_for_normal_paper(self):
        # Given
        paper = self._make_paper(total_marks=10, marks_obtained=5)

        # When
        paper._update_percent()

        # Then
        self.assertEqual(paper.percent, 50.0)

    def test_percent_rounded_to_two_places(self):
        # Given
        paper = self._make_paper(total_marks=3, marks_obtained=1)

        # When
        paper._update_percent()

        # Then
        self.assertEqual(paper.percent, 33.33)

    def test_percent_unchanged_marks_not_set(self):
        # Given
        paper = self._make_paper(total_marks=10, marks_obtained=None)
        paper.percent = None

        # When
        paper._update_percent()

        # Then
        self.assertIsNone(paper.percent)
