from rest_framework import serializers
from yaksh.models import (
    Question, Quiz, QuestionPaper, AnswerPaper, Course,
    LearningModule, LearningUnit, Lesson
)
from django.contrib.auth.models import User
class QuestionSerializer(serializers.ModelSerializer):
    test_cases = serializers.SerializerMethodField()

    def get_test_cases(self, obj):
        test_cases = obj.get_test_cases_as_dict()
        return test_cases

    class Meta:
        model = Question
        exclude = ('partial_grading', )


class QuestionPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionPaper
        fields = '__all__'


class AnswerPaperSerializer(serializers.ModelSerializer):

    questions = QuestionSerializer(many=True)

    class Meta:
        model = AnswerPaper
        fields = '__all__'

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        exclude = ('view_answerpaper', )
    def create(self,validated_data):
        return Quiz.objects.create(**validated_data)

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'
    def create(self,validated_data):
        return Lesson.objects.create(**validated_data)


class LearningUnitSerializer(serializers.ModelSerializer):
    quiz=QuizSerializer(allow_null=True)
    lesson=LessonSerializer(allow_null=True)
    class Meta:
        model = LearningUnit
        fields = '__all__'
    def create(self,validated_data,quiz=None,lesson=None):
        new_unit=LearningUnit(**validated_data)
        new_unit.save()
        return new_unit

class LearningModuleSerializer(serializers.ModelSerializer):

    learning_unit = LearningUnitSerializer(many=True)
    class Meta:
        model = LearningModule
        fields = '__all__'
    def create(self,validated_data):
        learning_unit=validated_data.pop("learning_unit")
        new_module=LearningModule(**validated_data)
        new_module.save()
        return new_module
        
    
class CourseSerializer(serializers.ModelSerializer):
    learning_module = LearningModuleSerializer(many=True)
    class Meta:
        model = Course
        exclude = (
            'teachers',
            'rejected',
            'requests',
            'students',
            'grading_system',
            'view_grade',
        )
    def create(self,validated_data):
          learning_module=validated_data.pop('learning_module')
          new_course=Course(**validated_data)
          new_course.save()
          return new_course

            

                

