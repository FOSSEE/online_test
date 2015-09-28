import os, sys

sys.path.append('/home/arj/arj_project/onlinetest/online_test/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "online_test.settings")
from django.conf import settings

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from yaksh.models import Quiz, Question, QuestionPaper, Answer
from yaksh.xmlrpc_clients import code_server
from yaksh.views import validate_answer

class Resource(object):
    def __init__(self, data=None):
        self.data = data

    def _get_quiz(self, pk):
        return Quiz.objects.get(id=pk)

    def _get_questions(self, *keys):
        return [Question.objects.get(id=k) for k in keys]

    def _get_question(self, pk):
        return Question.objects.get(id=pk)

    def authenticate_user(username, password):
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                return True
            else:
                print "Disabled account"
        else:
            return False

class QuestionResource(Resource):
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
        Question.objects.get(id=pk)


class QuestionPaperResource(Resource):
    def create(self):
        q = QuestionPaper.objects.create(quiz=self._get_quiz(self.data['quiz_id']),
                # fixed_questions=self._get_questions(*self.data['fixed_question_id']), # fixed_question_id will be a list of Question ID
                total_marks=self.data['total_marks'])

        q.fixed_questions.add(*self._get_questions(*self.data['fixed_question_id']))
        q.save()
        return q

    def detail(self, pk):
        return QuestionPaper.objects.get(id=pk)

    def list(self):
        return QuestionPaper.objects.all()

    def delete(self, pk):
        QuestionPaper.objects.get(id=pk).delete()


class QuizResource(Resource):
    def create(self):
        return Quiz.objects.create(duration=self.data['duration'],
                 description=self.data['description'],
                 pass_criteria=self.data['pass_criteria'],
                 language=self.data['language'], # Currently supports python, c, cpp, scilab, java, bash
                 attempts_allowed=self.data['attempts_allowed'], # 1,2,3,4,5, -1(Infinite)
                 time_between_attempts=self.data['time_between_attempts'] # In days: 0-400,
                )

    def detail(self, pk):
        return Quiz.objects.get(id=pk)

    def list(self):
        return Quiz.objects.all()

    def delete(self, pk):
        Quiz.objects.get(id=pk)


class AnswerResource(Resource):
    def create(self):
        return Answer.objects.create(answer=self.data['answer'],
                marks=self._get_question(self.data['question_id']).points,
                question=self._get_question(self.data['question_id']))

    def detail(self, pk):
        return Answer.objects.get(id=pk)

    def list(self):
        return Answer.objects.all()

    def delete(self, pk):
        Answer.objects.get(id=pk)

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

        return correct, result

    def evaluate_answer(self, question_id, answer_id):
        question = self._get_question(question_id)
        ans = self.detail(answer_id)
        json_data = question.consolidate_answer_data(test_cases=None, user_answer=ans.answer)
        return self._evaluate_answer(ans.answer, question, json_data=None)
