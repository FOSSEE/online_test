import unittest
import os
from yaksh_api import QuestionResource, QuestionPaperResource, QuizResource, AnswerResource

class McqEvaluationTest(unittest.TestCase):
    def setUp(self):
        # Create a Question
        ########################
        summary = "test-summary"
        description = "test-description"
        points = 1
        test = "abc"
        options = ["abc", "zxc", "qwe", "nbv"]
        language = "python" # Currently supports python, c, cpp, scilab, java, bash
        active = True # True/False
        _type = "mcq"

        qt = QuestionResource()
        self.question = qt.create(summary, description, points, test,
                 options, language, active, _type)

        # Create a Quiz
        ###########################
        duration = 10
        description = "test-quiz"
        pass_criteria = 40
        language = "python"
        attempts_allowed = -1
        time_between_attempts = 0

        qz = QuizResource()
        self.quiz = qz.create(duration, description, pass_criteria, language,
                 attempts_allowed, time_between_attempts)

        # Create a QuestionPaper
        ##############################
        quiz_id = 1
        fixed_question_id = [1,2]
        total_marks = 3.0

        qp = QuestionPaperResource()
        self.question_paper = qp.create(quiz_id, fixed_question_id, total_marks)

        # Create an Answer
        ##############################
        answer = "abc"
        question_id = 1

        self.answer_object = AnswerResource()
        self.answer = self.answer_object.create(answer, question_id)

    def test_evaluate_answer(self):
        question_id = 1
        answer_id = 1
        self.answer_object.evaluate_answer(question_id, answer_id)
