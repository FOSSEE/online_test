from yaksh.models import Question, Quiz, QuestionPaper
from yaksh.models import TestCase, StandardTestCase, StdioBasedTestCase, Course, AnswerPaper
from django.contrib import admin

admin.site.register(Question)
admin.site.register(TestCase)
admin.site.register(StandardTestCase)
admin.site.register(StdioBasedTestCase)
admin.site.register(Course)
admin.site.register(Quiz)
admin.site.register(QuestionPaper)
admin.site.register(AnswerPaper)