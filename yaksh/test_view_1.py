from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group,User
from yaksh.models import (Question,EasyStandardTestCase)


class QuestionForm_test(TestCase):
	def setUp(self):
		self.client=Client()
		self.mod_group = Group.objects.create(name='moderator')
		self.user_plaintext_pass = 'demo'
		self.user = User.objects.create_user(
				username='demo_user',
				password=self.user_plaintext_pass,
				first_name='first_name',
				last_name='last_name',
				email='demo@test.com'
			)
		self.mod_group.user_set.add(self.user)
		self.post_data={
			'summary':'testing',
			'language':'python',
			'type':'code',
			'description':'add',
			'min_time':0,
			'points':1,
			'form-TOTAL_FORMS':0,
			'form-INITIAL_FORMS':0,
			'standardtestcase_set-TOTAL_FORMS':0,
			'standardtestcase_set-INITIAL_FORMS':0,
			'standardtestcase_set-MIN_NUM_FORMS':0,
			'standardtestcase_set-MAX_NUM_FORMS':0,
			'easystandardtestcase_set-TOTAL_FORMS':0,
			'easystandardtestcase_set-INITIAL_FORMS':0,
			'easystandardtestcase_set-MIN_NUM_FORMS':0,
			'easystandardtestcase_set-MAX_NUM_FORMS':0,
			'stdiobasedtestcase_set-TOTAL_FORMS':0,
			'stdiobasedtestcase_set-INITIAL_FORMS':0,
			'stdiobasedtestcase_set-MIN_NUM_FORMS':0,
			'stdiobasedtestcase_set-MAX_NUM_FORMS':0,
			'mcqtestcase_set-TOTAL_FORMS':0,
			'mcqtestcase_set-INITIAL_FORMS':0,
			'mcqtestcase_set-MIN_NUM_FORMS':0,
			'mcqtestcase_set-MAX_NUM_FORMS':0,
			'hooktestcase_set-TOTAL_FORMS':0,
			'hooktestcase_set-INITIAL_FORMS':0,
			'hooktestcase_set-MIN_NUM_FORMS':0,
			'hooktestcase_set-MAX_NUM_FORMS':0,
			'integertestcase_set-TOTAL_FORMS':0,
			'integertestcase_set-INITIAL_FORMS':0,
			'integertestcase_set-MIN_NUM_FORMS':0,
			'integertestcase_set-MAX_NUM_FORMS':0,
			'stringtestcase_set-TOTAL_FORMS':0,
			'stringtestcase_set-INITIAL_FORMS':0,
			'stringtestcase_set-MIN_NUM_FORMS':0,
			'stringtestcase_set-MAX_NUM_FORMS':0,
			'floattestcase_set-TOTAL_FORMS':0,
			'floattestcase_set-INITIAL_FORMS':0,
			'floattestcase_set-MIN_NUM_FORMS':0,
			'floattestcase_set-MAX_NUM_FORMS':0,

			
		}
		self.post_easystandardtestcase_python={
			'summary':'testing',
			'language':'python',
			'type':'code',
			'description':'add',
			'min_time':0,
			'points':1,
			'form-TOTAL_FORMS':0,
			'form-INITIAL_FORMS':0,
			'standardtestcase_set-TOTAL_FORMS':0,
			'standardtestcase_set-INITIAL_FORMS':0,
			'standardtestcase_set-MIN_NUM_FORMS':0,
			'standardtestcase_set-MAX_NUM_FORMS':0,
			'easystandardtestcase_set-TOTAL_FORMS':1,
			'easystandardtestcase_set-INITIAL_FORMS':0,
			'easystandardtestcase_set-MIN_NUM_FORMS':0,
			'easystandardtestcase_set-MAX_NUM_FORMS':0,
			'easystandardtestcase_set-0-function_name':"add",
			'easystandardtestcase_set-0-operator':'==',
			'easystandardtestcase_set-0-input_vals':"5,5",
			'easystandardtestcase_set-0-output_vals':"10",
			'easystandardtestcase_set-0-type': "easystandardtestcase",
			'stdiobasedtestcase_set-TOTAL_FORMS':0,
			'stdiobasedtestcase_set-INITIAL_FORMS':0,
			'stdiobasedtestcase_set-MIN_NUM_FORMS':0,
			'stdiobasedtestcase_set-MAX_NUM_FORMS':0,
			'hooktestcase_set-TOTAL_FORMS':0,
			'hooktestcase_set-INITIAL_FORMS':0,
			'hooktestcase_set-MIN_NUM_FORMS':0,
			'hooktestcase_set-MAX_NUM_FORMS':0,
			
		}

		self.post_easystandardtestcase_cpp={
			'summary':'testing',
			'language':'c',
			'type':'code',
			'description':'add',
			'min_time':0,
			'points':1,
			'form-TOTAL_FORMS':0,
			'form-INITIAL_FORMS':0,
			'standardtestcase_set-TOTAL_FORMS':0,
			'standardtestcase_set-INITIAL_FORMS':0,
			'standardtestcase_set-MIN_NUM_FORMS':0,
			'standardtestcase_set-MAX_NUM_FORMS':0,
			'easystandardtestcase_set-TOTAL_FORMS':1,
			'easystandardtestcase_set-INITIAL_FORMS':0,
			'easystandardtestcase_set-MIN_NUM_FORMS':0,
			'easystandardtestcase_set-MAX_NUM_FORMS':0,
			'easystandardtestcase_set-0-function_name':"add",
			'easystandardtestcase_set-0-operator':'==',
			'easystandardtestcase_set-0-typeof_var':'int,int',
			'easystandardtestcase_set-0-input_vals':"5,5",
			'easystandardtestcase_set-0-output_vals':"10",
			'easystandardtestcase_set-0-type': "easystandardtestcase",
			'easystandardtestcase_set-0-typeof_output':'int',
			'stdiobasedtestcase_set-TOTAL_FORMS':0,
			'stdiobasedtestcase_set-INITIAL_FORMS':0,
			'stdiobasedtestcase_set-MIN_NUM_FORMS':0,
			'stdiobasedtestcase_set-MAX_NUM_FORMS':0,
			'hooktestcase_set-TOTAL_FORMS':0,
			'hooktestcase_set-INITIAL_FORMS':0,
			'hooktestcase_set-MIN_NUM_FORMS':0,
			'hooktestcase_set-MAX_NUM_FORMS':0,
			
		}

		self.question=Question.objects.create(
			summary='testing',
			language='python',
			type='code',
			description='add',user=self.user
		)

	def test_add_question_get(self):
		self.client.login(username=self.user.username,password=self.user_plaintext_pass)
		response=self.client.get(reverse('yaksh:add_question'))
		self.assertEqual(response.status_code,200)

	def test_add_question_post(self):
		self.client.login(username=self.user.username,password=self.user_plaintext_pass)
		response=self.client.post(
			reverse('yaksh:add_question', kwargs={'question_id':self.question.id}),
			data=self.post_data)

	def test_add_question_easystandardtestcase_python(self):
		self.client.login(username=self.user.username,password=self.user_plaintext_pass)
		response=self.client.post(
				reverse('yaksh:add_question',kwargs={'question_id':self.question.id}),
				data=self.post_easystandardtestcase_python
			)
		easy_id=self.question.testcase_set.get().easystandardtestcase
		self.assertEqual(easy_id.function_name,'add')
		self.assertEqual(easy_id.input_vals,'5,5')
		self.assertEqual(easy_id.output_vals,'10')
		self.assertEqual(easy_id.test_case,'assert add(5,5)==10')


	def test_add_question_easystandardtestcase_cpp(self):
		self.client.login(username=self.user.username,password=self.user_plaintext_pass)
		response=self.client.post(
				reverse('yaksh:add_question',kwargs={'question_id':self.question.id}),
				data=self.post_easystandardtestcase_cpp
			)
		easy_id=self.question.testcase_set.get().easystandardtestcase
		self.assertEqual(easy_id.function_name,'add')
		self.assertEqual(easy_id.input_vals,'5,5')
		self.assertEqual(easy_id.output_vals,'10')
		self.assertEqual(easy_id.typeof_var,'int,int')
		self.assertEqual(easy_id.typeof_output,'int')
		self.assertEqual(easy_id.test_case,'#include <stdio.h>\n#include <stdlib.h>\n#include<assert.h>\n\nextern int add(int,int);\n\nint main(void)\n{\n\tint result,output;\n\tresult = 10;\n\tassert(result == add(5,5));\n\n}\n\t\t')

