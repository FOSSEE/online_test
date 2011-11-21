# Django imports.
from django.core.management.base import BaseCommand
from django.template import Template, Context

# Local imports.
from exam.views import get_user_data
from exam.models import User

data_template = Template('''\
===============================================================================
Data for {{ user_data.name.title }} ({{ user_data.username }})

Name: {{ user_data.name.title }}
Username: {{ user_data.username }}
Roll number: {{ user_data.rollno }}
Email: {{ user_data.email }}
Date joined: {{ user_data.date_joined }}
Last login: {{ user_data.last_login }}
{% for paper in user_data.papers %}
Paper: {{ paper.name }}
-----------------------------------------
Total marks: {{ paper.total }}
Questions correctly answered: {{ paper.answered }}
Total attempts at questions: {{ paper.attempts }}
Start time: {{ paper.start_time }} 
User IP address: {{ paper.user_ip }} 
{% if paper.answers %}
Answers
-------
{% for question, answer in paper.answers.items %}
Question: {{ question }}
{{ answer|safe }}
{% endfor %} \
{% endif %} {# if paper.answers #} \
{% endfor %} {# for paper in user_data.papers #}
''')


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
        context = Context({'user_data': data})
        result = data_template.render(context)
        stdout.write(result)

class Command(BaseCommand):
    args = '<username1> ... <usernamen>'
    help = '''Dumps all user data to stdout, optional usernames can be
              specified.  If none is specified all user data is dumped.
           '''
    
    def handle(self, *args, **options):
        """Handle the command."""
        # Dump data.
        dump_user_data(args, self.stdout)

