import os
import signal
import subprocess
from datetime import datetime
import pytz
from threading import Thread
from selenium.webdriver.firefox.webdriver import WebDriver

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from yaksh.models import User, Profile, Question, Quiz, Course, QuestionPaper, TestCase
from selenium_test import SeleniumTest

from yaksh.code_server import ServerPool, SERVER_POOL_PORT, SERVER_PORTS
from yaksh import settings
from yaksh.xmlrpc_clients import CodeServerProxy

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

class MySeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(MySeleniumTests, cls).setUpClass()
        # setup a demo code server
        settings.code_evaluators['python']['standardtestcase'] = \
            "yaksh.python_assertion_evaluator.PythonAssertionEvaluator"
        settings.code_evaluators['c']['standardtestcase'] = \
            "yaksh.cpp_code_evaluator.CppCodeEvaluator"
        settings.code_evaluators['bash']['standardtestcase'] = \
            "yaksh.bash_code_evaluator.BashCodeEvaluator"
        code_server_pool = ServerPool(ports=SERVER_PORTS, pool_port=SERVER_POOL_PORT)
        cls.code_server_pool = code_server_pool
        cls.code_server_thread = t = Thread(target=code_server_pool.run)
        t.start()

        # Create set of demo users and profiles
        mod_user = User.objects.create_user(username='yaksh_demo_mod',
                password='yaksh_demo_mod',
                email='yaksh_demo_mod@test.com'
            )
  
        user = User.objects.create_user(username='demo_yaksh_user',
                password='demo_yaksh_user',
                email='demo_yaksh_user@test.com'
            )
        Profile.objects.create(user=user,
                roll_number='demo_rn',
                institute='IIT',
                department='Chemical',
                position='Student'
            )

        # create a course
        course = Course.objects.create(name="Demo Load Course",
               enrollment="Open Course",
               creator=mod_user
            )
        course.students.add(user)

        # create a Quiz
        quiz = Quiz.objects.create(
                start_date_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
                end_date_time=datetime(2199, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
                duration=30, active=True,
                attempts_allowed=1, time_between_attempts=0,
                description='yaksh demo quiz', pass_criteria=0,
                language='Python', prerequisite=None,
                course=course
            )

        # create a question set
        question = Question()
        with open(os.path.join(CUR_DIR, 'test_questions.json'), 'r') as f:
            question_list = f.read()
        question.load_from_json(question_list, mod_user)

        # create question paper
        question_paper = QuestionPaper.objects.create(quiz=quiz,
            total_marks=5,
            shuffle_questions=False
        )
        # add fixed set of questions to the question paper
        question_paper.fixed_questions.add(*Question.objects.all())

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        Course.objects.all().delete()

        cls.code_server_pool.stop()
        cls.code_server_thread.join()

        super(MySeleniumTests, cls).tearDownClass()

    def test_load(self):
        url = '%s%s' % (self.live_server_url, '/exam/login/')
        quiz_name = "yaksh demo quiz"
        selenium_test = SeleniumTest(url=url, quiz_name=quiz_name)
        selenium_test.run_load_test(url=url, username='demo_yaksh_user', password='demo_yaksh_user')
