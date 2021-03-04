import unittest
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import Group
from textwrap import dedent
import pytz
from yaksh.models import User, Profile, Question, Quiz, QuestionPaper,\
    AnswerPaper, Answer, Course, IntegerTestCase, FloatTestCase,\
    StringTestCase, McqTestCase, ArrangeTestCase



def setUpModule():
    mod_group = Group.objects.create(name='moderator')
    # Create user profile
    # Create User 1
    user = User.objects.create_user(username='demo_user_100',
                                    password='demo',
                                    email='demo@test.com')

    Profile.objects.create(user=user, roll_number=1,
                           institute='IIT', department='Aerospace',
                           position='Student')
    # Create User 2
    user2 = User.objects.create_user(
      username='demo_user_101', password='demo',
      email='demo@test.com')

    Profile.objects.create(user=user2, roll_number=2,
                           institute='IIT', department='Aerospace',
                           position='Student')

    # Create a course
    Course.objects.create(name="Python Course 100",
                          enrollment="Enroll Request", creator=user)

    quiz = Quiz.objects.create(
        start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
        end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
        duration=30, active=True, attempts_allowed=1,
        time_between_attempts=0, pass_criteria=0,
        description='demo quiz 100',
        instructions="Demo Instructions",
        creator=user
        )
    QuestionPaper.objects.create(quiz=quiz, total_marks=1.0)


def tearDownModule():
    User.objects.filter(username__in=["demo_user_100", "demo_user_101"])\
                 .delete()
    Group.objects.all().delete()


class IntegerQuestionTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Creating Course
        self.course = Course.objects.get(name="Python Course 100")
        # Creating Quiz
        self.quiz = Quiz.objects.get(description="demo quiz 100")
        # Creating Question paper
        self.question_paper = QuestionPaper.objects.get(quiz=self.quiz)

        # Creating User
        self.user = User.objects.get(username='demo_user_100')

        # Creating Question
        self.question1 = Question.objects.create(summary='int1', points=1,
                                                 type='code', user=self.user)
        self.question1.language = 'python'
        self.question1.type = "integer"
        self.question1.test_case_type = 'integertestcase'
        self.question1.description = 'sum of 12+13?'
        self.question1.save()

        # Creating answerpaper

        self.answerpaper = AnswerPaper.objects.create(
            user=self.user, user_ip='101.0.0.1', start_time=timezone.now(),
            question_paper=self.question_paper, course=self.course,
            end_time=timezone.now()+timedelta(minutes=5), attempt_number=1
            )
        self.answerpaper.questions.add(self.question1)
        self.answerpaper.save()
        # For question
        self.integer_based_testcase = IntegerTestCase(question=self.question1,
                                                      correct=25,
                                                      type='integertestcase',
                                                      )
        self.integer_based_testcase.save()

    @classmethod
    def tearDownClass(self):
        self.question1.delete()
        self.answerpaper.delete()

    def test_validate_regrade_integer_correct_answer(self):
        # Given
        integer_answer = 25
        self.answer = Answer(question=self.question1,
                             answer=integer_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)
        self.answerpaper.save()
        # When
        json_data = None
        result = self.answerpaper.validate_answer(integer_answer,
                                                  self.question1,
                                                  json_data,
                                                  )
        # Then
        self.assertTrue(result['success'])

        # Regrade
        # Given
        regrade_answer = Answer.objects.get(id=self.answer.id)
        regrade_answer.answer = 200
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id)

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question1
                                                      ).last()
        self.assertEqual(self.answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_validate_regrade_integer_incorrect_answer(self):
        # Given
        integer_answer = 26
        self.answer = Answer(question=self.question1,
                             answer=integer_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(integer_answer,
                                                  self.question1, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])

        # Regrade
        # Given
        regrade_answer = Answer.objects.get(id=self.answer.id)
        regrade_answer.answer = 25
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id)

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question1
                                                      ).last()
        self.assertEqual(self.answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 1)
        self.assertTrue(self.answer.correct)


class StringQuestionTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Creating Course
        self.course = Course.objects.get(name="Python Course 100")
        # Creating Quiz
        self.quiz = Quiz.objects.get(description="demo quiz 100")
        # Creating Question paper
        self.question_paper = QuestionPaper.objects.get(quiz=self.quiz)
        # Creating User
        self.user = User.objects.get(username='demo_user_100')
        # Creating Question
        self.question1 = Question.objects.create(summary='str1', points=1,
                                                 type='code', user=self.user)
        self.question1.language = 'python'
        self.question1.type = "string"
        self.question1.test_case_type = 'stringtestcase'
        self.question1.description = 'Write Hello, EARTH!'
        self.question1.save()

        self.question2 = Question.objects.create(summary='str2', points=1,
                                                 type='code', user=self.user)
        self.question2.language = 'python'
        self.question2.type = "string"
        self.question2.test_case_type = 'stringtestcase'
        self.question2.description = 'Write Hello, EARTH!'
        self.question2.save()

        # Creating answerpaper

        self.answerpaper = AnswerPaper.objects.create(
            user=self.user, user_ip='101.0.0.1', start_time=timezone.now(),
            question_paper=self.question_paper, course=self.course,
            end_time=timezone.now()+timedelta(minutes=5), attempt_number=1
            )
        self.answerpaper.questions.add(*[self.question1, self.question2])
        self.answerpaper.save()

        # For question
        self.lower_string_testcase = StringTestCase(question=self.question1,
                                                    correct="Hello, EARTH!",
                                                    string_check="lower",
                                                    type='stringtestcase',
                                                    )
        self.lower_string_testcase.save()

        self.exact_string_testcase = StringTestCase(question=self.question2,
                                                    correct="Hello, EARTH!",
                                                    string_check="exact",
                                                    type='stringtestcase',
                                                    )
        self.exact_string_testcase.save()

    @classmethod
    def tearDownClass(self):
        self.question1.delete()
        self.question2.delete()
        self.answerpaper.delete()

    def test_validate_regrade_case_insensitive_string_correct_answer(self):
        # Given
        string_answer = "hello, earth!"
        answer = Answer(question=self.question1, answer=string_answer)
        answer.save()
        self.answerpaper.answers.add(answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(string_answer,
                                                  self.question1, json_data
                                                  )
        # Then
        self.assertTrue(result['success'])

        # Regrade
        # Given
        regrade_answer = Answer.objects.get(id=answer.id)
        regrade_answer.answer = "hello, mars!"
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id)

        # Then
        answer = self.answerpaper.answers.filter(
            question=self.question1).last()
        self.assertEqual(answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(answer.marks, 0)
        self.assertFalse(answer.correct)

    def test_validate_regrade_case_insensitive_string_incorrect_answer(self):
        # Given
        string_answer = "hello, mars!"
        answer = Answer(question=self.question1, answer=string_answer)
        answer.save()
        self.answerpaper.answers.add(answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(string_answer,
                                                  self.question1, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])

        # Regrade
        # Given
        regrade_answer = Answer.objects.get(id=answer.id)
        regrade_answer.answer = "hello, earth!"
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id)

        # Then
        answer = self.answerpaper.answers.filter(
            question=self.question1).last()
        self.assertEqual(answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(answer.marks, 1)
        self.assertTrue(answer.correct)

    def test_validate_regrade_case_sensitive_string_correct_answer(self):
        # Given
        string_answer = "Hello, EARTH!"
        answer = Answer(question=self.question2, answer=string_answer)
        answer.save()
        self.answerpaper.answers.add(answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(string_answer,
                                                  self.question2, json_data
                                                  )
        # Then
        self.assertTrue(result['success'])

        # Regrade
        # Given
        regrade_answer = Answer.objects.get(id=answer.id)
        regrade_answer.answer = "hello, earth!"
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question2.id)

        # Then
        answer = self.answerpaper.answers.filter(
            question=self.question2).last()
        self.assertEqual(answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(answer.marks, 0)
        self.assertFalse(answer.correct)

    def test_case_sensitive_string_incorrect_answer(self):
        # Given
        string_answer = "hello, earth!"
        answer = Answer(question=self.question2, answer=string_answer)
        answer.save()
        self.answerpaper.answers.add(answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(string_answer,
                                                  self.question2, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])

        # Regrade
        # Given
        regrade_answer = Answer.objects.get(id=answer.id)
        regrade_answer.answer = "Hello, EARTH!"
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question2.id)

        # Then
        answer = self.answerpaper.answers.filter(
            question=self.question2).last()
        self.assertEqual(answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(answer.marks, 1)
        self.assertTrue(answer.correct)


class FloatQuestionTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Creating Course
        self.course = Course.objects.get(name="Python Course 100")
        # Creating Quiz
        self.quiz = Quiz.objects.get(description="demo quiz 100")
        # Creating Question paper
        self.question_paper = QuestionPaper.objects.get(quiz=self.quiz)

        # Creating User
        self.user = User.objects.get(username='demo_user_100')
        # Creating Question
        self.question1 = Question.objects.create(summary='flt1', points=1,
                                                 type='code', user=self.user)
        self.question1.language = 'python'
        self.question1.type = "float"
        self.question1.test_case_type = 'floattestcase'
        self.question1.save()

        # Creating answerpaper

        self.answerpaper = AnswerPaper.objects.create(
            user=self.user, user_ip='101.0.0.1', start_time=timezone.now(),
            question_paper=self.question_paper, course=self.course,
            end_time=timezone.now()+timedelta(minutes=5), attempt_number=1,
            )

        self.answerpaper.questions.add(self.question1)
        self.answerpaper.save()
        # For question
        self.float_based_testcase = FloatTestCase(question=self.question1,
                                                  correct=100,
                                                  error_margin=0.1,
                                                  type='floattestcase',
                                                  )
        self.float_based_testcase.save()

    @classmethod
    def tearDownClass(self):
        self.question1.delete()
        self.answerpaper.delete()

    def test_validate_regrade_float_correct_answer(self):
        # Given
        float_answer = 99.9
        self.answer = Answer(question=self.question1,
                             answer=float_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(float_answer,
                                                  self.question1,
                                                  json_data,
                                                  )
        # Then
        self.assertTrue(result['success'])

        # Regrade with wrong answer
        # Given
        regrade_answer = Answer.objects.get(id=self.answer.id)
        regrade_answer.answer = 0.0
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id)

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question1
                                                      ).last()
        self.assertEqual(self.answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_float_incorrect_answer(self):
        # Given
        float_answer = 99.8
        self.answer = Answer(question=self.question1,
                             answer=float_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(float_answer,
                                                  self.question1, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])

        # Regrade
        # Given
        regrade_answer = Answer.objects.get(id=self.answer.id)
        regrade_answer.answer = 99.9
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id)

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question1
                                                      ).last()
        self.assertEqual(self.answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 1)
        self.assertTrue(self.answer.correct)


class MCQQuestionTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Creating User
        self.user = User.objects.get(username='demo_user_100')
        self.user2 = User.objects.get(username='demo_user_101')
        self.user_ip = '127.0.0.1'

        # Creating Course
        self.course = Course.objects.get(name="Python Course 100")
        # Creating Quiz
        self.quiz = Quiz.objects.get(description="demo quiz 100")
        # Creating Question paper
        self.question_paper = QuestionPaper.objects.get(quiz=self.quiz)
        self.question_paper.shuffle_testcases = True
        self.question_paper.save()
        # Creating Question
        self.question1 = Question.objects.create(summary='mcq1', points=1,
                                                 type='code', user=self.user,
                                                 )
        self.question1.language = 'python'
        self.question1.type = "mcq"
        self.question1.test_case_type = 'Mcqtestcase'
        self.question1.description = 'Which option is Correct?'
        self.question1.save()

        # For questions
        self.mcq_based_testcase_1 = McqTestCase(question=self.question1,
                                                options="Correct",
                                                correct=True,
                                                type='mcqtestcase',
                                                )
        self.mcq_based_testcase_1.save()

        self.mcq_based_testcase_2 = McqTestCase(question=self.question1,
                                                options="Incorrect",
                                                correct=False,
                                                type='mcqtestcase',
                                                )
        self.mcq_based_testcase_2.save()

        self.mcq_based_testcase_3 = McqTestCase(question=self.question1,
                                                options="Incorrect",
                                                correct=False,
                                                type='mcqtestcase',
                                                )
        self.mcq_based_testcase_3.save()

        self.mcq_based_testcase_4 = McqTestCase(question=self.question1,
                                                options="Incorrect",
                                                correct=False,
                                                type='mcqtestcase',
                                                )
        self.mcq_based_testcase_4.save()

        self.question_paper.fixed_questions.add(self.question1)

        self.answerpaper = self.question_paper.make_answerpaper(
                                           user=self.user, ip=self.user_ip,
                                           attempt_num=1,
                                           course_id=self.course.id
                                           )

        # Answerpaper for user 2
        self.answerpaper2 = self.question_paper.make_answerpaper(
                                            user=self.user2, ip=self.user_ip,
                                            attempt_num=1,
                                            course_id=self.course.id
                                            )

    @classmethod
    def tearDownClass(self):
        self.question1.delete()
        self.answerpaper.delete()
        self.answerpaper2.delete()

    def test_shuffle_test_cases(self):
        # Given
        # When

        user_testcase = self.question1.get_ordered_test_cases(
                                        self.answerpaper
                                        )
        order1 = [tc.id for tc in user_testcase]
        user2_testcase = self.question1.get_ordered_test_cases(
                                        self.answerpaper2
                                        )
        order2 = [tc.id for tc in user2_testcase]
        self.question_paper.shuffle_testcases = False
        self.question_paper.save()
        answerpaper3 = self.question_paper.make_answerpaper(
                              user=self.user2, ip=self.user_ip,
                              attempt_num=self.answerpaper.attempt_number+1,
                              course_id=self.course.id
                              )
        not_ordered_testcase = self.question1.get_ordered_test_cases(
                                              answerpaper3
                                              )
        get_test_cases = self.question1.get_test_cases()
        # Then
        self.assertNotEqual(order1, order2)
        self.assertEqual(get_test_cases, not_ordered_testcase)


class ArrangeQuestionTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Creating Course
        self.course = Course.objects.get(name="Python Course 100")
        # Creating Quiz
        self.quiz = Quiz.objects.get(description="demo quiz 100")
        # Creating Question paper
        self.question_paper = QuestionPaper.objects.get(quiz=self.quiz,
                                                        total_marks=1.0)

        # Creating User
        self.user = User.objects.get(username='demo_user_100')
        # Creating Question
        self.question1 = Question.objects.create(summary='arrange1',
                                                 points=1.0,
                                                 user=self.user
                                                 )
        self.question1.language = 'python'
        self.question1.type = "arrange"
        self.question1.description = "Arrange alphabets in ascending order"
        self.question1.test_case_type = 'arrangetestcase'
        self.question1.save()

        # Creating answerpaper

        self.answerpaper = AnswerPaper.objects.create(
            user=self.user, user_ip='101.0.0.1', course=self.course,
            start_time=timezone.now(), question_paper=self.question_paper,
            end_time=timezone.now()+timedelta(minutes=5), attempt_number=1
            )
        self.answerpaper.questions.add(self.question1)
        self.answerpaper.save()
        # For question
        self.arrange_testcase_1 = ArrangeTestCase(question=self.question1,
                                                  options="A",
                                                  type='arrangetestcase',
                                                  )
        self.arrange_testcase_1.save()
        self.testcase_1_id = self.arrange_testcase_1.id
        self.arrange_testcase_2 = ArrangeTestCase(question=self.question1,
                                                  options="B",
                                                  type='arrangetestcase',
                                                  )
        self.arrange_testcase_2.save()
        self.testcase_2_id = self.arrange_testcase_2.id
        self.arrange_testcase_3 = ArrangeTestCase(question=self.question1,
                                                  options="C",
                                                  type='arrangetestcase',
                                                  )
        self.arrange_testcase_3.save()
        self.testcase_3_id = self.arrange_testcase_3.id

    @classmethod
    def tearDownClass(self):
        self.question1.delete()
        self.answerpaper.delete()

    def test_validate_regrade_arrange_correct_answer(self):
        # Given
        arrange_answer = [self.testcase_1_id,
                          self.testcase_2_id,
                          self.testcase_3_id,
                          ]
        self.answer = Answer(question=self.question1,
                             answer=arrange_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(arrange_answer,
                                                  self.question1,
                                                  json_data,
                                                  )
        # Then
        self.assertTrue(result['success'])

        # Regrade with wrong answer
        # Given
        regrade_answer = Answer.objects.get(id=self.answer.id)

        # Try regrade with wrong data structure
        # When
        regrade_answer.answer = 1
        regrade_answer.save()
        details = self.answerpaper.regrade(self.question1.id)
        self.assertFalse(details[0])
        self.assertIn("arrange answer not a list", details[1])

        # Try regrade with incorrect answer
        # When
        regrade_answer.answer = [self.testcase_1_id,
                                 self.testcase_3_id,
                                 self.testcase_2_id,
                                 ]
        regrade_answer.save()
        # Then
        details = self.answerpaper.regrade(self.question1.id)
        self.answer = self.answerpaper.answers.filter(question=self.question1
                                                      ).last()
        self.assertEqual(self.answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_validate_regrade_arrange_incorrect_answer(self):
        # Given
        arrange_answer = [self.testcase_1_id,
                          self.testcase_3_id,
                          self.testcase_2_id,
                          ]
        self.answer = Answer(question=self.question1,
                             answer=arrange_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(arrange_answer,
                                                  self.question1, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])
        # Regrade with wrong answer
        # Given
        regrade_answer = Answer.objects.get(id=self.answer.id)
        regrade_answer.answer = [self.testcase_1_id,
                                 self.testcase_2_id,
                                 self.testcase_3_id,
                                 ]
        regrade_answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id)

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question1
                                                      ).last()
        self.assertEqual(self.answer, regrade_answer)
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 1)
        self.assertTrue(self.answer.correct)


class MCQShuffleTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Creating User
        self.user = User.objects.get(username='demo_user_100')
        self.user2 = User.objects.get(username='demo_user_101')
        self.user_ip = '127.0.0.1'

        # Creating Course
        self.course = Course.objects.get(name="Python Course 100")
        # Creating Quiz
        self.quiz = Quiz.objects.get(description="demo quiz 100")
        # Creating Question paper
        self.question_paper = QuestionPaper.objects.get(quiz=self.quiz)
        self.question_paper.shuffle_testcases = True
        self.question_paper.save()
        # Creating Question
        self.question1 = Question.objects.create(summary='mcq1', points=1,
                                                 type='code', user=self.user,
                                                 )
        self.question1.language = 'python'
        self.question1.type = "mcq"
        self.question1.test_case_type = 'Mcqtestcase'
        self.question1.description = 'Which option is Correct?'
        self.question1.save()

        # For questions
        self.mcq_based_testcase_1 = McqTestCase(question=self.question1,
                                                options="Correct",
                                                correct=True,
                                                type='mcqtestcase',
                                                )
        self.mcq_based_testcase_1.save()

        self.mcq_based_testcase_2 = McqTestCase(question=self.question1,
                                                options="Incorrect",
                                                correct=False,
                                                type='mcqtestcase',
                                                )
        self.mcq_based_testcase_2.save()

        self.mcq_based_testcase_3 = McqTestCase(question=self.question1,
                                                options="Incorrect",
                                                correct=False,
                                                type='mcqtestcase',
                                                )
        self.mcq_based_testcase_3.save()

        self.mcq_based_testcase_4 = McqTestCase(question=self.question1,
                                                options="Incorrect",
                                                correct=False,
                                                type='mcqtestcase',
                                                )
        self.mcq_based_testcase_4.save()

        self.question_paper.fixed_questions.add(self.question1)

        self.answerpaper = self.question_paper.make_answerpaper(
                                           user=self.user, ip=self.user_ip,
                                           attempt_num=1,
                                           course_id=self.course.id
                                           )

        # Answerpaper for user 2
        self.answerpaper2 = self.question_paper.make_answerpaper(
                                            user=self.user2, ip=self.user_ip,
                                            attempt_num=1,
                                            course_id=self.course.id
                                            )

    @classmethod
    def tearDownClass(self):
        self.question1.delete()
        self.answerpaper.delete()
        self.answerpaper2.delete()

    def test_shuffle_test_cases(self):
        # Given
        # When

        user_testcase = self.question1.get_ordered_test_cases(
                                        self.answerpaper
                                        )
        order1 = [tc.id for tc in user_testcase]
        user2_testcase = self.question1.get_ordered_test_cases(
                                        self.answerpaper2
                                        )
        order2 = [tc.id for tc in user2_testcase]
        self.question_paper.shuffle_testcases = False
        self.question_paper.save()
        answerpaper3 = self.question_paper.make_answerpaper(
                              user=self.user2, ip=self.user_ip,
                              attempt_num=self.answerpaper.attempt_number+1,
                              course_id=self.course.id
                              )
        not_ordered_testcase = self.question1.get_ordered_test_cases(
                                              answerpaper3
                                              )
        get_test_cases = self.question1.get_test_cases()
        # Then
        self.assertNotEqual(order1, order2)
        self.assertEqual(get_test_cases, not_ordered_testcase)
        answerpaper3.delete()
