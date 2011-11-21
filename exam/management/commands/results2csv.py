# System library imports.
import sys
from os.path import basename

# Django imports.
from django.core.management.base import BaseCommand
from django.template import Template, Context

# Local imports.
from exam.views import get_quiz_data
from exam.models import Quiz

result_template = Template('''\
"name","username","rollno","email","answered","total","attempts","position","department","institute"
{% for paper in paper_list %}\
"{{ paper.name }}","{{ paper.username }}","{{ paper.rollno }}",\
"{{ paper.email }}","{{ paper.answered }}",{{ paper.total }},\
{{ paper.attempts }},"{{ paper.position }}",\
"{{ paper.department }}","{{ paper.institute }}"
{% endfor %}\
''')

def results2csv(filename, stdout):
    """Write exam data to a CSV file.  It prompts the user to choose the
    appropriate quiz.
    """
    qs = Quiz.objects.all()

    if len(qs) > 1:
        print "Select quiz to save:"
        for q in qs:
            stdout.write('%d. %s\n'%(q.id, q.description))
        quiz_id = int(raw_input("Please select quiz: "))
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            stdout.write("Sorry, quiz %d does not exist!\n"%quiz_id)
            sys.exit(1)
    else:
        quiz = qs[0]

    paper_list = get_quiz_data(quiz.id)
    stdout.write("Saving results of %s to %s ... "%(quiz.description,
                                                    basename(filename)))
    # Render the data and write it out.
    f = open(filename, 'w')
    context = Context({'paper_list': paper_list})
    f.write(result_template.render(context))
    f.close()

    stdout.write('Done\n')
    
class Command(BaseCommand):
    args = '<results.csv>'
    help = '''Writes out the results of a quiz to a CSV file.  Prompt user
              to select appropriate quiz if there are multiple.
           '''
    
    def handle(self, *args, **options):
        """Handle the command."""
        # Save to file.
        results2csv(args[0], self.stdout)
