# Django Imports
from django.contrib import admin

# Local Imports
from stats.models import TrackLesson


class TrackLessonAdmin(admin.ModelAdmin):
    search_fields = ['user__first_name', 'user__last_name', 'user__username',
                     'course__name', 'lesson__name']
    readonly_fields = ["course", "user", "lesson"]


admin.site.register(TrackLesson, TrackLessonAdmin)
