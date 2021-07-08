from django.contrib import admin

from yaksh.courses.models import (
    Course, Module, Lesson, Enrollment, CourseTeacher
)

admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(CourseTeacher)
