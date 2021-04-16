from yaksh.models import Question, Quiz, QuestionPaper, Profile
from yaksh.models import (TestCase, StandardTestCase, StdIOBasedTestCase,
                          Course, AnswerPaper, CourseStatus, LearningModule,
                          Lesson, Post, Comment, Topic, TableOfContents,
                          LessonQuizAnswer, Answer, AssignmentUpload
                          )
from django.contrib import admin


class AnswerPaperAdmin(admin.ModelAdmin):
    search_fields = ['user__first_name', 'user__last_name', 'user__username',
                     "question_paper__quiz__description", "user_ip"]
    list_filter = ['course__is_trial']
    readonly_fields = ["course", "question_paper"]

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("answers", "questions_unanswered",
                        "questions_answered", "questions")
        form = super(AnswerPaperAdmin, self).get_form(request, obj, **kwargs)
        return form


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ['user__first_name', 'user__last_name', 'user__username',
                     "roll_number", "institute", "department"]


class CourseStatusAdmin(admin.ModelAdmin):
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    list_filter = ['course__is_trial']


class CourseAdmin(admin.ModelAdmin):
    list_filter = ['active', 'is_trial']


class LearningModuleAdmin(admin.ModelAdmin):
    list_filter = ['active', 'is_trial']


class LessonAdmin(admin.ModelAdmin):
    list_filter = ['active']


class QuizAdmin(admin.ModelAdmin):
    list_filter = ['active', 'is_trial']


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Question)
admin.site.register(TestCase)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(StandardTestCase)
admin.site.register(StdIOBasedTestCase)
admin.site.register(Course, CourseAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuestionPaper)
admin.site.register(AnswerPaper, AnswerPaperAdmin)
admin.site.register(CourseStatus, CourseStatusAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(LearningModule, LearningModuleAdmin)
admin.site.register(Topic)
admin.site.register(TableOfContents)
admin.site.register(LessonQuizAnswer)
admin.site.register(Answer)
admin.site.register(AssignmentUpload)
