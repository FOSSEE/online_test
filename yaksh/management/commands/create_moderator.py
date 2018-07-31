'''
   This command creates a moderator group and adds users to the moderator group
   with permissions to add, change and delete
   the objects in the exam app.
'''

# django imports
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group, Permission

# local imports
from yaksh.models import create_group


class Command(BaseCommand):
    help = 'Adds users to the moderator group'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('usernames', nargs='*', type=str)

    def handle(self, *args, **options):
        app_label = 'yaksh'
        group_name = 'moderator'
        group = create_group(group_name, app_label)
        if group and isinstance(group, Group):
            self.stdout.write('Moderator group added successfully')

        if options['usernames']:
            for uname in options['usernames']:
                try:
                    user = User.objects.get(username=uname)
                except User.DoesNotExist:
                    raise CommandError('User "{0}" does not exist'.format(
                        uname)
                    )
                if user in group.user_set.all():
                    self.stdout.write('User "{0}" is '
                                      'already a Moderator'.format(uname)
                                      )
                else:
                    group.user_set.add(user)
                    self.stdout.write('Successfully added User "{0}"'
                                      ' to Moderator group'.format(uname)
                                      )
