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

from yaksh.code_server import ServerPool
from yaksh import settings


class YakshSeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(YakshSeleniumTests, cls).setUpClass()
        # setup a demo code server
        settings.code_evaluators['python']['standardtestcase'] = \
            "yaksh.python_assertion_evaluator.PythonAssertionEvaluator"
        settings.code_evaluators['c']['standardtestcase'] = \
            "yaksh.cpp_code_evaluator.CppCodeEvaluator"
        settings.code_evaluators['bash']['standardtestcase'] = \
            "yaksh.bash_code_evaluator.BashCodeEvaluator"
        settings.SERVER_POOL_PORT = 53578
        code_server_pool = ServerPool(ports=settings.SERVER_PORTS, pool_port=settings.SERVER_POOL_PORT)
        cls.code_server_pool = code_server_pool
        cls.code_server_thread = t = Thread(target=code_server_pool.run)
        t.start()

        demo_student = User.objects.create_user(username='demo_student',
           password='demo_student',
           email='demo_student@test.com'
        )
        demo_student_profile = Profile.objects.create(user=demo_student,
            roll_number=3, institute='IIT',
            department='Chemical', position='Student'
        )

        demo_mod = User.objects.create_user(username='demo_mod',
           password='demo_mod',
           email='demo_mod@test.com'
        )
        demo_mod_profile = Profile.objects.create(user=demo_mod,
            roll_number=0, institute='IIT',
            department='Chemical', position='Moderator'
        )

        course_obj = Course()
        course_obj.create_demo(demo_mod)
        demo_course = Course.objects.get(id=1)

        demo_course.students.add(demo_student)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        Course.objects.all().delete()

        settings.SERVER_POOL_PORT = 53579

        cls.code_server_pool.stop()
        cls.code_server_thread.join()

        super(YakshSeleniumTests, cls).tearDownClass()

    def test_load(self):
        url = '%s%s' % (self.live_server_url, '/exam/login/')
        quiz_name = "Yaksh Demo quiz"
        selenium_test = SeleniumTest(url=url, quiz_name=quiz_name)
        selenium_test.run_load_test(url=url, username='demo_student', password='demo_student')
