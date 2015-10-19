from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt

from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer
from restless.resources import skip_prepare

from yaksh.models import Quiz, Question, QuestionPaper, Answer
from yaksh.xmlrpc_clients import code_server
from yaksh.views import validate_answer

import json

class QuestionResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'summary': 'summary',
        'description': 'description',
        'points': 'points',
        'test': 'test',
        'options': 'options',
        'language': 'language',
        'type': 'type',
        'active': 'active',
        'snippet': 'snippet',
    })

    def is_authenticated(self):
        ##@@ Access open for all, Need to modify    
        return True

    def create(self):
        return Question.objects.create(summary=self.data['summary'],
                description=self.data['description'],
                points=self.data['points'],
                test=self.data['test'],
                options=self.data['options'],
                language=self.data['language'], # Currently supports python, c, cpp, scilab, java, bash
                active=self.data['active'], # True/False
                type=self.data['type'], # mcq/mcc/code/upload
                )

    def detail(self, pk):
        return Question.objects.get(id=pk)

    def list(self):
        return Question.objects.all()

    def delete(self, pk):
        Question.objects.get(id=pk).delete()


class QuestionPaperResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'quiz': 'quiz',
        'fixed_question': 'fixed_question',
        'total_marks': 'total_marks'
    })

    def is_authenticated(self):
        ##@@ Access open for all, Need to modify    
        return True

    def create(self):
        q = QuestionPaper.objects.create(quiz=self.data['quiz_id'],
                total_marks=self.data['total_marks'])

        q.fixed_questions.add(*self._get_questions(*self.data['fixed_question_id']))  # fixed_question_id will be a list of Question ID
        q.save()
        return q

    def detail(self, pk):
        return QuestionPaper.objects.get(id=pk)

    def list(self):
        return QuestionPaper.objects.all()

    def delete(self, pk):
        QuestionPaper.objects.get(id=pk).delete()

    def _get_questions(self, *keys):
        return [Question.objects.get(id=k) for k in keys]


class QuizResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'id': 'id',
        'duration': 'duration',
        'description': 'description',
        'pass_criteria': 'pass_criteria',
        'language': 'language',
        'attempts_allowed': 'attempts_allowed',
        'time_between_attempts': 'time_between_attempts'
    })

    def is_authenticated(self):
        ##@@ Access open for all, Need to modify    
        return True

    def create(self):
        return Quiz.objects.create(duration=self.data[duration],
                 description=self.data[description],
                 pass_criteria=self.data[pass_criteria],
                 language=self.data[language], # Currently supports python, c, cpp, scilab, java, bash
                 attempts_allowed=self.data[attempts_allowed], # 1,2,3,4,5, -1(Infinite)
                 time_between_attempts=self.data[time_between_attempts] # In days: 0-400,
                )

    def detail(self, pk):
        return Quiz.objects.get(id=pk)

    def list(self):
        return Quiz.objects.all()

    def delete(self, pk):
        Quiz.objects.get(id=pk).delete()


class AnswerResource(DjangoResource):
    def __init__(self, *args, **kwargs):
        super(AnswerResource, self).__init__(*args, **kwargs)

        # Add on a new top-level key, then define what HTTP methods it
        # listens on & what methods it calls for them.
        self.http_methods.update({
            'evaluate_answer': {
                'POST': 'evaluate_answer',
            }
        })

    preparer = FieldsPreparer(fields={
        'id': 'id',
        'answer': 'answer',
        'marks': 'marks',
        'question': 'question.id',
    })

    def is_authenticated(self):
        ##@@ Access open for all, Need to modify    
        return True

    def create(self):
        return Answer.objects.create(answer=self.data['answer'],
                marks=self._get_question(self.data['question_id']).points,
                question=self._get_question(self.data['question_id'])
            )

    def detail(self, pk):
        return Answer.objects.get(id=pk)

    def list(self):
        return Answer.objects.all()

    def delete(self, pk):
            Answer.objects.get(id=pk).delete()

    # POST with the info question_id & user_answer
    @skip_prepare
    def evaluate_answer(self):
        print "HELLO", self.data['user_answer']
        question = self._get_question(self.data['question_id'])
        json_data = question.consolidate_answer_data(test_cases=None, user_answer=self.data['user_answer'])
        return json.dumps({'correct': self._evaluate_answer(self.data['user_answer'], question, json_data=None)})

    def _evaluate_answer(self, user_answer, question, json_data=None):
        """
            Checks whether the answer submitted by the user is right or wrong.
            If right then returns correct = True, success and
            message = Correct answer.
            success is True for MCQ's and multiple correct choices because
            only one attempt are allowed for them.
            For code questions success is True only if the answer is correct.
        """

        result = {'success': True, 'error': ''}
        correct = False

        print "MOKA",user_answer
        if user_answer is not None:
            if question.type == 'mcq':
                if user_answer.strip() == question.test.strip():
                    correct = True
                    message = 'Correct answer'
            elif question.type == 'mcc':
                answers = set(question.test.splitlines())
                if set(user_answer) == answers:
                    correct = True
                    message = 'Correct answer'
            elif question.type == 'code':
                # user_dir = get_user_dir(user)
                json_result = code_server.run_code(question.language, json_data, '/tmp')
                result = json.loads(json_result)
                if result.get('success'):
                    correct = True

        return correct


    @classmethod
    def urls(cls, name_prefix=None):
        urlpatterns = super(AnswerResource, cls).urls(name_prefix=name_prefix)
        return urlpatterns + patterns('',
            url(r'^evaluate_answer/$', csrf_exempt(cls.as_view('evaluate_answer')), name=cls.build_url_name('evaluate_answer', name_prefix)),
        )

    def _get_question(self, pk):
        return Question.objects.get(id=pk)
