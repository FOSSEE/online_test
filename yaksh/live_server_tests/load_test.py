from threading import Thread
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

# Local imports
from yaksh.models import User, Profile, Course, create_group
from yaksh.code_server import ServerPool
from yaksh import settings
from .selenium_test import SeleniumTest


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

        app_label = 'yaksh'
        group_name = 'moderator'
        cls.group = create_group(group_name, app_label)

        cls.demo_student = User.objects.create_user(
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
            username='demo_mod',
            password='demo_mod',
            email='demo_mod@test.com'
        )
        cls.demo_mod_profile = Profile.objects.create(
            user=cls.demo_mod,
            roll_number=0, institute='IIT',
            department='Chemical', position='Moderator',
            is_moderator=True
        )

        course_obj = Course()
        course_obj.create_demo(cls.demo_mod)
        cls.demo_course = Course.objects.get(id=1)

        cls.demo_course.students.add(cls.demo_student)

    @classmethod
    def tearDownClass(cls):
        cls.demo_student.delete()
        cls.demo_student_profile.delete()
        cls.demo_mod.delete()
        cls.demo_mod_profile.delete()
        cls.demo_course.delete()
        cls.group.delete()

        cls.code_server_pool.stop()
        cls.code_server_thread.join()

        super(YakshSeleniumTests, cls).tearDownClass()

    def test_load(self):
        url = '%s%s' % (self.live_server_url, '/exam/login/')
        quiz_name = "Yaksh Demo quiz"
        module_name = "Demo Module"
        course_name = "Yaksh Demo course"
        selenium_test = SeleniumTest(url=url, quiz_name=quiz_name,
                                     module_name=module_name,
                                     course_name=course_name)
        selenium_test.run_load_test(
            url=url, username='demo_student', password='demo_student'
        )
