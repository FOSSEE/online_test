from django.utils import unittest
from exam.models import User, Profile, Question, Quiz, QuestionPaper,\
    QuestionSet, AnswerPaper, Answer
import datetime


def setUpModule():
    # create user profile
    user = User.objects.create_user(username='demo_user',
                                    password='demo',
                                    email='demo@test.com')
    User.objects.create_user(username='demo_user2',
                             password='demo',
                             email='demo@test.com')
    Profile.objects.create(user=user, roll_number=1, institute='IIT',
                           department='Chemical', position='Student')

    # create 20 questions
    for i in range(1, 21):
        Question.objects.create(summary='Q%d' % (i), points=1)

    # create a quiz
    Quiz.objects.create(start_date='2014-06-16', duration=30, active=False,
                        description='demo quiz')


def tearDownModule():
    User.objects.all().delete()
    Question.objects.all().delete()
    Quiz.objects.all().delete()


###############################################################################
class ProfileTestCases(unittest.TestCase):
    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.profile = Profile.objects.get(pk=1)

    def test_user_profile(self):
        """ Test user profile"""
        self.assertEqual(self.user.username, 'demo_user')
        self.assertEqual(self.profile.user.username, 'demo_user')
        self.assertEqual(int(self.profile.roll_number), 1)
        self.assertEqual(self.profile.institute, 'IIT')
        self.assertEqual(self.profile.department, 'Chemical')
        self.assertEqual(self.profile.position, 'Student')


###############################################################################
class QuestionTestCases(unittest.TestCase):
    def setUp(self):
        # Single question details
        self.question = Question(summary='Demo question', language='Python',
                                 type='Code', active=True,
                                 description='Write a function', points=1.0,
                                 test='Test Cases', snippet='def myfunc()')
        self.question.save()
        self.question.tags.add('python', 'function')

    def test_question(self):
        """ Test question """
        self.assertEqual(self.question.summary, 'Demo question')
        self.assertEqual(self.question.language, 'Python')
        self.assertEqual(self.question.type, 'Code')
        self.assertFalse(self.question.options)
        self.assertEqual(self.question.description, 'Write a function')
        self.assertEqual(self.question.points, 1.0)
        self.assertTrue(self.question.active)
        self.assertEqual(self.question.test, 'Test Cases')
        self.assertEqual(self.question.snippet, 'def myfunc()')
        tag_list = []
        for tag in self.question.tags.all():
                    tag_list.append(tag.name)
        self.assertEqual(tag_list, ['python', 'function'])


###############################################################################
class QuizTestCases(unittest.TestCase):
    def setUp(self):
        self.quiz = Quiz.objects.get(pk=1)

    def test_quiz(self):
        """ Test Quiz"""
        self.assertEqual((self.quiz.start_date).strftime('%Y-%m-%d'),
                         '2014-06-16')
        self.assertEqual(self.quiz.duration, 30)
        self.assertTrue(self.quiz.active is False)
        self.assertEqual(self.quiz.description, 'demo quiz')


###############################################################################
class QuestionPaperTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # All active questions
        self.questions = Question.objects.filter(active=True)
        self.quiz = Quiz.objects.get(id=1)

        # create question paper
        self.question_paper = QuestionPaper.objects.create(quiz=self.quiz,
                                                           total_marks=0.0)
        # add fixed set of questions to the question paper
        self.question_paper.fixed_questions.add(self.questions[3],
                                                self.questions[5])
        # create two QuestionSet for random questions
        # QuestionSet 1
        self.question_set_1 = QuestionSet.objects.create(marks=2,
                                                         num_questions=2)

        # add pool of questions for random sampling
        self.question_set_1.questions.add(self.questions[6], self.questions[7],
                                          self.questions[8], self.questions[9])
        # add question set 1 to random questions in Question Paper
        self.question_paper.random_questions.add(self.question_set_1)

        # QuestionSet 2
        self.question_set_2 = QuestionSet.objects.create(marks=3,
                                                         num_questions=3)

        # add pool of questions
        self.question_set_2.questions.add(self.questions[11],
                                          self.questions[12],
                                          self.questions[13],
                                          self.questions[14])
        # add question set 2
        self.question_paper.random_questions.add(self.question_set_2)

        # ip address for AnswerPaper
        self.ip = '127.0.0.1'

        self.user = User.objects.get(pk=1)

    def test_questionpaper(self):
        """ Test question paper"""
        self.assertEqual(self.question_paper.quiz.description, 'demo quiz')
        self.assertEqual(list(self.question_paper.fixed_questions.all()),
                         [self.questions[3], self.questions[5]])

    def test_update_total_marks(self):
        """ Test update_total_marks() method of Question Paper"""
        self.assertEqual(self.question_paper.update_total_marks(), 15)

    def test_get_random_questions(self):
        """ Test get_random_questions() method of Question Paper"""
        random_questions_set_1 = self.question_set_1.get_random_questions()
        random_questions_set_2 = self.question_set_2.get_random_questions()

        # To check whether random questions are from random_question_set
        questions_set_1 = set(self.question_set_1.questions.all())
        random_set_1 = set(random_questions_set_1)
        random_set_2 = set(random_questions_set_2)
        boolean = questions_set_1.intersection(random_set_1) == random_set_1
        self.assertTrue(boolean)
        self.assertEqual(len(random_set_1), 2)
        # To check that the questions are random.
        # If incase not random then check that the order is diferent
        try:
            self.assertFalse(random_set_1 == random_set_2)
        except AssertionError:
            self.assertTrue(random_questions_set_1 != random_questions_set_2)

    def test_get_questions_for_answerpaper(self):
        """ Test get_questions_for_answerpaper() method of Question Paper"""
        questions = self.question_paper._get_questions_for_answerpaper()
        fixed = list(self.question_paper.fixed_questions.all())
        question_set = self.question_paper.random_questions.all()
        total_random_questions = 0
        available_questions = []
        for qs in question_set:
            total_random_questions += qs.num_questions
            available_questions += qs.questions.all()
        self.assertEqual(total_random_questions, 5)
        self.assertEqual(len(available_questions), 8)
        self.assertEqual(len(questions), 7)

    def test_make_answerpaper(self):
        """ Test make_answerpaper() method of Question Paper"""
        answerpaper = self.question_paper.make_answerpaper(self.user, self.ip)
        self.assertIsInstance(answerpaper, AnswerPaper)
        paper_questions = set((answerpaper.questions).split('|'))
        self.assertEqual(len(paper_questions), 7)
        fixed = {'4', '6'}
        boolean = fixed.intersection(paper_questions) == fixed
        self.assertTrue(boolean)


###############################################################################
class AnswerPaperTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ip = '101.0.0.1'
        self.user = User.objects.get(id=1)
        self.profile = self.user.profile
        self.quiz = Quiz.objects.get(pk=1)
        self.question_paper = QuestionPaper(quiz=self.quiz, total_marks=3)
        self.question_paper.save()

        # create answerpaper
        self.answerpaper = AnswerPaper(user=self.user, profile=self.profile,
                                       questions='1|2|3',
                                       question_paper=self.question_paper,
                                       start_time='2014-06-13 12:20:19.791297',
                                       end_time='2014-06-13 12:50:19.791297',
                                       user_ip=self.ip)
        self.answerpaper.questions_answered = '1'
        self.answerpaper.save()

        # answers for the Answer Paper
        self.answer_right = Answer(question=Question.objects.get(id=1),
                                   answer="Demo answer", correct=True, marks=1)
        self.answer_wrong = Answer(question=Question.objects.get(id=2),
                                   answer="My answer", correct=False, marks=0)
        self.answer_right.save()
        self.answer_wrong.save()
        self.answerpaper.answers.add(self.answer_right)
        self.answerpaper.answers.add(self.answer_wrong)

    def test_answerpaper(self):
        """ Test Answer Paper"""
        self.assertEqual(self.answerpaper.user.username, 'demo_user')
        self.assertEqual(self.answerpaper.profile_id, 1)
        self.assertEqual(self.answerpaper.user_ip, self.ip)
        questions = self.answerpaper.questions
        num_questions = len(questions.split('|'))
        self.assertEqual(questions, '1|2|3')
        self.assertEqual(num_questions, 3)
        self.assertEqual(self.answerpaper.question_paper, self.question_paper)
        self.assertEqual(self.answerpaper.start_time,
                         '2014-06-13 12:20:19.791297')
        self.assertEqual(self.answerpaper.end_time,
                         '2014-06-13 12:50:19.791297')

    def test_current_question(self):
        """ Test current_question() method of Answer Paper"""
        current_question = self.answerpaper.current_question()
        self.assertEqual(current_question, '2')

    def test_completed_question(self):
        """ Test completed_question() method of Answer Paper"""
        question = self.answerpaper.completed_question(1)
        self.assertEqual(self.answerpaper.questions_left(), 2)

    def test_questions_left(self):
        """ Test questions_left() method of Answer Paper"""
        self.assertEqual(self.answerpaper.questions_left(), 2)

    def test_skip(self):
        """ Test skip() method of Answer Paper"""
        next_question_id = self.answerpaper.skip()
        self.assertTrue(next_question_id is not None)
        self.assertEqual(next_question_id, '3')

    def test_answered_str(self):
        """ Test answered_str() method of Answer Paper"""
        answered_question = self.answerpaper.get_answered_str()
        self.assertEqual(answered_question, '1')

    def test_get_marks_obtained(self):
        """ Test get_marks_obtained() method of Answer Paper"""
        self.assertEqual(self.answerpaper.get_marks_obtained(), 1.0)

    def test_get_question_answer(self):
        """ Test get_question_answer() method of Answer Paper"""
        answered = self.answerpaper.get_question_answers()
        first_answer = answered.values()[0][0]
        self.assertEqual(first_answer.answer, 'Demo answer')
        self.assertTrue(first_answer.correct)
        self.assertEqual(len(answered), 2)
