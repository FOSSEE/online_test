from yaksh.models import (
    Question, Quiz, QuestionPaper, QuestionSet, AnswerPaper, Course, Answer
)
from api.serializers import (
    QuestionSerializer, QuizSerializer, QuestionPaperSerializer,
    AnswerPaperSerializer, CourseSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes
)
from django.http import Http404
from django.contrib.auth import authenticate
from yaksh.code_server import get_result as get_result_from_code_server
from yaksh.settings import SERVER_POOL_PORT, SERVER_HOST_NAME
import json


class QuestionList(APIView):
    """ List all questions or create a new question. """

    def get(self, request, format=None):
        questions = Question.objects.filter(user=request.user)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseList(APIView):
    """ List all courses """

    def get(self, request, format=None):
        courses = Course.objects.filter(students=request.user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


class StartQuiz(APIView):
    """ Retrieve Answerpaper. If does not exists then create one """

    def get_quiz(self, pk, user):
        try:
            return Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            raise Http404

    def get(self, request, course_id, quiz_id,  format=None):
        context = {}
        user = request.user
        quiz = self.get_quiz(quiz_id, user)
        questionpaper = quiz.questionpaper_set.first()

        last_attempt = AnswerPaper.objects.get_user_last_attempt(
            questionpaper, user, course_id)
        if last_attempt and last_attempt.is_attempt_inprogress():
            serializer = AnswerPaperSerializer(last_attempt)
            context["time_left"] = last_attempt.time_left()
            context["answerpaper"] = serializer.data
            return Response(context)

        can_attempt, msg = questionpaper.can_attempt_now(user, course_id)
        if not can_attempt:
            return Response({'message': msg})
        if not last_attempt:
            attempt_number = 1
        else:
            attempt_number = last_attempt.attempt_number + 1
        ip = request.META['REMOTE_ADDR']
        answerpaper = questionpaper.make_answerpaper(user, ip, attempt_number,
                                                     course_id)
        serializer = AnswerPaperSerializer(answerpaper)
        context["time_left"] = answerpaper.time_left()
        context["answerpaper"] = serializer.data
        return Response(context, status=status.HTTP_201_CREATED)


class QuestionDetail(APIView):
    """ Retrieve, update or delete a question """

    def get_question(self, pk, user):
        try:
            return Question.objects.get(pk=pk, user=user)
        except Question.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        question = self.get_question(pk, request.user)
        serializer = QuestionSerializer(question)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        question = self.get_question(pk, request.user)
        serializer = QuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        question = self.get_question(pk, request.user)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnswerPaperList(APIView):

    def get_questionpaper(self, pk):
        try:
            return QuestionPaper.objects.get(pk=pk)
        except QuestionPaper.DoesNotExist:
            raise Http404

    def get_course(self, pk):
        try:
            return Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            raise Http404

    def get_answerpapers(self, user):
        return AnswerPaper.objects.filter(question_paper__quiz__creator=user)

    def get(self, request, format=None):
        user = request.user
        answerpapers = self.get_answerpapers(user)
        serializer = AnswerPaperSerializer(answerpapers, many=True)
        return Response(serializer.data)

    def is_user_allowed(self, user, course):
        ''' if user is student or teacher or creator then allow '''
        return user in course.students.all() or user in course.teachers.all() \
            or user == course.creator

    def post(self, request, format=None):
        try:
            questionpaperid = request.data['question_paper']
            attempt_number = request.data['attempt_number']
            course_id = request.data['course']
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        ip = request.META['REMOTE_ADDR']
        questionpaper = self.get_questionpaper(questionpaperid)
        course = self.get_course(course_id)
        if not self.is_user_allowed(user, course):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        answerpaper = questionpaper.make_answerpaper(user, ip, attempt_number,
                                                     course_id)
        serializer = AnswerPaperSerializer(answerpaper)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AnswerValidator(APIView):

    def get_answerpaper(self, pk, user):
        try:
            return AnswerPaper.objects.get(pk=pk, user=user)
        except AnswerPaper.DoesNotExist:
            raise Http404

    def get_question(self, pk, answerpaper):
        try:
            question = Question.objects.get(pk=pk)
            if question in answerpaper.questions.all():
                return question
            else:
                raise Http404
        except AnswerPaper.DoesNotExist:
            raise Http404

    def get_answer(self, pk):
        try:
            return Answer.objects.get(pk=pk)
        except Answer.DoesNotExist:
            raise Http404

    def post(self, request, answerpaper_id, question_id, format=None):
        user = request.user
        answerpaper = self.get_answerpaper(answerpaper_id, user)
        question = self.get_question(question_id, answerpaper)
        try:
            if question.type == 'mcq' or question.type == 'mcc':
                user_answer = request.data['answer']
            elif question.type == 'integer':
                user_answer = int(request.data['answer'][0])
            elif question.type == 'float':
                user_answer = float(request.data['answer'][0])
            elif question.type == 'string':
                user_answer = request.data['answer']
            else:
                user_answer = request.data['answer']
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # save answer uid
        answer = Answer.objects.create(question=question, answer=user_answer)
        answerpaper.answers.add(answer)
        answerpaper.save()
        json_data = None
        if question.type in ['code', 'upload']:
            json_data = question.consolidate_answer_data(user_answer, user)
        result = answerpaper.validate_answer(user_answer, question, json_data,
                                             answer.id)

        # updaTE RESult
        if question.type not in ['code', 'upload']:
            if result.get('success'):
                answer.correct = True
                answer.marks = question.points
            answer.error = json.dumps(result.get('error'))
            answer.save()
            answerpaper.update_marks(state='inprogress')
        return Response(result)

    def get(self, request, uid):
        answer = self.get_answer(uid)
        url = '{0}:{1}'.format(SERVER_HOST_NAME, SERVER_POOL_PORT)
        result = get_result_from_code_server(url, uid)
        # update result
        if result['status'] == 'done':
            final_result = json.loads(result.get('result'))
            answer.error = json.dumps(final_result.get('error'))
            if final_result.get('success'):
                answer.correct = True
                answer.marks = answer.question.points
            answer.save()
            answerpaper = answer.answerpaper_set.get()
            answerpaper.update_marks(state='inprogress')
        return Response(result)


class QuizList(APIView):
    """ List all quizzes or create a new quiz """

    def get(self, request, format=None):
        quizzes = Quiz.objects.filter(creator=request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = QuizSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizDetail(APIView):
    """ Retrieve, update or delete a quiz """

    def get_quiz(self, pk, user):
        try:
            return Quiz.objects.get(pk=pk, creator=user)
        except Quiz.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        quiz = self.get_quiz(pk, request.user)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        quiz = self.get_quiz(pk, request.user)
        serializer = QuizSerializer(quiz, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        quiz = self.get_quiz(pk, request.user)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionPaperList(APIView):
    """ List all question papers or create a new question paper """

    def get_questionpapers(self, user):
        return QuestionPaper.objects.filter(quiz__creator=user)

    def questionpaper_exists(self, quiz_id):
        return QuestionPaper.objects.filter(quiz=quiz_id).exists()

    def check_quiz_creator(self, user, quiz_id):
        try:
            Quiz.objects.get(pk=quiz_id, creator=user)
        except Quiz.DoesNotExist:
            raise Http404

    def check_questions_creator(self, user, question_ids):
        for question_id in question_ids:
            try:
                Question.objects.get(pk=question_id, user=user)
            except Question.DoesNotExist:
                raise Http404

    def check_questionsets_creator(self, user, questionset_ids):
        for question_id in questionset_ids:
            try:
                questionset = QuestionSet.objects.get(pk=question_id)
                for question in questionset.questions.all():
                    Question.objects.get(pk=question.id, user=user)
            except (QuestionSet.DoesNotExist, Question.DoesNotExist):
                raise Http404

    def get(self, request, format=None):
        questionpapers = self.get_questionpapers(request.user)
        serializer = QuestionPaperSerializer(questionpapers, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = QuestionPaperSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            quiz_id = request.data.get('quiz')
            question_ids = request.data.get('fixed_questions', [])
            questionset_ids = request.data.get('random_questions', [])
            if self.questionpaper_exists(quiz_id):
                return Response({'error': 'Already exists'},
                                status=status.HTTP_409_CONFLICT)
            self.check_quiz_creator(user, quiz_id)
            self.check_questions_creator(user, question_ids)
            self.check_questionsets_creator(user, questionset_ids)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class QuestionPaperDetail(APIView):
    """ Retrieve, update or delete a question paper"""

    def get_questionpaper(self, pk, user):
        try:
            return QuestionPaper.objects.get(pk=pk, quiz__creator=user)
        except QuestionPaper.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        questionpaper = self.get_questionpaper(pk, request.user)
        serializer = QuestionPaperSerializer(questionpaper)
        return Response(serializer.data)

    def check_quiz_creator(self, user, quiz_id):
        try:
            Quiz.objects.get(pk=quiz_id, creator=user)
        except Quiz.DoesNotExist:
            raise Http404

    def check_questions_creator(self, user, question_ids):
        for question_id in question_ids:
            try:
                Question.objects.get(pk=question_id, user=user)
            except Question.DoesNotExist:
                raise Http404

    def check_questionsets_creator(self, user, questionset_ids):
        for question_id in questionset_ids:
            try:
                questionset = QuestionSet.objects.get(pk=question_id)
                for question in questionset.questions.all():
                    Question.objects.get(pk=question.id, user=user)
            except (QuestionSet.DoesNotExist, Question.DoesNotExist):
                raise Http404

    def put(self, request, pk, format=None):
        user = request.user
        questionpaper = self.get_questionpaper(pk, user)
        serializer = QuestionPaperSerializer(questionpaper, data=request.data)
        if serializer.is_valid():
            user = request.user
            quiz_id = request.data.get('quiz')
            question_ids = request.data.get('fixed_questions', [])
            questionset_ids = request.data.get('random_questions', [])
            self.check_quiz_creator(user, quiz_id)
            self.check_questions_creator(user, question_ids)
            self.check_questionsets_creator(user, questionset_ids)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        questionpaper = self.get_questionpaper(pk, request.user)
        questionpaper.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetCourse(APIView):
    def get(self, request, pk, format=None):
        course = Course.objects.get(id=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data)


@api_view(['POST'])
@authentication_classes(())
@permission_classes(())
def login(request):
    data = {}
    if request.method == "POST":
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_authenticated:
            token, created = Token.objects.get_or_create(user=user)
            data = {
                'token': token.key
            }
    return Response(data, status=status.HTTP_201_CREATED)


class QuitQuiz(APIView):
    def get_answerpaper(self, answerpaper_id):
        try:
            return AnswerPaper.objects.get(id=answerpaper_id)
        except AnswerPaper.DoesNotExist:
            raise Http404

    def get(self, request, answerpaper_id, format=None):
        answerpaper = self.get_answerpaper(answerpaper_id)
        answerpaper.status = 'completed'
        answerpaper.save()
        serializer = AnswerPaperSerializer(answerpaper)
        return Response(serializer.data)