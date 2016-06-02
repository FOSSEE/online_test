from yaksh.models import Question, Quiz
from yaksh.models import TestCase, StandardTestCase, StdioBasedTestCase
from django.contrib import admin

admin.site.register(Question)
admin.site.register(TestCase)
admin.site.register(StandardTestCase)
admin.site.register(StdioBasedTestCase)
admin.site.register(Quiz)
