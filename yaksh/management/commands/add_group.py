'''
   This command adds moderator group with permissions to add, change and delete
   the objects in the exam app.
   We can modify this command to add more groups by providing arguments.
   Arguments like group-name, app-name can be passed.
'''

# django imports
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError

class Command(BaseCommand):
    help = 'Adds the moderator group'

    def handle(self, *args, **options):
        app_label = 'yaksh'
        group = Group(name='moderator')
        try:
            group.save()
        except IntegrityError:
            raise CommandError("The group already exits")
        else:
            # Get the models for the given app
            content_types = ContentType.objects.filter(app_label=app_label)
            # Get list of permissions for the models
            permission_list = Permission.objects.filter(content_type__in=content_types)
            group.permissions.add(*permission_list)
            group.save()

        self.stdout.write('Moderator group added successfully')
