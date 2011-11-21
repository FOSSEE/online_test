# System library imports.
import sys
from os.path import basename

# Django imports.
from django.core.management.base import BaseCommand

# Local imports.
from exam.views import get_quiz_data
from exam.models import Quiz

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
    f = open(filename, 'w')
    fields = ['name', 'username', 'rollno', 'email', 'answered', 'total',
              'attempts']
    SEP = ','
    f.write(SEP.join(['"%s"'%x for x in fields]) + '\n')
    for paper in paper_list:
        # name, username, rollno, email, answered
        f.write(SEP.join(['"%s"'%(paper[x]) for x in fields[:5]]) + SEP) 
        # total, attempts
        f.write(SEP.join(['%d'%(paper[x]) for x in fields[5:]]) + '\n')
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
