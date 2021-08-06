from django.contrib import admin

from yaksh.courses.models import (
    Course, Module, Lesson, Enrollment, CourseTeacher, Topic, Question, Answer,
    TableOfContent, LessonQuizAnswer, Unit
)

admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(CourseTeacher)
admin.site.register(Topic)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(TableOfContent)
admin.site.register(LessonQuizAnswer)
admin.site.register(Unit)
