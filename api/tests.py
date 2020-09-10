from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from yaksh.models import (
    Question, Quiz, QuestionPaper, QuestionSet,
    AnswerPaper, Course, LearningModule, LearningUnit, StandardTestCase,
    McqTestCase, Profile
)
from api.serializers import (
    QuestionSerializer, QuizSerializer,
    QuestionPaperSerializer, AnswerPaperSerializer
)
from datetime import datetime
import pytz
from textwrap import dedent
from yaksh.settings import SERVER_POOL_PORT
from yaksh.code_server import ServerPool
from yaksh import settings
from threading import Thread
import time
import json


class QuestionListTestCase(TestCase):
    """ Test get all questions and create a new question """

    def setUp(self):
        self.client = APIClient()
        self.username = 'demo'
        self.password = 'demo'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        Question.objects.create(summary='test question 1', language='python',
                                type='mcq', user=self.user)
        Question.objects.create(summary='test question 2', language='python',
                                type='mcq', user=self.user)

    def test_get_all_questions_anonymous(self):
        # When
        response = self.client.get(reverse('api:questions'))
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_questions(self):
        # Given
        questions = Question.objects.filter(user=self.user)
        serializer = QuestionSerializer(questions, many=True)
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:questions'))
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data, serializer.data)

    def test_create_question_invalid_data(self):
        # Given
        data = {'summary': 'Add test question', 'user': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('api:questions'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Question.objects.filter(
                         summary='Add test question').exists())

    def test_create_question_valid_data(self):
        # Given
        data = {'summary': 'Add test question', 'description': 'test',
                'language': 'python', 'type': 'mcq', 'user': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('api:questions'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Question.objects.filter(
                        summary='Add test question').exists())

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Question.objects.all().delete()


class QuestionDetailTestCase(TestCase):
    """ Test get, update or delete a question """

    def setUp(self):
        self.client = APIClient()
        self.username = 'demo'
        self.password = 'demo'
        self.otherusername = 'otheruser'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        self.otheruser = User.objects.create_user(username=self.otherusername,
                                                  password=self.password)
        Question.objects.create(summary='test question', language='python',
                                type='mcq', user=self.user)
        Question.objects.create(summary='delete question', language='python',
                                type='mcq', user=self.user)
        Question.objects.create(summary='Created by other user',
                                language='python', type='mcq',
                                user=self.otheruser)

    def test_get_question_anonymous(self):
        # Given
        question = Question.objects.get(summary='test question')
        # When
        response = self.client.get(reverse('api:question',
                                   kwargs={'pk': question.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_question_invalid_pk(self):
        # Given
        invalid_pk = 3243
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:question',
                                   kwargs={'pk': invalid_pk}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_question(self):
        # Given
        question = Question.objects.get(summary='test question')
        serializer = QuestionSerializer(question)
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:question',
                                   kwargs={'pk': question.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_question_not_own(self):
        # Given
        question = Question.objects.get(summary='Created by other user')
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:question',
                                   kwargs={'pk': question.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edit_question_anonymous(self):
        # Given
        question = Question.objects.get(summary='test question')
        data = {'summary': 'Edited test question', 'description': 'test',
                'language': 'python', 'type': 'mcq', 'user': self.user.id}
        # When
        response = self.client.put(reverse('api:question',
                                   kwargs={'pk': question.id}), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_edit_question_invalid_data(self):
        # Given
        question = Question.objects.get(summary='test question')
        data = {'summary': 'Edited test question', 'user': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(reverse('api:question',
                                   kwargs={'pk': question.id}), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_question(self):
        # Given
        question = Question.objects.get(summary='test question')
        data = {'summary': 'Edited test question', 'description': 'test',
                'language': 'python', 'type': 'mcq', 'user': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(reverse('api:question',
                                   kwargs={'pk': question.id}), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question = Question.objects.get(pk=question.pk)
        self.assertEqual(question.summary, 'Edited test question')

    def test_delete_question_anonymous(self):
        # Given
        question = Question.objects.get(summary='delete question')
        # When
        response = self.client.delete(reverse('api:question',
                                      kwargs={'pk': question.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_question_not_own(self):
        # Given
        question = Question.objects.get(summary='Created by other user')
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(reverse('api:question',
                                      kwargs={'pk': question.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Question.objects.filter(pk=question.id).exists())

    def test_delete_question(self):
        # Given
        question = Question.objects.get(summary='delete question')
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(reverse('api:question',
                                      kwargs={'pk': question.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Question.objects.filter(pk=question.id).exists())

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Question.objects.all().delete()


class QuestionPaperListTestCase(TestCase):
    """ Test get all question paper and create a new question paper """

    def setUp(self):
        self.client = APIClient()
        self.username = 'demo'
        self.otherusername = 'otheruser'
        self.password = 'demo'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        self.otheruser = User.objects.create_user(username=self.otherusername,
                                                  password=self.password)
        self.quiz1 = Quiz.objects.create(description='Quiz1',
                                         creator=self.user)
        self.quiz2 = Quiz.objects.create(description='Quiz2',
                                         creator=self.user)
        self.quiz3 = Quiz.objects.create(description='Quiz3',
                                         creator=self.otheruser)
        self.quiz4 = Quiz.objects.create(description='Quiz4',
                                         creator=self.user)
        self.quiz5 = Quiz.objects.create(description='Quiz5',
                                         creator=self.user)
        self.quiz6 = Quiz.objects.create(description='Quiz6',
                                         creator=self.otheruser)
        self.questionpaper = QuestionPaper.objects.create(quiz=self.quiz1)
        self.questionpaper2 = QuestionPaper.objects.create(quiz=self.quiz2)
        QuestionPaper.objects.create(quiz=self.quiz3)

        self.question1 = Question.objects.create(summary='Q1', user=self.user,
                                                 language='python', type='mcq')
        self.question2 = Question.objects.create(summary='Q2', user=self.user,
                                                 language='python', type='mcq')
        self.question3 = Question.objects.create(summary='Q3', user=self.user,
                                                 language='python', type='mcq')
        self.question4 = Question.objects.create(summary='Q4', user=self.user,
                                                 language='python', type='mcq')
        self.question5 = Question.objects.create(summary='Q5',
                                                 user=self.otheruser,
                                                 language='python', type='mcq')
        self.questionset = QuestionSet.objects.create(marks=1, num_questions=1)
        self.questionset.questions.add(self.question3)
        self.questionset.questions.add(self.question4)
        self.questionset.save()
        self.questionpaper.fixed_questions.add(self.question1)
        self.questionpaper.fixed_questions.add(self.question2)
        self.questionpaper.random_questions.add(self.questionset)
        self.questionpaper.save()
        self.questionpaper.update_total_marks()

    def test_get_all_questionpapers_anonymous(self):
        # When
        response = self.client.get(reverse('api:questionpapers'))
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_questionpaper(self):
        # Given
        questionpapers = QuestionPaper.objects.filter(
            quiz__in=[self.quiz1, self.quiz2]
        )
        serializer = QuestionPaperSerializer(questionpapers, many=True)
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:questionpapers'))
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data, serializer.data)

    def test_create_questionpaper_invalid_data(self):
        # Given
        data = {'fixed_questions': [self.question1.id], 'user': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('api:questionpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_questionpaper_valid_data(self):
        # Given
        data = {'quiz': self.quiz4.id,
                'fixed_questions': [self.question1.id, self.question2.id],
                'random_questions': [self.questionset.id]}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('api:questionpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(QuestionPaper.objects.filter(quiz=self.quiz4).exists())

    def test_create_questionpaper_not_own_quiz(self):
        # Given
        data = {'quiz': self.quiz5.id, 'fixed_questions': [self.question1.id],
                'random_questions': [self.questionset.id]}
        # When
        self.client.login(username=self.otherusername, password=self.password)
        response = self.client.post(reverse('api:questionpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_questionpaper_not_own_questions(self):
        # Given
        data = {'quiz': self.quiz6.id,
                'fixed_questions': [self.question1.id, self.question5.id],
                'random_questions': [self.questionset.id]}
        # When
        self.client.login(username=self.otherusername, password=self.password)
        response = self.client.post(reverse('api:questionpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_questionpaper_not_own_questionsets(self):
        # Given
        data = {'quiz': self.quiz6.id,
                'fixed_questions': [self.question5.id],
                'random_questions': [self.questionset.id]}
        # When
        self.client.login(username=self.otherusername, password=self.password)
        response = self.client.post(reverse('api:questionpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_questionpaper_already_exists(self):
        # Given
        data = {'quiz': self.quiz1.id,
                'fixed_questions': [self.question1.id],
                'random_questions': [self.questionset.id]}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('api:questionpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(QuestionPaper.objects.filter(
                         quiz=self.quiz1).count(), 1)

    # QuestionPaper Detail Tests
    def test_get_questionpaper(self):
        # Given
        questionpaper = self.questionpaper
        serializer = QuestionPaperSerializer(questionpaper)
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:questionpaper',
                                   kwargs={'pk': questionpaper.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_questionpaper_not_own(self):
        # Given
        questionpaper = self.questionpaper
        # When
        self.client.login(username=self.otherusername, password=self.password)
        response = self.client.get(reverse('api:questionpaper',
                                   kwargs={'pk': questionpaper.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edit_questionpaper(self):
        # Given
        questionpaper = self.questionpaper2
        data = {'quiz': self.quiz5.id,
                'fixed_questions': [self.question1.id, self.question2.id],
                'random_questions': [self.questionset.id]}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(reverse('api:questionpaper',
                                   kwargs={'pk': questionpaper.id}), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        questionpaper = QuestionPaper.objects.get(pk=questionpaper.id)
        self.assertEqual(questionpaper.quiz.id, self.quiz5.id)

    def test_delete_questionpaper(self):
        # Given
        questionpaper = self.questionpaper2
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(reverse('api:questionpaper',
                                      kwargs={'pk': questionpaper.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        questionpapers = QuestionPaper.objects.filter(quiz=self.quiz2)
        self.assertFalse(questionpapers.exists())

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Question.objects.all().delete()
        QuestionPaper.objects.all().delete()
        Quiz.objects.all().delete()


class QuizListTestCase(TestCase):
    """ Test get all quizzes and create a new quiz """

    def setUp(self):
        self.client = APIClient()
        self.username = 'demo'
        self.password = 'demo'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        Quiz.objects.create(description='Test Quiz 1', creator=self.user)
        Quiz.objects.create(description='Test Quiz 2', creator=self.user)

    def test_get_all_quizzes_anonymous(self):
        # When
        response = self.client.get(reverse('api:quizzes'))
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_quizzes(self):
        # Given
        quizzes = Quiz.objects.filter(creator=self.user)
        serializer = QuizSerializer(quizzes, many=True)
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:quizzes'))
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data, serializer.data)

    def test_create_quiz_invalid_data(self):
        # Given
        data = {'creator': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('api:quizzes'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_quiz_valid_data(self):
        # Given
        data = {'description': 'Added quiz', 'creator': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse('api:quizzes'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Quiz.objects.filter(description='Added quiz').exists())

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Quiz.objects.all().delete()


class QuizDetailTestCase(TestCase):
    """ Test get, update or delete a quiz """

    def setUp(self):
        self.client = APIClient()
        self.username = 'quizuser'
        self.password = 'demo'
        self.otherusername = 'quizuser2'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        self.otheruser = User.objects.create_user(username=self.otherusername,
                                                  password=self.password)
        Quiz.objects.create(description='Quiz1', creator=self.user)
        Quiz.objects.create(description='Quiz2', creator=self.user)
        Quiz.objects.create(description='delete quiz', creator=self.user)
        Quiz.objects.create(description='Quiz3', creator=self.otheruser)

    def test_get_quiz_anonymous(self):
        # Given
        quiz = Quiz.objects.get(description='Quiz1')
        # When
        response = self.client.get(reverse('api:quiz', kwargs={'pk': quiz.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_quiz_invalid_pk(self):
        # Given
        invalid_pk = 3242
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:quiz',
                                   kwargs={'pk': invalid_pk}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_quiz(self):
        # Given
        quiz = Quiz.objects.get(description='Quiz1')
        serializer = QuizSerializer(quiz)
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:quiz',
                                   kwargs={'pk': quiz.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_quiz_not_own(self):
        # Given
        quiz = Quiz.objects.get(description='Quiz3')
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:quiz', kwargs={'pk': quiz.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edit_quiz_anonymous(self):
        # Given
        quiz = Quiz.objects.get(description='Quiz1')
        data = {'description': 'Quiz1 Edited', 'creator': self.user.id}
        # When
        response = self.client.put(reverse('api:quiz', kwargs={'pk': quiz.id}),
                                   data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_edit_quiz_invalid_data(self):
        # Given
        quiz = Quiz.objects.get(description='Quiz1')
        data = {'creator': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(reverse('api:quiz', kwargs={'pk': quiz.id}),
                                   data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_quiz(self):
        # Given
        quiz = Quiz.objects.get(description='Quiz2')
        data = {'description': 'Quiz2 edited', 'creator': self.user.id}
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(reverse('api:quiz', kwargs={'pk': quiz.id}),
                                   data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        quiz = Quiz.objects.get(pk=quiz.id)
        self.assertEqual(quiz.description, 'Quiz2 edited')

    def test_delete_quiz_anonymous(self):
        # Given
        quiz = Quiz.objects.get(description='delete quiz')
        # When
        response = self.client.delete(reverse('api:quiz',
                                      kwargs={'pk': quiz.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_quiz_not_own(self):
        # Given
        quiz = Quiz.objects.get(description='Quiz3')
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(reverse('api:quiz',
                                      kwargs={'pk': quiz.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Quiz.objects.filter(pk=quiz.id).exists())

    def test_delete_quiz(self):
        # Given
        quiz = Quiz.objects.get(description='delete quiz')
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(reverse('api:quiz',
                                      kwargs={'pk': quiz.id}))
        # Then
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(pk=quiz.id).exists())

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Quiz.objects.all().delete()


class AnswerPaperListTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.username = 'demo'
        self.otherusername = 'otheruser'
        self.studentusername = 'student'
        self.password = 'demo'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        self.otheruser = User.objects.create_user(username=self.otherusername,
                                                  password=self.password)
        self.student = User.objects.create_user(username=self.studentusername,
                                                password='demo')
        self.quiz1 = Quiz.objects.create(description='Quiz1',
                                         creator=self.user)
        self.quiz2 = Quiz.objects.create(description='Quiz2',
                                         creator=self.otheruser)
        self.questionpaper1 = QuestionPaper.objects.create(quiz=self.quiz1)
        self.questionpaper2 = QuestionPaper.objects.create(quiz=self.quiz2)
        self.question1 = Question.objects.create(summary='Q1', user=self.user,
                                                 language='python', type='mcq')
        self.question2 = Question.objects.create(summary='Q5',
                                                 user=self.otheruser,
                                                 language='python', type='mcq')
        self.questionpaper1.fixed_questions.add(self.question1)
        self.questionpaper2.fixed_questions.add(self.question2)
        self.questionpaper1.save()
        self.questionpaper2.save()
        self.questionpaper1.update_total_marks()
        self.questionpaper2.update_total_marks()
        self.answerpaper1 = AnswerPaper.objects.create(
            user=self.user,
            question_paper=self.questionpaper1, attempt_number=1,
            start_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            end_time=datetime(2015, 10, 9, 10, 28, 15, 0, tzinfo=pytz.utc)
        )
        self.answerpaper2 = AnswerPaper.objects.create(
            user=self.otheruser,
            question_paper=self.questionpaper2, attempt_number=1,
            start_time=datetime(2015, 10, 9, 10, 8, 15, 0, tzinfo=pytz.utc),
            end_time=datetime(2015, 10, 9, 10, 28, 15, 0, tzinfo=pytz.utc)
        )
        self.course = Course.objects.create(name="Python Course",
                                            enrollment="Enroll Request",
                                            creator=self.user)
        # Learing module
        learning_module = LearningModule.objects.create(
            name='LM1', description='module one', creator=self.user
        )
        learning_unit_quiz = LearningUnit.objects.create(quiz=self.quiz1,
                                                         type='quiz', order=1)
        learning_module.learning_unit.add(learning_unit_quiz)
        learning_module.save()
        self.course.learning_module.add(learning_module)
        self.course.students.add(self.student)
        self.course.save()

    def test_get_all_answerpapers(self):
        # Given
        answerpapers = [self.answerpaper1]
        serializer = AnswerPaperSerializer(answerpapers, many=True)
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('api:answerpapers'))
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_create_answerpaper_valid_data(self):
        # Given
        data = {'question_paper': self.questionpaper1.id,
                'attempt_number': 1, 'course': self.course.id}
        # When
        self.client.login(username=self.studentusername,
                          password=self.password)
        response = self.client.post(reverse('api:answerpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        answerpapers = AnswerPaper.objects.filter(
            user=self.student, attempt_number=1,
            question_paper=self.questionpaper1, course=self.course
        )
        self.assertTrue(answerpapers.exists())
        self.assertEqual(answerpapers.count(), 1)

    def test_create_answerpaper_invalid_data(self):
        # Given
        data = {'question_paper': self.questionpaper1.id}
        # When
        self.client.login(username=self.studentusername,
                          password=self.password)
        response = self.client.post(reverse('api:answerpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_answerpaper_not_enrolled(self):
        # Given
        data = {'question_paper': self.questionpaper1.id,
                'attempt_number': 1, 'course': self.course.id}
        # When
        self.client.login(username=self.otherusername, password=self.password)
        response = self.client.post(reverse('api:answerpapers'), data)
        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        answerpapers = AnswerPaper.objects.filter(
            question_paper=self.questionpaper1, user=self.otheruser,
            attempt_number=1, course=self.course
        )
        self.assertFalse(answerpapers.exists())
        self.assertEqual(answerpapers.count(), 0)

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Question.objects.all().delete()
        QuestionPaper.objects.all().delete()
        Quiz.objects.all().delete()
        AnswerPaper.objects.all().delete()


class AnswerValidatorTestCase(TestCase):

    @classmethod
    def setUpClass(self):
        self.client = APIClient()
        self.username = 'demo'
        self.password = 'demo'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        Profile.objects.create(user=self.user)
        self.quiz = Quiz.objects.create(description='Quiz', creator=self.user)
        self.questionpaper = QuestionPaper.objects.create(quiz=self.quiz)
        self.question1 = Question.objects.create(summary='Q1', user=self.user,
                                                 points=1.0, language='python',
                                                 type='code')
        self.question2 = Question.objects.create(summary='Q2', user=self.user,
                                                 points=1.0, language='python',
                                                 type='mcq')
        self.question3 = Question.objects.create(summary='Q3', user=self.user,
                                                 points=1.0, language='python',
                                                 type='mcc')
        self.question4 = Question.objects.create(summary='Q4', user=self.user,
                                                 points=1.0, language='python',
                                                 type='mcq')
        self.question5 = Question.objects.create(summary='Q5', user=self.user,
                                                 points=1.0, language='python',
                                                 type='mcq')
        self.assertion_testcase = StandardTestCase(
            question=self.question1,
            test_case='assert add(1, 3) == 4',
            type='standardtestcase'
        )
        self.assertion_testcase.save()
        self.mcq_based_testcase1 = McqTestCase(
            options='a',
            question=self.question2,
            correct=True,
            type='mcqtestcase'
        )
        self.mcq_based_testcase1.save()
        self.mcq_based_testcase2 = McqTestCase(
            options='b',
            question=self.question2,
            correct=False,
            type='mcqtestcase'
        )
        self.mcq_based_testcase2.save()
        self.mcc_based_testcase = McqTestCase(
            question=self.question3,
            options='a',
            correct=True,
            type='mcqtestcase'
        )
        self.mcc_based_testcase.save()
        self.questionset = QuestionSet.objects.create(marks=1, num_questions=1)
        self.questionset.questions.add(self.question3)
        self.questionset.questions.add(self.question4)
        self.questionset.save()
        self.questionpaper.fixed_questions.add(self.question1)
        self.questionpaper.fixed_questions.add(self.question2)
        self.questionpaper.random_questions.add(self.questionset)
        self.questionpaper.save()
        self.questionpaper.update_total_marks()
        self.course = Course.objects.create(name="Python Course",
                                            enrollment="Enroll Request",
                                            creator=self.user)
        # Learing module
        learning_module = LearningModule.objects.create(
            name='LM1', description='module one', creator=self.user
        )
        learning_unit_quiz = LearningUnit.objects.create(quiz=self.quiz,
                                                         type='quiz', order=1)
        learning_module.learning_unit.add(learning_unit_quiz)
        learning_module.save()
        self.course.learning_module.add(learning_module)
        self.course.students.add(self.user)
        self.course.save()
        self.ip = '127.0.0.1'
        self.answerpaper = self.questionpaper.make_answerpaper(
            self.user, self.ip, 1, self.course.id
        )

        settings.code_evaluators['python']['standardtestcase'] = \
            "yaksh.python_assertion_evaluator.PythonAssertionEvaluator"
        server_pool = ServerPool(n=1, pool_port=SERVER_POOL_PORT)
        self.server_pool = server_pool
        self.server_thread = t = Thread(target=server_pool.run)
        t.start()

    @classmethod
    def tearDownClass(self):
        self.client.logout()
        User.objects.all().delete()
        Question.objects.all().delete()
        QuestionPaper.objects.all().delete()
        Quiz.objects.all().delete()
        AnswerPaper.objects.all().delete()
        self.server_pool.stop()
        self.server_thread.join()
        settings.code_evaluators['python']['standardtestcase'] = \
            "python_assertion_evaluator.PythonAssertionEvaluator"

    def test_correct_mcq(self):
        # Given
        data = {'answer': str(self.mcq_based_testcase1.id)}
        answerpaper_id = self.answerpaper.id
        question_id = self.question2.id
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(
            reverse('api:validators', kwargs={'answerpaper_id': answerpaper_id,
                    'question_id': question_id}), data
        )
        # Then
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        answerpaper = AnswerPaper.objects.get(
            user=self.user, course=self.course, attempt_number=1,
            question_paper=self.questionpaper
        )
        self.assertTrue(answerpaper.marks_obtained > 0)

    def test_wrong_mcq(self):
        # Given
        data = {'answer': str(self.mcq_based_testcase2.id)}
        answerpaper_id = self.answerpaper.id
        question_id = self.question2.id
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(
            reverse('api:validators', kwargs={'answerpaper_id': answerpaper_id,
                    'question_id': question_id}), data
        )
        # Then
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('success'))

    def test_correct_mcc(self):
        # Given
        data = {'answer': str(self.mcc_based_testcase.id)}
        answerpaper_id = self.answerpaper.id
        question_id = self.question3.id
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(
            reverse('api:validators', kwargs={'answerpaper_id': answerpaper_id,
                    'question_id': question_id}), data
        )
        # Then
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        answerpaper = AnswerPaper.objects.get(
            user=self.user, course=self.course, attempt_number=1,
            question_paper=self.questionpaper
        )
        self.assertTrue(answerpaper.marks_obtained >= 0)

    def test_correct_code(self):
        # Given
        answer = dedent("""\
                            def add(a,b):
                                return a+b
                        """)
        data = {'answer': answer}
        answerpaper_id = self.answerpaper.id
        question_id = self.question1.id
        # When
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(
            reverse('api:validators', kwargs={'answerpaper_id': answerpaper_id,
                    'question_id': question_id}), data
        )
        # Then
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('status'), 'running')
        uid = response.data['uid']
        time.sleep(2)
        response = self.client.get(reverse('api:validator',
                                           kwargs={'uid': uid}))
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        answerpaper = AnswerPaper.objects.get(
            user=self.user, course=self.course, attempt_number=1,
            question_paper=self.questionpaper
        )
        if response.data.get('status') == 'done':
            result = json.loads(response.data.get('result'))
            self.assertTrue(result.get('success'))
        else:
            self.assertEqual(response.data.get('status'), 'running')
