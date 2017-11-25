import unittest
from yaksh.models import User, Profile, Question, Quiz, QuestionPaper,\
    QuestionSet, AnswerPaper, Answer, Course, StandardTestCase,\
    StdIOBasedTestCase, FileUpload, McqTestCase, AssignmentUpload 
from yaksh.code_server import(ServerPool,
                              get_result as get_result_from_code_server
                              )
import json
import ruamel.yaml as yaml
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
from django.contrib.auth.models import Group
from django.core.files import File
from django.forms.models import model_to_dict
from textwrap import dedent
import zipfile
import os
import shutil
import tempfile
from threading import Thread
from yaksh import settings

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

    user4 = User.objects.create_user(username='demo_user4',
        password='demo',
        email='demo4@test.com'
    )
    Profile.objects.create(user=user4, roll_number=4, institute='IIT',
                           department='Chemical', position='Student')


    # create a course
    course = Course.objects.create(name="Python Course",
                                   enrollment="Enroll Request", creator=user)

    # create 20 questions
    for i in range(1, 21):
        Question.objects.create(summary='Q%d' % (i), points=1, type='code', user=user)

    # create a quiz
    quiz = Quiz.objects.create(start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                                        tzinfo=pytz.utc),
                        end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0,
                                               tzinfo=pytz.utc),
                        duration=30, active=True,
                        attempts_allowed=1, time_between_attempts=0,
                        description='demo quiz 1', pass_criteria=0,
                        language='Python', prerequisite=None,
                        course=course, instructions="Demo Instructions")

    Quiz.objects.create(start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0,
                                                 tzinfo=pytz.utc),
                        end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                                               tzinfo=pytz.utc),
                        duration=30, active=False,
                        attempts_allowed=-1, time_between_attempts=0,
                        description='demo quiz 2', pass_criteria=40,
                        language='Python', prerequisite=quiz,
                        course=course, instructions="Demo Instructions")
    tmp_file1 = os.path.join(tempfile.gettempdir(), "test.txt")
    with open(tmp_file1, 'wb') as f:
        f.write('2'.encode('ascii'))


def tearDownModule():
    User.objects.all().delete()
    Question.objects.all().delete()
    Quiz.objects.all().delete()
    Course.objects.all().delete()
    QuestionPaper.objects.all().delete()


###############################################################################
class ProfileTestCases(unittest.TestCase):
    def setUp(self):
        self.user1 = User.objects.get(username="demo_user")
        self.profile = Profile.objects.get(user=self.user1)
        self.user2 = User.objects.get(username='demo_user3')

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
        self.user1 = User.objects.get(username="demo_user")
        self.user2 = User.objects.get(username="demo_user2")
        self.question1 = Question.objects.create(summary='Demo Python 1',
            language='Python',
            type='Code',
            active=True,
            description='Write a function',
            points=1.0,
            snippet='def myfunc()',
            user=self.user1
        )

        self.question2 = Question.objects.create(summary='Yaml Json',
            language='python',
            type='code',
            active=True,
            description='factorial of a no',
            points=2.0,
            snippet='def fact()',
            user=self.user2
        )

        # create a temp directory and add files for loading questions test
        file_path = os.path.join(tempfile.gettempdir(), "test.txt")
        self.load_tmp_path = tempfile.mkdtemp()
        shutil.copy(file_path, self.load_tmp_path)
        file1 = os.path.join(self.load_tmp_path, "test.txt")

        # create a temp directory and add files for dumping questions test
        self.dump_tmp_path = tempfile.mkdtemp()
        shutil.copy(file_path, self.dump_tmp_path)
        file2 = os.path.join(self.dump_tmp_path, "test.txt")
        upload_file = open(file2, "r")
        django_file = File(upload_file)
        file = FileUpload.objects.create(file=django_file,
                                         question=self.question2
                                         )

        self.question1.tags.add('python', 'function')
        self.assertion_testcase = StandardTestCase(question=self.question1,
            test_case='assert myfunc(12, 13) == 15',
            type='standardtestcase'
        )
        self.upload_test_case = StandardTestCase(question=self.question2,
            test_case='assert fact(3) == 6',
            type='standardtestcase'
        )
        self.upload_test_case.save()
        self.user_answer = "demo_answer"
        self.test_case_upload_data = [{"test_case": "assert fact(3)==6",
                                        "test_case_type": "standardtestcase",
                                        "test_case_args": "",
                                        "weight": 1.0
                                        }]
        questions_data = [{"snippet": "def fact()", "active": True,
                           "points": 1.0,
                           "description": "factorial of a no",
                           "language": "Python", "type": "Code",
                           "testcase": self.test_case_upload_data,
                           "files": [[file1, 0]],
                           "summary": "Yaml Demo",
                           "tags": ['yaml_demo']
                           }]
        questions_data_with_missing_fields = [{"active": True,
                                               "points": 1.0,
                                               "description":\
                                                "factorial of a no",
                                               "language": "Python",
                                               "type": "Code",
                                               "testcase":\
                                                self.test_case_upload_data,
                                               "summary": "Yaml Demo 2"
                                               }]
        self.yaml_questions_data = yaml.safe_dump_all(questions_data)
        self.yaml_questions_data_with_missing_fields = yaml.safe_dump_all(
                questions_data_with_missing_fields
                )

    def tearDown(self):
        shutil.rmtree(self.load_tmp_path)
        shutil.rmtree(self.dump_tmp_path)
        uploaded_files = FileUpload.objects.all()
        que_id_list = [file.question.id for file in uploaded_files]
        for que_id in que_id_list:
            dir_path = os.path.join(os.getcwd(), "yaksh", "data",
                                    "question_{0}".format(que_id)
                                    )
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        uploaded_files.delete()

    def test_question(self):
        """ Test question """
        self.assertEqual(self.question1.summary, 'Demo Python 1')
        self.assertEqual(self.question1.language, 'Python')
        self.assertEqual(self.question1.type, 'Code')
        self.assertEqual(self.question1.description, 'Write a function')
        self.assertEqual(self.question1.points, 1.0)
        self.assertTrue(self.question1.active)
        self.assertEqual(self.question1.snippet, 'def myfunc()')
        tag_list = []
        for tag in self.question1.tags.all():
                    tag_list.append(tag.name)
        for tag in tag_list:
            self.assertIn(tag, ['python', 'function'])

    def test_dump_questions(self):
        """ Test dump questions into Yaml """
        question = Question()
        question_id = [self.question2.id]
        questions_zip = question.dump_questions(question_id, self.user2)
        que_file = FileUpload.objects.get(question=self.question2.id)
        zip_file = zipfile.ZipFile(questions_zip, "r")
        tmp_path = tempfile.mkdtemp()
        zip_file.extractall(tmp_path)
        test_case = self.question2.get_test_cases()
        with open("{0}/questions_dump.yaml".format(tmp_path), "r") as f:
            questions = yaml.safe_load_all(f.read())
            for q in questions:
                self.assertEqual(self.question2.summary, q['summary'])
                self.assertEqual(self.question2.language, q['language'])
                self.assertEqual(self.question2.type, q['type'])
                self.assertEqual(self.question2.description, q['description'])
                self.assertEqual(self.question2.points, q['points'])
                self.assertTrue(self.question2.active)
                self.assertEqual(self.question2.snippet, q['snippet'])
                self.assertEqual(os.path.basename(que_file.file.path),
                                                  q['files'][0][0])
                self.assertEqual([case.get_field_value() for case in test_case],
                                 q['testcase']
                                 )
        for file in zip_file.namelist():
            os.remove(os.path.join(tmp_path, file))

    def test_load_questions_with_all_fields(self):
        """ Test load questions into database from Yaml """
        question = Question()
        result = question.load_questions(self.yaml_questions_data, self.user1)
        question_data = Question.objects.get(summary="Yaml Demo")
        file = FileUpload.objects.get(question=question_data)
        test_case = question_data.get_test_cases()
        self.assertEqual(question_data.summary, 'Yaml Demo')
        self.assertEqual(question_data.language, 'Python')
        self.assertEqual(question_data.type, 'Code')
        self.assertEqual(question_data.description, 'factorial of a no')
        self.assertEqual(question_data.points, 1.0)
        self.assertTrue(question_data.active)
        tags = question_data.tags.all().values_list("name",flat=True)
        self.assertListEqual(list(tags), ['yaml_demo'])
        self.assertEqual(question_data.snippet, 'def fact()')
        self.assertEqual(os.path.basename(file.file.path), "test.txt")
        self.assertEqual([case.get_field_value() for case in test_case],
                         self.test_case_upload_data
                         )

    def test_load_questions_with_missing_fields(self):
        """ Test load questions into database from Yaml with
            missing fields like files, snippet and tags. """
        question = Question()
        result = question.load_questions(
                            self.yaml_questions_data_with_missing_fields,
                            self.user1
                            )
        question_data = Question.objects.get(summary="Yaml Demo 2")
        file = FileUpload.objects.filter(question=question_data)
        test_case = question_data.get_test_cases()
        self.assertEqual(question_data.summary,'Yaml Demo 2')
        self.assertEqual(question_data.language,'Python')
        self.assertEqual(question_data.type, 'Code')
        self.assertEqual(question_data.description,'factorial of a no')
        self.assertEqual(question_data.points, 1.0)
        self.assertTrue(question_data.active)
        self.assertEqual(question_data.snippet,'')
        self.assertListEqual(list(file),[])
        self.assertEqual([case.get_field_value() for case in test_case],
                         self.test_case_upload_data
                         )
        tags = question_data.tags.all().values_list("name",flat=True)
        self.assertListEqual(list(tags), [])

###############################################################################
class QuizTestCases(unittest.TestCase):
    def setUp(self):
        self.creator = User.objects.get(username="demo_user")
        self.teacher = User.objects.get(username="demo_user2")
        self.quiz1 = Quiz.objects.get(description='demo quiz 1')
        self.quiz2 = Quiz.objects.get(description='demo quiz 2')
        self.trial_course = Course.objects.create_trial_course(self.creator)

    def test_quiz(self):
        """ Test Quiz"""
        self.assertEqual((self.quiz1.start_date_time).strftime('%Y-%m-%d'),
                         '2015-10-09')
        self.assertEqual((self.quiz1.start_date_time).strftime('%H:%M:%S'),
                         '10:08:15')
        self.assertEqual(self.quiz1.duration, 30)
        self.assertTrue(self.quiz1.active)
        self.assertEqual(self.quiz1.description, 'demo quiz 1')
        self.assertEqual(self.quiz1.language, 'Python')
        self.assertEqual(self.quiz1.pass_criteria, 0)
        self.assertEqual(self.quiz1.prerequisite, None)
        self.assertEqual(self.quiz1.instructions, "Demo Instructions")

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

    def test_create_trial_quiz(self):
        """Test to check if trial quiz is created"""
        trial_quiz = Quiz.objects.create_trial_quiz(self.trial_course,
                                                    self.creator
                                                    )
        self.assertEqual(trial_quiz.course, self.trial_course)
        self.assertEqual(trial_quiz.duration, 1000)
        self.assertEqual(trial_quiz.description, "trial_questions")
        self.assertTrue(trial_quiz.is_trial)
        self.assertEqual(trial_quiz.time_between_attempts, 0)

    def test_create_trial_from_quiz_godmode(self):
        """Test to check if a copy of original quiz is created in godmode"""
        trial_quiz = Quiz.objects.create_trial_from_quiz(self.quiz1.id,
                                                         self.creator,
                                                         True
                                                         )
        self.assertEqual(trial_quiz.description,
                         "Trial_orig_id_{}_godmode".format(self.quiz1.id)
                         )
        self.assertTrue(trial_quiz.is_trial)
        self.assertEqual(trial_quiz.duration, 1000)
        self.assertTrue(trial_quiz.active)
        self.assertEqual(trial_quiz.end_date_time,
                         datetime(2199, 1, 1, 0, 0, 0, 0, tzinfo=pytz.utc)
                         )
        self.assertEqual(trial_quiz.time_between_attempts, 0)

    def test_create_trial_from_quiz_usermode(self):
        """Test to check if a copy of original quiz is created in usermode"""
        trial_quiz = Quiz.objects.create_trial_from_quiz(self.quiz2.id,
                                                         self.creator,
                                                         False
                                                         )
        self.assertEqual(trial_quiz.description,
                         "Trial_orig_id_{}_usermode".format(self.quiz2.id))
        self.assertTrue(trial_quiz.is_trial)
        self.assertEqual(trial_quiz.duration, self.quiz2.duration)
        self.assertEqual(trial_quiz.active, self.quiz2.active)
        self.assertEqual(trial_quiz.start_date_time,
                         self.quiz2.start_date_time
                         )
        self.assertEqual(trial_quiz.end_date_time,
                         self.quiz2.end_date_time
                         )
        self.assertEqual(trial_quiz.time_between_attempts, 0)

    def test_view_answerpaper(self):
        self.assertFalse(self.quiz1.view_answerpaper)
        self.assertFalse(self.quiz2.view_answerpaper)

        # When
        self.quiz1.view_answerpaper = True
        self.quiz1.save()

        # Then
        self.assertTrue(self.quiz1.view_answerpaper)



###############################################################################
class QuestionPaperTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # All active questions
        self.questions = Question.objects.filter(active=True)
        self.quiz = Quiz.objects.get(description="demo quiz 1")

        # create question paper with only fixed questions
        self.question_paper_fixed_questions = QuestionPaper.objects.create(
                quiz=self.quiz)
        self.question_paper_fixed_questions.fixed_questions.add(
                self.questions.get(summary='Q11'), self.questions.get(summary='Q10'))

        # create question paper with only random questions
        self.question_paper_random_questions = QuestionPaper.objects.create(
                quiz=self.quiz)
        self.question_set_random = QuestionSet.objects.create(marks=2,
            num_questions=2)
        self.question_set_random.questions.add(self.questions.get(summary='Q13'),
                self.questions.get(summary='Q5'), self.questions.get(summary='Q7'))
        self.question_paper_random_questions.random_questions.add(
                self.question_set_random)

        # create question paper with no questions
        self.question_paper_no_questions = QuestionPaper.objects.create(
                quiz=self.quiz)

        # create question paper
        self.question_paper = QuestionPaper.objects.create(quiz=self.quiz,
            total_marks=0.0,
            shuffle_questions=True
        )

        self.question_paper.fixed_question_order = "{0}, {1}".format(
                self.questions[3].id, self.questions[5].id
                )
        # add fixed set of questions to the question paper
        self.question_paper.fixed_questions.add(self.questions[3],
                self.questions[5]
                )
        # create two QuestionSet for random questions
        # QuestionSet 1
        self.question_set_1 = QuestionSet.objects.create(marks=2,
            num_questions=2
        )

        # add pool of questions for random sampling
        self.question_set_1.questions.add(self.questions[6],
            self.questions[7],
            self.questions[8],
            self.questions[9]
        )
        # add question set 1 to random questions in Question Paper
        self.question_paper.random_questions.add(self.question_set_1)

        # QuestionSet 2
        self.question_set_2 = QuestionSet.objects.create(marks=3,
            num_questions=3
        )

        # add pool of questions
        self.question_set_2.questions.add(self.questions[11],
            self.questions[12],
            self.questions[13],
            self.questions[14]
        )
        # add question set 2
        self.question_paper.random_questions.add(self.question_set_2)

        # ip address for AnswerPaper
        self.ip = '127.0.0.1'

        self.user = User.objects.get(username="demo_user")

        self.attempted_papers = AnswerPaper.objects.filter(
            question_paper=self.question_paper,
            user=self.user
        )

        # For Trial case
        self.questions_list = [self.questions[3].id, self.questions[5].id]
        self.trial_course = Course.objects.create_trial_course(self.user)
        self.trial_quiz = Quiz.objects.create_trial_quiz(self.trial_course, self.user)


    def test_get_question_bank(self):
        # Given
        summaries = ['Q11', 'Q10']
        questions = list(Question.objects.filter(summary__in=summaries))
        # When
        question_bank = self.question_paper_fixed_questions.get_question_bank()
        # Then
        self.assertSequenceEqual(questions, question_bank)

        # Given
        summaries = ['Q13','Q5','Q7']
        questions = list(Question.objects.filter(summary__in=summaries))
        # When
        question_bank = self.question_paper_random_questions.get_question_bank()
        # Then
        self.assertSequenceEqual(questions, question_bank)

        # Given
        questions = []
        # When
        question_bank = self.question_paper_no_questions.get_question_bank()
        # Then
        self.assertSequenceEqual(questions, question_bank)

    def test_questionpaper(self):
        """ Test question paper"""
        self.assertEqual(self.question_paper.quiz.description, 'demo quiz 1')
        self.assertSequenceEqual(self.question_paper.fixed_questions.all(),
                [self.questions[3], self.questions[5]]
                )
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
        total_random_questions = len(random_questions_set_1 + \
            random_questions_set_2)
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
        # trying to create an answerpaper with same parameters passed.
        answerpaper2 = self.question_paper.make_answerpaper(self.user, self.ip,
                                                             attempt_num)
        # check if make_answerpaper returned an object instead of creating one.
        self.assertEqual(answerpaper, answerpaper2)



    def test_create_trial_paper_to_test_quiz(self):
        qu_list = [str(self.questions_list[0]), str(self.questions_list[1])]
        trial_paper = QuestionPaper.objects.create_trial_paper_to_test_quiz\
                                            (self.trial_quiz,
                                             self.quiz.id
                                             )
        trial_paper.random_questions.add(self.question_set_1)
        trial_paper.random_questions.add(self.question_set_2)
        trial_paper.fixed_question_order = ",".join(qu_list)
        self.assertEqual(trial_paper.quiz, self.trial_quiz)
        self.assertSequenceEqual(trial_paper.get_ordered_questions(),
                         self.question_paper.get_ordered_questions()
                         )
        trial_paper_ran = [q_set.id for q_set in
                           trial_paper.random_questions.all()]
        qp_ran = [q_set.id for q_set in
                  self.question_paper.random_questions.all()]

        self.assertSequenceEqual(trial_paper_ran, qp_ran)

    def test_create_trial_paper_to_test_questions(self):
        qu_list = [str(self.questions_list[0]), str(self.questions_list[1])]
        trial_paper = QuestionPaper.objects.\
                         create_trial_paper_to_test_questions(
                                self.trial_quiz, qu_list
                                )
        self.assertEqual(trial_paper.quiz, self.trial_quiz)
        fixed_q = self.question_paper.fixed_questions.values_list(
            'id', flat=True)
        self.assertSequenceEqual(self.questions_list, fixed_q)

    def test_fixed_order_questions(self):
        fixed_ques = self.question_paper.get_ordered_questions()
        actual_ques = [self.questions[3], self.questions[5]]
        self.assertSequenceEqual(fixed_ques, actual_ques)


###############################################################################
class AnswerPaperTestCases(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ip = '101.0.0.1'
        self.user = User.objects.get(username='demo_user')
        self.user2 = User.objects.get(username='demo_user2')
        self.profile = self.user.profile
        self.quiz = Quiz.objects.get(description='demo quiz 1')
        self.question_paper = QuestionPaper(quiz=self.quiz, total_marks=3)
        self.question_paper.save()
        self.quiz2 = Quiz.objects.get(description='demo quiz 2')
        self.qtn_paper_with_single_question = QuestionPaper(
            quiz=self.quiz2, total_marks=3
        )
        self.qtn_paper_with_single_question.save()

        all_questions = Question.objects.all()
        self.questions = all_questions[0:3]
        self.start_time = timezone.now()
        self.end_time = self.start_time + timedelta(minutes=20)
        self.question1 = all_questions[0]
        self.question2 = all_questions[1]
        self.question3 = all_questions[2]
        self.question4 = all_questions[3]

        # create answerpaper
        self.answerpaper = AnswerPaper(user=self.user,
            question_paper=self.question_paper,
            start_time=self.start_time,
            end_time=self.end_time,
            user_ip=self.ip
        )
        self.attempted_papers = AnswerPaper.objects.filter(
            question_paper=self.question_paper,
            user=self.user
        )
        self.question_paper.fixed_questions.add(*self.questions)
        already_attempted = self.attempted_papers.count()
        self.answerpaper.attempt_number = already_attempted + 1
        self.answerpaper.save()
        self.answerpaper.questions.add(*self.questions)
        self.answerpaper.questions_unanswered.add(*self.questions)
        self.answerpaper.save()
        # answers for the Answer Paper
        self.answer_right = Answer(question=self.question1,
            answer="Demo answer",
            correct=True, marks=1,
            error=json.dumps([])
        )
        self.answer_wrong = Answer(question=self.question2,
            answer="My answer",
            correct=False,
            marks=0,
            error=json.dumps(['error1', 'error2'])
        )
        self.answer_right.save()
        self.answer_wrong.save()
        self.answerpaper.answers.add(self.answer_right)
        self.answerpaper.answers.add(self.answer_wrong)

        self.answer1 = Answer.objects.create(
            question=self.question1,
            answer="answer1", correct=False, error=json.dumps([])
        )
        self.answerpaper.answers.add(self.answer1)

        # create an answerpaper with only one question
        self.answerpaper_single_question = AnswerPaper(user=self.user,
            question_paper=self.question_paper,
            start_time=self.start_time,
            end_time=self.end_time,
            user_ip=self.ip
        )
        self.attempted_papers = AnswerPaper.objects.filter(
            question_paper=self.question_paper,
            user=self.user
        )
        self.qtn_paper_with_single_question.fixed_questions.add(self.question4)
        already_attempted = self.attempted_papers.count()
        self.answerpaper_single_question.attempt_number = already_attempted + 1
        self.answerpaper_single_question.save()
        self.answerpaper_single_question.questions.add(self.question4)
        self.answerpaper_single_question.questions_unanswered.add(self.question4)
        self.answerpaper_single_question.save()
        # answers for the Answer Paper
        self.single_answer = Answer(question=self.question4,
            answer="Demo answer",
            correct=True, marks=1,
            error=json.dumps([])
        )
        self.single_answer.save()
        self.answerpaper_single_question.answers.add(self.single_answer)

        self.question1.language = 'python'
        self.question1.test_case_type = 'standardtestcase'
        self.question1.summary = "Question1"
        self.question1.save()
        self.question2.language = 'python'
        self.question2.type = 'mcq'
        self.question2.test_case_type = 'mcqtestcase'
        self.question2.summary = "Question2"
        self.question2.save()
        self.question3.language = 'python'
        self.question3.type = 'mcc'
        self.question3.test_case_type = 'mcqtestcase'
        self.question3.summary = "Question3"
        self.question3.save()
        self.assertion_testcase = StandardTestCase(
            question=self.question1,
            test_case='assert add(1, 3) == 4',
            type = 'standardtestcase'

        )
        self.assertion_testcase.save()
        self.mcq_based_testcase = McqTestCase(
            options = 'a',
            question=self.question2,
            correct = True,
            type = 'mcqtestcase'

        )
        self.mcq_based_testcase.save()
        self.mcc_based_testcase = McqTestCase(
            question=self.question3,
            options = 'a',
            correct = True,
            type = 'mcqtestcase'
        )
        self.mcc_based_testcase.save()

        # Setup quiz where questions are shuffled
        # Create Quiz and Question Paper
        self.quiz2 = Quiz.objects.get(description="demo quiz 2")
        self.question_paper2 = QuestionPaper(
            quiz=self.quiz2, total_marks=3, shuffle_questions=True)
        self.question_paper2.save()
        summary_list = ['Q%d' % (i) for i in range(1, 21)]
        self.que_list = Question.objects.filter(summary__in=summary_list)
        self.question_paper2.fixed_questions.add(*self.que_list)

        # Create AnswerPaper for user1 and user2
        self.user1_answerpaper = self.question_paper2.make_answerpaper(
            self.user, self.ip, 1
        )
        self.user2_answerpaper = self.question_paper2.make_answerpaper(
            self.user2, self.ip, 1
        )

        self.user2_answerpaper2 = self.question_paper.make_answerpaper(
            self.user2, self.ip, 1
        )
        settings.code_evaluators['python']['standardtestcase'] = \
            "yaksh.python_assertion_evaluator.PythonAssertionEvaluator"
        self.SERVER_POOL_PORT = 4000
        server_pool = ServerPool(n=1, pool_port=self.SERVER_POOL_PORT)
        self.server_pool = server_pool
        self.server_thread = t = Thread(target=server_pool.run)
        t.start()
    
    @classmethod
    def tearDownClass(self):
        self.server_pool.stop()
        self.server_thread.join()
        settings.code_evaluators['python']['standardtestcase'] = \
            "python_assertion_evaluator.PythonAssertionEvaluator"

    def test_get_per_question_score(self):
        # Given
        question_id = self.question4.id
        expected_score = 1
        # When
        score = self.answerpaper_single_question.get_per_question_score(question_id)
        # Then
        self.assertEqual(score, expected_score)

        # Given
        question_id = self.question2.id
        expected_score = 0
        # When
        score = self.answerpaper.get_per_question_score(question_id)
        # Then
        self.assertEqual(score, expected_score)

        # Given
        question_id = 131
        expected_score = 'NA'
        # When
        score = self.answerpaper.get_per_question_score(question_id)
        # Then
        self.assertEqual(score, expected_score)

    def test_returned_question_is_not_none(self):
        # Test add_completed_question and next_question
        # When all questions are answered

        # Before questions are answered
        self.assertEqual(self.answerpaper_single_question.questions_left(), 1)

        current_question = self.answerpaper_single_question.add_completed_question(
            self.question4.id
        )


        # Then
        self.assertEqual(
            self.answerpaper_single_question.questions_answered.all()[0],
            self.question4
        )
        self.assertEqual(self.answerpaper_single_question.questions_left(), 0)
        self.assertIsNotNone(current_question)
        self.assertEqual(current_question.summary, "Q4")

        # When
        next_question = self.answerpaper_single_question.next_question(
            self.question4.id
        )

        # Then
        self.assertEqual(self.answerpaper_single_question.questions_left(), 0)
        self.assertIsNotNone(next_question)
        self.assertEqual(next_question.summary, "Q4")

        # When
        current_question = self.answerpaper_single_question.get_current_question(
            self.answerpaper_single_question.questions.all()
        )

        # Then
        self.assertEqual(self.answerpaper_single_question.questions_left(), 0)
        self.assertIsNotNone(current_question)
        self.assertEqual(current_question.summary, "Q4")

    def test_validate_and_regrade_mcc_correct_answer(self):
        # Given
        mcc_answer = [str(self.mcc_based_testcase.id)]
        self.answer = Answer(question=self.question3,
                             answer=mcc_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(mcc_answer,
                                                  self.question3, json_data
                                                  )

        # Then
        self.assertTrue(result['success'])
        self.assertEqual(result['error'], ['Correct answer'])
        self.answer.correct = True
        self.answer.marks = 1

        # Given
        self.answer.correct = True
        self.answer.marks = 1

        self.answer.answer = ['a', 'b']
        self.answer.save()

        # When
        details = self.answerpaper.regrade(self.question3.id)

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question3).last()
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_validate_and_regrade_code_correct_answer(self):
        # Given
        # Start code server
        
        user_answer = dedent("""\
                                def add(a,b):
                                    return a+b
                             """)
        self.answer = Answer(question=self.question1,
                             answer=user_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)
        user = self.answerpaper.user

        # When
        json_data = self.question1.consolidate_answer_data(user_answer,
                                                          user
                                                          )
        get_result = self.answerpaper.validate_answer(user_answer,
                                                      self.question1,
                                                      json_data,
                                                      self.answer.id,
                                                      self.SERVER_POOL_PORT
                                                      )
        url = 'http://localhost:%s' % self.SERVER_POOL_PORT
        check_result = get_result_from_code_server(url,get_result['uid'],
                                                   block=True
                                                   )
        result = json.loads(check_result.get('result'))

        # Then
        self.assertTrue(result['success'])
        self.answer.correct = True
        self.answer.marks = 1

        # Regrade
        # Given
        self.answer.correct = True
        self.answer.marks = 1

        self.answer.answer = dedent("""
                                    def add(a,b):
                                        return a-b
                                    """)
        self.answer.save()

        # When
        details = self.answerpaper.regrade(self.question1.id,
                                           self.SERVER_POOL_PORT
                                           )

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question1
                                                      ).last()
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_validate_and_regrade_mcq_correct_answer(self):
        # Given
        mcq_answer = str(self.mcq_based_testcase.id)
        self.answer = Answer(question=self.question2,
            answer=mcq_answer,
        )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(mcq_answer,
                                                  self.question2, json_data
                                                  )

        # Then
        self.assertTrue(result['success'])
        self.answer.correct = True
        self.answer.marks = 1

        # Given
        self.answer.correct = True
        self.answer.marks = 1

        self.answer.answer = 'b'
        self.answer.save()

        # When
        details = self.answerpaper.regrade(self.question2.id)

        # Then
        self.answer = self.answerpaper.answers.filter(question=self.question2).last()
        self.assertTrue(details[0])
        self.assertEqual(self.answer.marks, 0)
        self.assertFalse(self.answer.correct)

    def test_mcq_incorrect_answer(self):
        # Given
        mcq_answer = 'b'
        self.answer = Answer(question=self.question2,
            answer=mcq_answer,
        )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(mcq_answer,
                                                  self.question2, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])

    def test_mcc_incorrect_answer(self):
        # Given
        mcc_answer = ['b']
        self.answer = Answer(question=self.question3,
                             answer=mcc_answer,
                             )
        self.answer.save()
        self.answerpaper.answers.add(self.answer)

        # When
        json_data = None
        result = self.answerpaper.validate_answer(mcc_answer,
                                                  self.question3, json_data
                                                  )

        # Then
        self.assertFalse(result['success'])

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
        self.assertEqual(current_question.summary, "Question1")
        # Test completed_question() method of Answer Paper

        question = self.answerpaper.add_completed_question(self.question1.id)
        self.assertIsNotNone(question)
        self.assertEqual(self.answerpaper.questions_left(), 2)

        # Test next_question() method of Answer Paper
        current_question = self.answerpaper.current_question()
        self.assertEqual(current_question.summary, "Question2")

        # When
        next_question_id = self.answerpaper.next_question(current_question.id)

        # Then
        self.assertTrue(next_question_id is not None)
        self.assertEqual(next_question_id.summary, "Question3")

        # Given, here question is already answered
        current_question_id = self.question1.id

        # When
        next_question_id = self.answerpaper.next_question(current_question_id)

        # Then
        self.assertTrue(next_question_id is not None)
        self.assertEqual(next_question_id.summary, "Question2")

        # Given, wrong question id
        current_question_id = 12

        # When
        next_question_id = self.answerpaper.next_question(current_question_id)

        # Then
        self.assertTrue(next_question_id is not None)
        self.assertEqual(next_question_id.summary, "Question1")

        # Given, last question in the list
        current_question_id = self.question3.id

        # When
        next_question_id = self.answerpaper.next_question(current_question_id)

        # Then
        self.assertTrue(next_question_id is not None)

        self.assertEqual(next_question_id.summary, "Question1")

        # Test get_questions_answered() method
        # When
        questions_answered = self.answerpaper.get_questions_answered()

        # Then
        self.assertEqual(questions_answered.count(), 1)
        self.assertSequenceEqual(questions_answered, [self.questions[0]])

        # When
        questions_unanswered = self.answerpaper.get_questions_unanswered()

        # Then
        self.assertEqual(questions_unanswered.count(), 2)
        self.assertSequenceEqual(questions_unanswered,
                                 [self.questions[1], self.questions[2]])

        # Test completed_question and next_question
        # When all questions are answered

        current_question = self.answerpaper.add_completed_question(
            self.question2.id
        )

        # Then
        self.assertEqual(self.answerpaper.questions_left(), 1)
        self.assertIsNotNone(current_question)
        self.assertEqual(current_question.summary, "Question3")

        # When
        current_question = self.answerpaper.add_completed_question(
                                            self.question3.id
                                            )

        # Then
        self.assertEqual(self.answerpaper.questions_left(), 0)
        self.assertIsNotNone(current_question)
        self.assertTrue(current_question == self.answerpaper.questions.all()[0])

        # When
        next_question_id = self.answerpaper.next_question(current_question_id)

        # Then
        all_questions = self.questions.all()
        self.assertTrue(next_question_id == all_questions[0])

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
        current_time = timezone.now()
        self.answerpaper.set_end_time(current_time)
        self.assertEqual(self.answerpaper.end_time,current_time)

    def test_get_question_answer(self):
        """ Test get_question_answer() method of Answer Paper"""
        answered = self.answerpaper.get_question_answers()
        first_answer = list(answered.values())[0][0]
        first_answer_obj = first_answer['answer']
        self.assertEqual(first_answer_obj.answer, 'Demo answer')
        self.assertTrue(first_answer_obj.correct)
        self.assertEqual(len(answered), 2)

    def test_is_answer_correct(self):
        self.assertTrue(self.answerpaper.is_answer_correct(self.questions[0]))
        self.assertFalse(self.answerpaper.is_answer_correct(self.questions[1]))

    def test_get_previous_answers(self):
        answers = self.answerpaper.get_previous_answers(self.questions[0])
        self.assertEqual(answers.count(), 2)
        self.assertTrue(answers[0], self.answer_right)
        answers = self.answerpaper.get_previous_answers(self.questions[1])
        self.assertEqual(answers.count(), 1)
        self.assertTrue(answers[0], self.answer_wrong)

    def test_set_marks(self):
        self.answer_wrong.set_marks(0.5)
        self.assertEqual(self.answer_wrong.marks, 0.5)
        self.answer_wrong.set_marks(10.0)
        self.assertEqual(self.answer_wrong.marks, 1.0)

    def test_get_latest_answer(self):
        latest_answer = self.answerpaper.get_latest_answer(self.question1.id)
        self.assertEqual(latest_answer.id, self.answer1.id)
        self.assertEqual(latest_answer.answer, "answer1")

    def test_shuffle_questions(self):
        ques_set_1 = self.user1_answerpaper.get_all_ordered_questions()
        ques_set_2 = self.user2_answerpaper.get_all_ordered_questions()
        self.assertFalse(ques_set_1 == ques_set_2)

    def test_validate_current_question(self):
        self.user2_answerpaper2.questions_unanswered.remove(*self.questions)
        self.assertEqual(self.user2_answerpaper2.current_question(),
                         self.question1)


###############################################################################
class CourseTestCases(unittest.TestCase):
    def setUp(self):
        self.course = Course.objects.get(name="Python Course")
        self.creator = User.objects.get(username="demo_user")
        self.template_course_user = User.objects.get(username="demo_user4")
        self.student1 = User.objects.get(username="demo_user2")
        self.student2 = User.objects.get(username="demo_user3")
        self.quiz1 = Quiz.objects.get(description='demo quiz 1')
        self.quiz2 = Quiz.objects.get(description='demo quiz 2')
        self.questions = Question.objects.filter(active=True)

        # create courses with disabled enrollment
        self.enroll_request_course = Course.objects.create(
            name="Enrollment Request Course With Enrollment Disabled",
            enrollment="Enroll Request",
            creator=self.creator,
            start_enroll_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                tzinfo=pytz.utc
            ),
            end_enroll_time=datetime(2015, 11, 9, 10, 8, 15, 0,
               tzinfo=pytz.utc
            ),
        )
        self.open_course = Course.objects.create(
            name="Open Course With Enrollment Disabled",
            enrollment="Open Course",
            creator=self.creator,
            start_enroll_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                tzinfo=pytz.utc
            ),
            end_enroll_time=datetime(2015, 11, 9, 10, 8, 15, 0,
               tzinfo=pytz.utc
            ),
        )

        # create a course that will be cloned
        self.template_course = Course.objects.create(
            name="Template Course to clone",
            enrollment="Open Course",
            creator=self.creator,
            start_enroll_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                tzinfo=pytz.utc
            ),
            end_enroll_time=datetime(2015, 11, 9, 10, 8, 15, 0,
               tzinfo=pytz.utc
            ),
        )

        self.template_quiz = Quiz.objects.create(
            start_date_time=datetime(2014, 10, 9, 10, 8, 15, 0,
                tzinfo=pytz.utc
            ),
            end_date_time=datetime(2015, 10, 9, 10, 8, 15, 0,
                tzinfo=pytz.utc
            ),
            duration=30,
            active=False,
            attempts_allowed=-1,
            time_between_attempts=0,
            description='template quiz 1',
            pass_criteria=40,
            language='Python',
            course=self.template_course,
            instructions="Demo Instructions"
        )

        self.template_question_paper = QuestionPaper.objects.create(
            quiz=self.template_quiz,
            total_marks=0.0,
            shuffle_questions=True
        )

        self.template_question_paper.fixed_questions.add(self.questions[1],
            self.questions[2],
            self.questions[3]
        )

        self.template_quiz2 = Quiz.objects.create(
            start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            duration=30,
            active=True,
            attempts_allowed=1,
            time_between_attempts=0,
            description='template quiz 2',
            pass_criteria=0,
            language='Python',
            prerequisite=self.template_quiz,
            course=self.template_course,
            instructions="Demo Instructions"
        )

        self.template_question_paper2 = QuestionPaper.objects.create(
            quiz=self.template_quiz2,
            total_marks=0.0,
            shuffle_questions=True
        )

        self.template_question_paper2.fixed_questions.add(self.questions[1],
            self.questions[2],
            self.questions[3]
        )

    def test_create_duplicate_course(self):
        """ Test create_duplicate_course method of course """
        # create a duplicate course
        cloned_course = self.template_course.create_duplicate_course(
            self.template_course_user
        )
        self.assertEqual(cloned_course.name,
            'Copy Of Template Course to clone')
        self.assertEqual(cloned_course.enrollment,
            self.template_course.enrollment
        )
        self.assertEqual(cloned_course.creator,
            self.template_course_user
        )
        self.assertEqual(cloned_course.start_enroll_time,
            self.template_course.start_enroll_time
        )
        self.assertEqual(cloned_course.end_enroll_time,
            self.template_course.end_enroll_time
        )

        # check if attributes are same
        cloned_course_dict = model_to_dict(cloned_course,
            fields=[field.name for field in cloned_course._meta.fields \
                if field.name != 'id']
        )
        template_course_dict = model_to_dict(self.template_course,
            fields=[field.name for field in self.template_course._meta.fields \
                if field.name != 'id']
        )
        self.assertEqual(cloned_course_dict, template_course_dict)

        # get duplicate quiz associated with duplicate course
        cloned_quiz = cloned_course.quiz_set.all()[0]

        self.assertEqual(cloned_quiz.start_date_time,
            self.template_quiz.start_date_time
        )
        self.assertEqual(cloned_quiz.end_date_time,
            self.template_quiz.end_date_time
        )
        self.assertEqual(cloned_quiz.duration,
            self.template_quiz.duration
        )
        self.assertEqual(cloned_quiz.active,
            self.template_quiz.active
        )
        self.assertEqual(cloned_quiz.attempts_allowed,
            self.template_quiz.attempts_allowed
        )
        self.assertEqual(cloned_quiz.time_between_attempts,
            self.template_quiz.time_between_attempts
        )
        self.assertEqual(cloned_quiz.description,
            'Copy Of template quiz 1'
        )
        self.assertEqual(cloned_quiz.pass_criteria,
            self.template_quiz.pass_criteria
        )
        self.assertEqual(cloned_quiz.language,
            self.template_quiz.language
        )
        self.assertEqual(cloned_quiz.course,
            cloned_course
        )
        self.assertEqual(cloned_quiz.instructions,
            self.template_quiz.instructions
        )

        # Get duplicate questionpaper associated with duplicate quiz
        cloned_qp = cloned_quiz.questionpaper_set.all()[0]

        self.assertEqual(cloned_qp.quiz, cloned_quiz)
        self.assertEqual(cloned_qp.total_marks,
            self.template_question_paper.total_marks
        )
        self.assertEqual(cloned_qp.shuffle_questions,
            self.template_question_paper.shuffle_questions
        )

        for q in cloned_qp.fixed_questions.all():
            self.assertIn(q, self.template_question_paper.fixed_questions.all())

        # get second duplicate quiz associated with duplicate course
        cloned_quiz = cloned_course.quiz_set.all()[1]

        self.assertEqual(cloned_quiz.start_date_time,
            self.template_quiz2.start_date_time
        )
        self.assertEqual(cloned_quiz.end_date_time,
            self.template_quiz2.end_date_time
        )
        self.assertEqual(cloned_quiz.duration,
            self.template_quiz2.duration
        )
        self.assertEqual(cloned_quiz.active,
            self.template_quiz2.active
        )
        self.assertEqual(cloned_quiz.attempts_allowed,
            self.template_quiz2.attempts_allowed
        )
        self.assertEqual(cloned_quiz.time_between_attempts,
            self.template_quiz2.time_between_attempts
        )
        self.assertEqual(cloned_quiz.description,
            'Copy Of template quiz 2'
        )
        self.assertEqual(cloned_quiz.pass_criteria,
            self.template_quiz2.pass_criteria
        )
        self.assertEqual(cloned_quiz.language,
            self.template_quiz2.language
        )
        self.assertEqual(cloned_quiz.course,
            cloned_course
        )
        self.assertEqual(cloned_quiz.instructions,
            self.template_quiz2.instructions
        )

        # Get second duplicate questionpaper associated with duplicate quiz
        cloned_qp = cloned_quiz.questionpaper_set.all()[0]

        self.assertEqual(cloned_qp.quiz, cloned_quiz)
        self.assertEqual(cloned_qp.total_marks,
            self.template_question_paper2.total_marks
        )
        self.assertEqual(cloned_qp.shuffle_questions,
            self.template_question_paper2.shuffle_questions
        )

        for q in cloned_qp.fixed_questions.all():
            self.assertIn(q, self.template_question_paper2.fixed_questions.all())


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
        self.assertSequenceEqual(self.course.get_quizzes(),
                                     [self.quiz1, self.quiz2])

    def test_add_teachers(self):
        """ Test to add teachers to a course"""
        self.course.add_teachers(self.student1, self.student2)
        self.assertSequenceEqual(self.course.get_teachers(),
                                     [self.student1, self.student2])

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

    def test_create_trial_course(self):
        """Test to check if trial course is created"""
        trial_course = Course.objects.create_trial_course(self.creator)
        self.assertEqual(trial_course.name, "trial_course")
        self.assertEqual(trial_course.enrollment, "open")
        self.assertTrue(trial_course.active)
        self.assertEqual(self.creator, trial_course.creator)
        self.assertIn(self.creator, trial_course.students.all())
        self.assertTrue(trial_course.is_trial)

    def test_enabled_enrollment_for_course(self):
        """Test to check enrollment is closed for open course"""
        self.assertTrue(self.course.is_active_enrollment())

    def test_disabled_enrollment_for_open_course(self):
        """Test to check enrollment is closed for open course"""
        self.assertFalse(self.open_course.is_active_enrollment())

    def test_disabled_enrollment_for_enroll_request_course(self):
        """Test to check enrollment is closed for open course"""
        self.assertFalse(self.enroll_request_course.is_active_enrollment())



###############################################################################
class TestCaseTestCases(unittest.TestCase):
    def setUp(self):
        self.user = User.objects.get(username="demo_user")
        self.question1 = Question(summary='Demo question 1',
            language='Python',
            type='Code',
            active=True,
            description='Write a function',
            points=1.0,
            user=self.user,
            snippet='def myfunc()'
        )
        self.question2 = Question(summary='Demo question 2',
             language='Python',
             type='Code',
             active=True,
             description='Write to standard output',
             points=1.0,
             user=self.user,
             snippet='def myfunc()'
        )
        self.question1.save()
        self.question2.save()
        self.assertion_testcase = StandardTestCase(
            question=self.question1,
            test_case='assert myfunc(12, 13) == 15',
            type='standardtestcase'
        )
        self.stdout_based_testcase = StdIOBasedTestCase(
            question=self.question2,
            expected_output='Hello World',
            type='standardtestcase'

        )
        self.assertion_testcase.save()
        self.stdout_based_testcase.save()
        answer_data = {'metadata': { 'user_answer': 'demo_answer',
                        'language': 'python',
                        'partial_grading': False
                        },
                    'test_case_data': [{'test_case': 'assert myfunc(12, 13) == 15',
                        'test_case_type': 'standardtestcase',
                        'test_case_args': "",
                        'weight': 1.0
                        }]
                    }
        self.answer_data_json = json.dumps(answer_data)

    def test_assertion_testcase(self):
        """ Test question """
        self.assertEqual(self.assertion_testcase.question, self.question1)
        self.assertEqual(self.assertion_testcase.test_case,
                             'assert myfunc(12, 13) == 15')

    def test_stdout_based_testcase(self):
        """ Test question """
        self.assertEqual(self.stdout_based_testcase.question, self.question2)
        self.assertEqual(self.stdout_based_testcase.expected_output,
            'Hello World'
        )

    def test_consolidate_answer_data(self):
        """ Test consolidate answer data model method """
        result = self.question1.consolidate_answer_data(
            user_answer="demo_answer"
        )
        actual_data = json.loads(result)
        exp_data = json.loads(self.answer_data_json)
        self.assertEqual(actual_data['metadata']['user_answer'], exp_data['metadata']['user_answer'])
        self.assertEqual(actual_data['test_case_data'], exp_data['test_case_data'])


class AssignmentUploadTestCases(unittest.TestCase):
    def setUp(self):
        self.user1 = User.objects.get(username="demo_user")
        self.user1.first_name = "demo"
        self.user1.last_name = "user"
        self.user1.save()
        self.user2 = User.objects.get(username="demo_user3")
        self.user2.first_name = "demo"
        self.user2.last_name = "user3"
        self.user2.save()
        self.quiz = Quiz.objects.get(description="demo quiz 1")

        self.questionpaper = QuestionPaper.objects.create(quiz=self.quiz,
            total_marks=0.0,
            shuffle_questions=True
        )
        self.question = Question.objects.create(summary='Assignment',
            language='Python',
            type='upload',
            active=True,
            description='Upload a file',
            points=1.0,
            snippet='',
            user=self.user1
        )
        self.questionpaper.fixed_question_order = "{0}".format(self.question.id)
        self.questionpaper.fixed_questions.add(self.question)
        file_path1 = os.path.join(tempfile.gettempdir(), "upload1.txt")
        file_path2 = os.path.join(tempfile.gettempdir(), "upload2.txt")
        self.assignment1 = AssignmentUpload.objects.create(user=self.user1,
            assignmentQuestion=self.question, assignmentFile=file_path1,
            question_paper=self.questionpaper
            )
        self.assignment2 = AssignmentUpload.objects.create(user=self.user2,
            assignmentQuestion=self.question, assignmentFile=file_path2,
            question_paper=self.questionpaper
            )

    def test_get_assignments_for_user_files(self):
        assignment_files, file_name = AssignmentUpload.objects.get_assignments(
                                    self.questionpaper, self.question.id,
                                    self.user1.id
                                    )
        self.assertIn("upload1.txt", assignment_files[0].assignmentFile.name)
        self.assertEqual(assignment_files[0].user, self.user1)
        actual_file_name = self.user1.get_full_name().replace(" ", "_")
        file_name = file_name.replace(" ", "_")
        self.assertEqual(file_name, actual_file_name)

    def test_get_assignments_for_quiz_files(self):
        assignment_files, file_name = AssignmentUpload.objects.get_assignments(
                                    self.questionpaper
                                    )
        files = [os.path.basename(file.assignmentFile.name)
                 for file in assignment_files]
        question_papers = [file.question_paper for file in assignment_files]
        self.assertIn("upload1.txt", files)
        self.assertIn("upload2.txt", files)
        self.assertEqual(question_papers[0].quiz, self.questionpaper.quiz)
        actual_file_name = self.quiz.description.replace(" ", "_")
        file_name = file_name.replace(" ", "_")
        self.assertIn(actual_file_name, file_name)
