from django.contrib import admin

# Register your models here.
from .models import Team, Role, Permission

admin.site.register(Team)
admin.site.register(Role)
admin.site.register(Permission)
