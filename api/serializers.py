from rest_framework import serializers
from yaksh.models import Question, Quiz, QuestionPaper, AnswerPaper


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
    class Meta:
        model = AnswerPaper
        fields = '__all__'
