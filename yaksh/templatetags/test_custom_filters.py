import unittest
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import Group
import pytz

# local imports
from yaksh.models import (User, Profile, Question, Quiz, QuestionPaper,
                          AnswerPaper, Course, ArrangeTestCase, TestCaseOrder
                          )

from yaksh.templatetags.custom_filters import (completed, inprogress,
                                               get_ordered_testcases,
                                               get_answer_for_arrange_options,
                                               highlight_spaces
                                               )


def setUpModule():
    mod_group = Group.objects.create(name='moderator')

    # Create user profile
    teacher = User.objects.create_user(
      username='teacher2000', password='demo',
      email='teacher2000@test.com'
      )
    Profile.objects.create(user=teacher, roll_number=2000, institute='IIT',
                           department='Chemical', position='Teacher')
    # Create a course
    course = Course.objects.create(name="Python Course 2000",
                                   enrollment="Enroll Request",
                                   creator=teacher)
    # Create a quiz
    quiz = Quiz.objects.create(
      start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
      end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
      duration=30, active=True,
      attempts_allowed=1, time_between_attempts=0,
      description='demo quiz 2000',
      pass_criteria=0, instructions="Demo Instructions",
      creator=teacher
      )
    # Create a question paper
    question_paper = QuestionPaper.objects.create(quiz=quiz,
                                                  total_marks=1.0)
    # Create an answer paper
    AnswerPaper.objects.create(
        user=teacher, user_ip='101.0.0.1',
        start_time=timezone.now(),
        question_paper=question_paper,
        end_time=timezone.now()+timedelta(minutes=5),
        attempt_number=1,
        course=course
        )


def tearDownModule():
    User.objects.get(username="teacher2000").delete()
    Group.objects.all().delete()


class CustomFiltersTestCases(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.course = Course.objects.get(name="Python Course 2000")
        self.quiz = Quiz.objects.get(description="demo quiz 2000")
        self.question_paper = QuestionPaper.objects.get(quiz=self.quiz)
        self.user = User.objects.get(username='teacher2000')
        self.question1 = Question.objects.create(summary='int1', points=1,
                                                 type='code', user=self.user)
        self.question1.language = 'python'
        self.question1.type = "arrange"
        self.question1.description = "Arrange alphabets in ascending order"
        self.question1.test_case_type = 'arrangetestcase'
        self.question1.save()
        self.question_paper.fixed_questions.add(self.question1)
        self.question_paper.save()
        # Creating answerpaper

        self.answerpaper = AnswerPaper.objects.get(
            user=self.user, course=self.course,
            question_paper=self.question_paper
            )
        self.answerpaper.questions.add(self.question1)
        self.answerpaper.save()
        # For question
        self.arrange_testcase_1 = ArrangeTestCase(
            question=self.question1, options="A",
            type='arrangetestcase',
            )
        self.arrange_testcase_1.save()
        self.testcase_1_id = self.arrange_testcase_1.id
        self.arrange_testcase_2 = ArrangeTestCase(
            question=self.question1, options="B",
            type='arrangetestcase',
            )
        self.arrange_testcase_2.save()
        self.testcase_2_id = self.arrange_testcase_2.id
        self.arrange_testcase_3 = ArrangeTestCase(
            question=self.question1, options="C",
            type='arrangetestcase',
            )
        self.arrange_testcase_3.save()
        self.testcase_3_id = self.arrange_testcase_3.id

    @classmethod
    def tearDownClass(self):
        self.question1.delete()
        self.answerpaper.delete()

    def test_completed_inprogress(self):
        # Test in progress
        answerpaper = AnswerPaper.objects.filter(id=self.answerpaper.id)

        self.assertEqual(inprogress(answerpaper), 1)
        self.assertEqual(completed(answerpaper), 0)
        # Test completed
        self.answerpaper.status = 'completed'
        self.answerpaper.save()
        self.assertEqual(inprogress(answerpaper), 0)
        self.assertEqual(completed(answerpaper), 1)

    def test_get_answer_for_arrange_options(self):
        arrange_ans = [self.arrange_testcase_3,
                       self.arrange_testcase_2,
                       self.arrange_testcase_1,
                       ]
        arrange_ans_id = [tc.id for tc in arrange_ans]
        user_ans_order = get_answer_for_arrange_options(arrange_ans_id,
                                                        self.question1
                                                        )
        self.assertSequenceEqual(arrange_ans, user_ans_order)

    def test_get_ordered_testcases(self):
        new_answerpaper = self.question_paper.make_answerpaper(self.user,
                                                               "101.0.0.1", 2,
                                                               self.course.id
                                                               )
        tc_order = TestCaseOrder.objects.get(answer_paper=new_answerpaper,
                                             question=self.question1
                                             )
        testcases = [self.question1.get_test_case(id=ids)
                     for ids in tc_order.order.split(",")
                     ]

        ordered_testcases = get_ordered_testcases(self.question1,
                                                  new_answerpaper
                                                  )
        self.assertSequenceEqual(testcases, ordered_testcases)

        new_answerpaper.delete()

    def test_highlight_spaces(self):
        expected_output = "A "
        highlighted_output = highlight_spaces(expected_output)
        self.assertEqual(highlighted_output,
                         'A<span style="background-color:#ffb6db">&nbsp</span>'
                         )
