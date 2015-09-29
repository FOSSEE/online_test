# System library imports.
from os.path import basename

# Django imports.
from django.core.management.base import BaseCommand

# Local imports.
from yaksh.models import Question, Quiz

def clear_exam():
    """Deactivate all questions from the database."""
    for question in Question.objects.all():
        question.active = False
        question.save()
        
    # Deactivate old quizzes.
    for quiz in Quiz.objects.all():
        quiz.active = False
        quiz.save()

def load_exam(filename):
    """Load questions and quiz from the given Python file.  The Python file 
    should declare a list of name "questions" which define all the questions 
    in pure Python.  It can optionally load a Quiz from an optional 'quiz' 
    object.
    """
    # Simply exec the given file and we are done.
    exec(open(filename).read())
    
    if 'questions' not in locals():
        msg = 'No variable named "questions" with the Questions in file.'
        raise NameError(msg)
    
    for question in questions:
        question[0].save()
        for tag in question[1]:
            question[0].tags.add(tag)
        
    if 'quiz' in locals():
        quiz.save()
    
class Command(BaseCommand):
    args = '<q_file1.py q_file2.py>'
    help = '''loads the questions from given Python files which declare the 
              questions in a list called "questions".'''
    
    def handle(self, *args, **options):
        """Handle the command."""
        # Delete existing stuff.
        clear_exam()
        
        # Load from files.
        for fname in args:
            self.stdout.write('Importing from {0} ... '.format(basename(fname)))
            load_exam(fname)
            self.stdout.write('Done\n')
            
