from rest_framework import serializers
from yaksh.models import (
    Question, Quiz, QuestionPaper, AnswerPaper, Course,
    LearningModule, LearningUnit, Lesson
)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = '__all__'


class QuestionPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionPaper
        fields = '__all__'


class AnswerPaperSerializer(serializers.ModelSerializer):

    questions = QuestionSerializer(many=True)

    class Meta:
        model = AnswerPaper
        fields = '__all__'


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'


class LearningUnitSerializer(serializers.ModelSerializer):

    quiz = QuizSerializer()
    lesson = LessonSerializer()

    class Meta:
        model = LearningUnit
        fields = '__all__'


class LearningModuleSerializer(serializers.ModelSerializer):

    learning_unit = LearningUnitSerializer(many=True)

    class Meta:
        model = LearningModule
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):

    learning_module = LearningModuleSerializer(many=True)

    class Meta:
        model = Course
        fields = '__all__'
