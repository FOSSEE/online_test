from threading import Thread
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType

# Local imports
from yaksh.models import User, Profile, Course
from yaksh.code_server import ServerPool
from yaksh import settings
from yaksh.live_server_tests.selenium_test import SeleniumTest


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
        code_server_pool = ServerPool(
            n=settings.N_CODE_SERVERS, pool_port=settings.SERVER_POOL_PORT
        )
        cls.code_server_pool = code_server_pool
        cls.code_server_thread = t = Thread(target=code_server_pool.run)
        t.start()

        group_name = 'moderator'

        cls.group = Group.objects.get_or_create(name=group_name)[0]

        if cls.group and isinstance(cls.group, Group):
            print('Moderator group added successfully')

        cls.demo_student = User.objects.create_user(
            first_name="demo_student",
            username='demo_student',
            password='demo_student',
            email='demo_student@test.com'
        )
        cls.demo_student_profile = Profile.objects.create(
            user=cls.demo_student,
            roll_number=3, institute='IIT',
            department='Chemical', position='Student'
        )

        cls.demo_mod = User.objects.create_user(
            first_name="demo_mod",
            username='demo_mod',
            password='demo_mod',
            email='demo_mod@test.com'
        )
        cls.demo_mod_profile = Profile.objects.create(
            user=cls.demo_mod,
            roll_number=0, institute='IIT',
            department='Chemical', position='Moderator',
        )

        cls.demo_mod_profile.is_moderator = True
        cls.demo_mod_profile.save()

    @classmethod
    def tearDownClass(cls):
        cls.demo_student.delete()
        cls.demo_student_profile.delete()
        cls.demo_mod.delete()
        cls.demo_mod_profile.delete()
        cls.group.delete()

        cls.code_server_pool.stop()
        cls.code_server_thread.join()
        super(YakshSeleniumTests, cls).tearDownClass()

    def test_load(self):
        url = '%s%s' % (self.live_server_url, '/exam/login/')
        quiz_name = "demo_quiz"
        module_name = "demo_module"
        course_name = "demo_course"
        selenium_test = SeleniumTest(url=url, quiz_name=quiz_name,
                                     module_name=module_name,
                                     course_name=course_name)
        selenium_test.run_load_test(
            url=url
        )
