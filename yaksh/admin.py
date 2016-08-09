from yaksh.models import Question, Quiz
from yaksh.models import TestCase, StandardTestCase, StdoutBasedTestCase, Course
from yaksh.models import Question, Quiz, Course, QuestionPaper
from yaksh.models import TestCase, StandardTestCase, StdoutBasedTestCase
from django.contrib import admin

admin.site.register(Question)
admin.site.register(TestCase)
admin.site.register(StandardTestCase)
admin.site.register(StdoutBasedTestCase)
admin.site.register(Course)
admin.site.register(Quiz)
admin.site.register(Course)
admin.site.register(QuestionPaper)
