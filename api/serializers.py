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
        return Quiz.objcects.create(**validated_data)

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'
    def create(self,validated_data):
        return Lesson.objcects.create(**validated_data)


class LearningUnitSerializer(serializers.ModelSerializer):
    quiz=QuizSerializer(allow_null=True)
    lesson=LessonSerializer(allow_null=True)
    class Meta:
        model = LearningUnit
        fields = '__all__'
    def create(self,validated_data,quiz,lesson):
        new_unit=LearningUnit.objects.create(**validated_data,quiz=quiz,lesson=lesson)
        return new_unit

class LearningModuleSerializer(serializers.ModelSerializer):

    learning_unit = LearningUnitSerializer(many=True)
    class Meta:
        model = LearningModule
        fields = '__all__'
    def create(self,validated_data):
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
          new_course=Course(**validated_data)
          new_course.save()
          return new_course
    # def create(self,validated_data):
    #     learning_modules=validated_data.pop('learning_module')
    #     new_course=Course(**validated_data)
    #     new_course.save()
    #     for learning_module in learning_modules:
    #         learning_units=learning_module.pop('learning_unit')
    #         new_learning_module=LearningModule(**learning_module)
    #         new_learning_module.save()
    #         for learning_unit in learning_units:
    #             lesson=learning_unit.pop('lesson')
    #             quiz=learning_unit.pop('quiz')
    #             new_quiz= Quiz.objects.create(**quiz) if quiz else None
    #             new_lesson=Lesson.objects.create(**lesson) if lesson else None
    #             new_learning_unit=LearningUnit(**learning_unit,quiz=new_quiz,lesson=new_lesson)
    #             new_learning_unit.save()
    #             new_learning_module.learning_unit.add(new_learning_unit)
    #         new_course.learning_module.add(new_learning_module)
    #     return new_course

            

                

