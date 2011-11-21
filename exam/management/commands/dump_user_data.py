# Django imports.
from django.core.management.base import BaseCommand

# Local imports.
from exam.views import get_user_data
from exam.models import User


def dump_user_data(unames, stdout):
    '''Dump user data given usernames (a sequence) if none is given dump all
    their data.  The data is dumped to stdout.
    '''
    if not unames:
        try:
            users = User.objects.all()
        except User.DoesNotExist:
            pass
    else:
        users = []
        for uname in unames:
            try:
                user = User.objects.get(username__exact = uname)
            except User.DoesNotExist:
                stdout.write('User %s does not exist'%uname)
            else:
                users.append(user)

    for user in users:
        data = get_user_data(user.username)
        stdout.write('='*80 + '\n')
        stdout.write('Data for %s (%s)\n'%(data['name'], data['username']))
        stdout.write('Roll Number: %s, email: %s\n'%(data['rollno'], data['email']))
        stdout.write('-'*40 + '\n')
        for paper in data['papers']:
            title = "Paper: %s\n"%paper['name']
            stdout.write(title)
            stdout.write('-'*len(title) + '\n')
            stdout.write('Total marks: %d\n'%paper['total'])
            stdout.write('Questions correctly answered: %s\n'%paper['answered'])
            stdout.write('Attempts: %d\n'%paper['attempts'])
            stdout.write('\nAnswers\n----------\n\n')
            for question, answer in paper['answers'].iteritems():
                stdout.write('Question: %s\n'%question)
                stdout.write(answer)
                stdout.write('\n')


class Command(BaseCommand):
    args = '<username1> ... <usernamen>'
    help = '''Dumps all user data to stdout, optional usernames can be
              specified.  If none is specified all user data is dumped.
           '''
    
    def handle(self, *args, **options):
        """Handle the command."""
        # Dump data.
        dump_user_data(args, self.stdout)

