import unittest
from yaksh.models import User, Profile, Question, Quiz, QuestionPaper,\
    QuestionSet, AnswerPaper, Answer, Course, StandardTestCase,\
    StdoutBasedTestCase
import json
from datetime import datetime, timedelta
from django.contrib.auth.models import Group

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
    student = User.objects.create_user(username='demo_user3',
                                       password='demo',
                                       email='demo3@test.com')
    Profile.objects.create(user=student, roll_number=3, institute='IIT',
                           department='Chemical', position='Student')

    # create a course
    course = Course.objects.create(name="Python Course",
                                   enrollment="Enroll Request", creator=user)

    # create 20 questions
    for i in range(1, 21):
        Question.objects.create(summary='Q%d' % (i), points=1, type='code', user=user)

    # create a quiz
    quiz = Quiz.objects.create(start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0),
                        end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0),
                        duration=30, active=True,
                        attempts_allowed=1, time_between_attempts=0,
                        description='demo quiz', pass_criteria=0,
                        language='Python', prerequisite=None,
                        course=course)

    Quiz.objects.create(start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0),
                        end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0),
                        duration=30, active=False,
                        attempts_allowed=-1, time_between_attempts=0,
                        description='demo quiz', pass_criteria=40,
                        language='Python', prerequisite=quiz,
                        course=course)

def tearDownModule():
    User.objects.all().delete()
    Question.objects.all().delete()
    Quiz.objects.all().delete()


###############################################################################
class ProfileTestCases(unittest.TestCase):
    def setUp(self):
        self.user1 = User.objects.get(pk=1)
        self.profile = Profile.objects.get(pk=1)
        self.user2 = User.objects.get(pk=3)

    def test_user_profile(self):
        """ Test user profile"""
        self.assertEqual(self.user1.username, 'demo_user')
        self.assertEqual(self.profile.user.username, 'demo_user')
        self.assertEqual(int(self.profile.roll_number), 1)
        self.assertEqual(self.profile.institute, 'IIT')
        self.assertEqual(self.profile.department, 'Chemical')
        self.assertEqual(self.profile.position, 'Student')

###############################################################################
class QuestionTestCases(unittest.TestCase):
    def setUp(self):
        # Single question details
        self.user1 = User.objects.get(pk=1)
        self.user2 = User.objects.get(pk=2)
        self.question1 = Question(summary='Demo question', language='Python',
                                 type='Code', active=True,
                                 test_case_type='standardtestcase',
                                 description='Write a function', points=1.0,
                                 user=self.user1)
        self.question1.save()

        self.question2 = Question(summary='Demo Json', language='python',
                                 type='code', active=True,
                                 description='factorial of a no', points=2.0,
                                 user=self.user2)
        self.question2.save()

        self.question1.tags.add('python', 'function')
        self.assertion_testcase = StandardTestCase(question=self.question1,
                                 test_case='assert myfunc(12, 13) == 15')
        answer_data = {"user_answer": "demo_answer",
                         "test_case_data": ["assert myfunc(12, 13) == 15"],
                    }
        self.answer_data_json = json.dumps(answer_data)
        self.user_answer = "demo_answer"
        questions_data = [{"snippet": "def fact()", "active": True, "points": 1.0,
                        "ref_code_path": "", "description": "factorial of a no",
                        "language": "Python", "test": "", "type": "Code",
                        "options": "", "summary": "Json Demo"}]
        self.json_questions_data = json.dumps(questions_data)

    def test_question(self):
        """ Test question """
        self.assertEqual(self.question1.summary, 'Demo question')
        self.assertEqual(self.question1.language, 'Python')
        self.assertEqual(self.question1.type, 'Code')
        # self.assertFalse(self.question.options)
        self.assertEqual(self.question1.description, 'Write a function')
        self.assertEqual(self.question1.points, 1.0)
        self.assertTrue(self.question1.active)
        # self.assertEqual(self.question.snippet, 'def myfunc()')
        tag_list = []
        for tag in self.question1.tags.all():
                    tag_list.append(tag.name)
        self.assertEqual(tag_list, ['python', 'function'])

    def test_consolidate_answer_data(self):
        """ Test consolidate_answer_data function """
        result = self.question1.consolidate_answer_data(self.user_answer)
        self.assertEqual(result, self.answer_data_json)

    def test_dump_questions_into_json(self):
        """ Test dump questions into json """
        question = Question()
        question_id = ['24']
        questions = json.loads(question.dump_into_json(question_id, self.user1))
        for q in questions:
            self.assertEqual(self.question2.summary, q['summary'])
            self.assertEqual(self.question2.language, q['language'])
            self.assertEqual(self.question2.type, q['type'])
            self.assertEqual(self.question2.description, q['description'])
            self.assertEqual(self.question2.points, q['points'])
            self.assertTrue(self.question2.active)
            self.assertEqual(self.question2.snippet, q['snippet'])

    def test_load_questions_from_json(self):
        """ Test load questions into database from json """
        question = Question()
        result = question.load_from_json(self.json_questions_data, self.user1)
        question_data = Question.objects.get(pk=27)
        self.assertEqual(question_data.summary, 'Json Demo')
        self.assertEqual(question_data.language, 'Python')
        self.assertEqual(question_data.type, 'Code')
        self.assertEqual(question_data.description, 'factorial of a no')
        self.assertEqual(question_data.points, 1.0)
        self.assertTrue(question_data.active)
        self.assertEqual(question_data.snippet, 'def fact()')

###############################################################################
# class TestCaseTestCases(unittest.TestCase):
#     def setUp(self):
#         self.question = Question(summary='Demo question', language='Python',
#                                  type='Code', active=True,
#                                  description='Write a function', points=1.0,
#                                  snippet='def myfunc()')
#         self.question.save()
#         self.testcase = TestCase(question=self.question,
#                                  func_name='def myfunc', kw_args='a=10,b=11',
#                                  pos_args='12,13', expected_answer='15')

#     def test_testcase(self):
#         """ Test question """
#         self.assertEqual(self.testcase.question, self.question)
#         self.assertEqual(self.testcase.func_name, 'def myfunc')
#         self.assertEqual(self.testcase.kw_args, 'a=10,b=11')
#         self.assertEqual(self.testcase.pos_args, '12,13')
#         self.assertEqual(self.testcase.expected_answer, '15')


###############################################################################
class QuizTestCases(unittest.TestCase):
    def setUp(self):
        self.quiz1 = Quiz.objects.get(pk=1)
        self.quiz2 = Quiz.objects.get(pk=2)

    def test_quiz(self):
        """ Test Quiz"""
        self.assertEqual((self.quiz1.start_date_time).strftime('%Y-%m-%d'),
                         '2015-10-09')
        self.assertEqual((self.quiz1.start_date_time).strftime('%H:%M:%S'),
                         '10:08:15')
        self.assertEqual(self.quiz1.duration, 30)
        self.assertTrue(self.quiz1.active)
        self.assertEqual(self.quiz1.description, 'demo quiz')
        self.assertEqual(self.quiz1.language, 'Python')
        self.assertEqual(self.quiz1.pass_criteria, 0)
        self.assertEqual(self.quiz1.prerequisite, None)

    def test_is_expired(self):
        self.assertFalse(self.quiz1.is_expired())
        self.assertTrue(self.quiz2.is_expired())

    def test_has_prerequisite(self):
        self.assertFalse(self.quiz1.has_prerequisite())
        self.assertTrue(self.quiz2.has_prerequisite())

    def test_get_active_quizzes(self):
        quizzes = Quiz.objects.get_active_quizzes()
        for quiz in quizzes:
            self.assertTrue(quiz.active)


###############################################################################
class QuestionPaperTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # All active questions
        self.questions = Question.objects.filter(active=True)
        self.quiz = Quiz.objects.get(id=1)

        # create question paper
        self.question_paper = QuestionPaper.objects.create(quiz=self.quiz,
                                  total_marks=0.0, shuffle_questions=True)

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

        self.attempted_papers = AnswerPaper.objects.filter(question_paper=self.question_paper,
                                                        user=self.user)

    def test_questionpaper(self):
        """ Test question paper"""
        self.assertEqual(self.question_paper.quiz.description, 'demo quiz')
        self.assertSequenceEqual(self.question_paper.fixed_questions.all(),
                         [self.questions[3], self.questions[5]])
        self.assertTrue(self.question_paper.shuffle_questions)

    def test_update_total_marks(self):
        """ Test update_total_marks() method of Question Paper"""
        self.assertEqual(self.question_paper.total_marks, 0)
        self.question_paper.update_total_marks()
        self.assertEqual(self.question_paper.total_marks, 15)

    def test_get_random_questions(self):
        """ Test get_random_questions() method of Question Paper"""
        random_questions_set_1 = self.question_set_1.get_random_questions()
        random_questions_set_2 = self.question_set_2.get_random_questions()
        total_random_questions = len(random_questions_set_1 + random_questions_set_2)
        self.assertEqual(total_random_questions, 5)

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

    def test_make_answerpaper(self):
        """ Test make_answerpaper() method of Question Paper"""
        already_attempted = self.attempted_papers.count()
        attempt_num = already_attempted + 1
        answerpaper = self.question_paper.make_answerpaper(self.user, self.ip,
                                                             attempt_num)
        self.assertIsInstance(answerpaper, AnswerPaper)
        paper_questions = answerpaper.questions.all()
        self.assertEqual(len(paper_questions), 7)
        fixed_questions = set(self.question_paper.fixed_questions.all())
        self.assertTrue(fixed_questions.issubset(set(paper_questions)))
        answerpaper.passed = True
        answerpaper.save()
        self.assertFalse(self.question_paper.is_prerequisite_passed(self.user))
        # test can_attempt_now(self):
        self.assertFalse(self.question_paper.can_attempt_now(self.user))


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
        self.questions = Question.objects.filter(id__in=[1,2,3])
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=20)

        # create answerpaper
        self.answerpaper = AnswerPaper(user=self.user,
                                       question_paper=self.question_paper,
                                       start_time=self.start_time,
                                       end_time=self.end_time,
                                       user_ip=self.ip)
        self.attempted_papers = AnswerPaper.objects.filter(question_paper=self.question_paper,
                                                        user=self.user)
        already_attempted = self.attempted_papers.count()
        self.answerpaper.attempt_number = already_attempted + 1
        self.answerpaper.save()
        self.answerpaper.questions.add(*self.questions)
        self.answerpaper.questions_unanswered.add(*self.questions)
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
        self.assertEqual(self.answerpaper.user_ip, self.ip)
        questions = self.answerpaper.get_questions()
        num_questions = len(questions)
        self.assertSequenceEqual(list(questions), list(self.questions))
        self.assertEqual(num_questions, 3)
        self.assertEqual(self.answerpaper.question_paper, self.question_paper)
        self.assertEqual(self.answerpaper.start_time, self.start_time)
        self.assertEqual(self.answerpaper.status, 'inprogress')

    def test_questions(self):
        # Test questions_left() method of Answer Paper
        self.assertEqual(self.answerpaper.questions_left(), 3)
        # Test current_question() method of Answer Paper
        current_question = self.answerpaper.current_question()
        self.assertEqual(current_question.id, 1)
        # Test completed_question() method of Answer Paper
        question = self.answerpaper.completed_question(1)
        self.assertEqual(self.answerpaper.questions_left(), 2)
        # Test skip() method of Answer Paper
        current_question = self.answerpaper.current_question()
        self.assertEqual(current_question.id, 2)
        next_question_id = self.answerpaper.skip(current_question.id)
        self.assertTrue(next_question_id is not None)
        self.assertEqual(next_question_id.id, 3)
        questions_answered = self.answerpaper.get_questions_answered()
        self.assertEqual(questions_answered.count(), 1)
        self.assertSequenceEqual(questions_answered, [self.questions[0]])
        questions_unanswered = self.answerpaper.get_questions_unanswered()
        self.assertEqual(questions_unanswered.count(), 2)
        self.assertSequenceEqual(questions_unanswered,
                                 [self.questions[1], self.questions[2]])

    def test_update_marks(self):
        """ Test update_marks method of AnswerPaper"""
        self.answerpaper.update_marks('inprogress')
        self.assertEqual(self.answerpaper.status, 'inprogress')
        self.assertTrue(self.answerpaper.is_attempt_inprogress())
        self.answerpaper.update_marks()
        self.assertEqual(self.answerpaper.status, 'completed')
        self.assertEqual(self.answerpaper.marks_obtained, 1.0)
        self.assertEqual(self.answerpaper.percent, 33.33)
        self.assertTrue(self.answerpaper.passed)
        self.assertFalse(self.answerpaper.is_attempt_inprogress())

    def test_set_end_time(self):
        current_time = datetime.now()
        self.answerpaper.set_end_time(current_time)
        self.assertEqual(self.answerpaper.end_time,current_time)

    def test_get_question_answer(self):
        """ Test get_question_answer() method of Answer Paper"""
        answered = self.answerpaper.get_question_answers()
        first_answer = answered.values()[0][0]
        self.assertEqual(first_answer.answer, 'Demo answer')
        self.assertTrue(first_answer.correct)
        self.assertEqual(len(answered), 2)

    def test_is_answer_correct(self):
        self.assertTrue(self.answerpaper.is_answer_correct(self.questions[0]))
        self.assertFalse(self.answerpaper.is_answer_correct(self.questions[1]))

    def test_get_previous_answers(self):
        answers = self.answerpaper.get_previous_answers(self.questions[0])
        self.assertEqual(answers.count(), 1)
        self.assertTrue(answers[0], self.answer_right)
        answers = self.answerpaper.get_previous_answers(self.questions[1])
        self.assertEqual(answers.count(), 1)
        self.assertTrue(answers[0], self.answer_wrong)

    def test_set_marks (self):
        self.answer_wrong.set_marks(0.5)
        self.assertEqual(self.answer_wrong.marks, 0.5)
        self.answer_wrong.set_marks(10.0)
        self.assertEqual(self.answer_wrong.marks,1.0)


###############################################################################
class CourseTestCases(unittest.TestCase):
    def setUp(self):
        self.course = Course.objects.get(pk=1)
        self.creator = User.objects.get(pk=1)
        self.student1 = User.objects.get(pk=2)
        self.student2 = User.objects.get(pk=3)
        self.quiz1 = Quiz.objects.get(pk=1)
        self.quiz2 = Quiz.objects.get(pk=2)

    def test_is_creator(self):
        """ Test is_creator method of Course"""
        self.assertTrue(self.course.is_creator(self.creator))

    def test_is_self_enroll(self):
        """ Test is_self_enroll method of Course"""
        self.assertFalse(self.course.is_self_enroll())

    def test_deactivate(self):
        """ Test deactivate method of Course"""
        self.course.deactivate()
        self.assertFalse(self.course.active)

    def test_activate(self):
        """ Test activate method of Course"""
        self.course.activate()
        self.assertTrue(self.course.active)

    def test_request(self):
        """ Test request and get_requests methods of Course"""
        self.course.request(self.student1, self.student2)
        self.assertSequenceEqual(self.course.get_requests(),
                                 [self.student1, self.student2])

    def test_enroll_reject(self):
        """ Test enroll, reject, get_enrolled and get_rejected methods"""
        self.assertSequenceEqual(self.course.get_enrolled(), [])
        was_rejected = False
        self.course.enroll(was_rejected, self.student1)
        self.assertSequenceEqual(self.course.get_enrolled(), [self.student1])

        self.assertSequenceEqual(self.course.get_rejected(), [])
        was_enrolled = False
        self.course.reject(was_enrolled, self.student2)
        self.assertSequenceEqual(self.course.get_rejected(), [self.student2])

        was_rejected = True
        self.course.enroll(was_rejected, self.student2)
        self.assertSequenceEqual(self.course.get_enrolled(),
                                 [self.student1, self.student2])
        self.assertSequenceEqual(self.course.get_rejected(), [])

        was_enrolled = True
        self.course.reject(was_enrolled, self.student2)
        self.assertSequenceEqual(self.course.get_rejected(), [self.student2])
        self.assertSequenceEqual(self.course.get_enrolled(), [self.student1])

        self.assertTrue(self.course.is_enrolled(self.student1))

    def test_get_quizzes(self):
        """ Test get_quizzes method of Courses"""
        self.assertSequenceEqual(self.course.get_quizzes(), [self.quiz1, self.quiz2])

    def test_add_teachers(self):
        """ Test to add teachers to a course"""
        self.course.add_teachers(self.student1, self.student2)
        self.assertSequenceEqual(self.course.get_teachers(), [self.student1, self.student2])

    def test_remove_teachers(self):
        """ Test to remove teachers from a course"""
        self.course.add_teachers(self.student1, self.student2)
        self.course.remove_teachers(self.student1)
        self.assertSequenceEqual(self.course.get_teachers(), [self.student2])

    def test_is_teacher(self):
        """ Test to check if user is teacher"""
        self.course.add_teachers(self.student2)
        result = self.course.is_teacher(self.student2)
        self.assertTrue(result)


###############################################################################
class TestCaseTestCases(unittest.TestCase):
    def setUp(self):
        self.question = Question(summary='Demo question', language='Python',
                                 type='Code', active=True,
                                 description='Write a function', points=1.0,
                                )
        self.question.save()
        self.assertion_testcase = StandardTestCase(question=self.question,
                                 test_case='assert myfunc(12, 13) == 15')
        self.stdout_based_testcase = StdoutBasedTestCase(question=self.question,
                                 output='Hello World')

    def test_assertion_testcase(self):
        """ Test question """
        self.assertEqual(self.assertion_testcase.question, self.question)
        self.assertEqual(self.assertion_testcase.test_case, 'assert myfunc(12, 13) == 15')

    def test_stdout_based_testcase(self):
        """ Test question """
        self.assertEqual(self.stdout_based_testcase.question, self.question)
        self.assertEqual(self.stdout_based_testcase.output, 'Hello World')
