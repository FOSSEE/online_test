import sys

# Django imports.
from django.core.management.base import BaseCommand
from django.template import Template, Context

# Local imports.
from yaksh.views import get_user_data
from yaksh.models import User

data_template = Template('''\
===============================================================================
Data for {{ data.user.get_full_name.title }} ({{ data.user.username }})

Name: {{ data.user.get_full_name.title }}
Username: {{ data.user.username }}
{% if data.profile %}\
Roll number: {{ data.profile.roll_number }}
Position: {{ data.profile.position }}
Department: {{ data.profile.department }}
Institute: {{ data.profile.institute }}
{% endif %}\
Email: {{ data.user.email }}
Date joined: {{ data.user.date_joined }}
Last login: {{ data.user.last_login }} 
{% for paper in data.papers %}
Paper: {{ paper.quiz.description }}
---------------------------------------
Marks obtained: {{ paper.get_total_marks }}
Questions correctly answered: {{ paper.get_answered_str }}
Total attempts at questions: {{ paper.answers.count }}
Start time: {{ paper.start_time }}
User IP address: {{ paper.user_ip }}
{% if paper.answers.count %}
Answers
-------
{% for question, answers in paper.get_question_answers.items %}
Question: {{ question.id }}. {{ question.summary }} (Points: {{ question.points }})
{% if question.type == "mcq" %}\
###############################################################################
Choices: {% for option in question.options.strip.splitlines %} {{option}}, {% endfor %}
Student answer: {{ answers.0|safe }}
{% else %}{# non-mcq questions #}\
{% for answer in answers %}\
###############################################################################
{{ answer.answer.strip|safe }}
# Autocheck: {{ answer.error|safe }}
{% endfor %}{# for answer in answers #}\
{% endif %}\
{% with answers|last as answer %}\
Marks: {{answer.marks}}
{% endwith %}\
{% endfor %}{# for question, answers ... #}\

Teacher comments
-----------------
{{ paper.comments|default:"None" }}
{% endif %}{# if paper.answers.count #}\
{% endfor %}{# for paper in data.papers #}
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
        context = Context({'data': data})
        result = data_template.render(context)
        stdout.write(result.encode('ascii', 'xmlcharrefreplace'))

class Command(BaseCommand):
    args = '<username1> ... <usernamen>'
    help = '''Dumps all user data to stdout, optional usernames can be
              specified.  If none is specified all user data is dumped.
           '''
    
    def handle(self, *args, **options):
        """Handle the command."""
        # Dump data.
        dump_user_data(args, self.stdout)

