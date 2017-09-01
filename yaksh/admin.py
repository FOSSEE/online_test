from yaksh.models import Question, Quiz, QuestionPaper, Profile
from yaksh.models import TestCase, StandardTestCase, StdIOBasedTestCase, Course, AnswerPaper
from django.contrib import admin



class AnswerPaperAdmin(admin.ModelAdmin):
	search_fields = ['user__first_name', 'user__last_name','user__username',
					 "question_paper__quiz__description","user_ip" ]

class ProfileAdmin(admin.ModelAdmin):
	search_fields = ['user__first_name', 'user__last_name','user__username',
					 "roll_number", "institute","department"]

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Question)
admin.site.register(TestCase)
admin.site.register(StandardTestCase)
admin.site.register(StdIOBasedTestCase)
admin.site.register(Course)
admin.site.register(Quiz)
admin.site.register(QuestionPaper)
admin.site.register(AnswerPaper, AnswerPaperAdmin)
