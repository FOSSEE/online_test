from django.contrib import admin
from grades.models import GradingSystem, GradeRange

# Register your models here.
class GradingSystemAdmin(admin.ModelAdmin):
    readonly_fields = ('creator',)

admin.site.register(GradingSystem, GradingSystemAdmin)
admin.site.register(GradeRange)
