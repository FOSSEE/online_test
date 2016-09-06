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
from django.core.management import call_command


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

        call_command('create_demo_course')

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
        quiz_name = "Demo_quiz"
        selenium_test = SeleniumTest(url=url, quiz_name=quiz_name)
        selenium_test.run_load_test(url=url, username='demo_student', password='demo_student')
