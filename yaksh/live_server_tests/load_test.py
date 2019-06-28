from threading import Thread
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User, Group, Permission
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

        app_label = 'yaksh'
        group_name = 'moderator'

        try:
            cls.group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            cls.group = Group(name=group_name)
            cls.group.save()
            # Get the models for the given app
            content_types = ContentType.objects.filter(app_label=app_label)
            # Get list of permissions for the models
            permission_list = Permission.objects.filter(
                content_type__in=content_types)
            cls.group.permissions.add(*permission_list)
            cls.group.save()

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
