from django.contrib import admin
from grades.models import GradingSystem, GradeRange


class GradingSystemAdmin(admin.ModelAdmin):
    readonly_fields = ('creator',)

admin.site.register(GradingSystem, GradingSystemAdmin)
admin.site.register(GradeRange)
