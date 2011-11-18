# System library imports.
from os.path import basename
from xml.dom.minidom import parse
from htmlentitydefs import name2codepoint
import re

# Django imports.
from django.core.management.base import BaseCommand

# Local imports.
from exam.models import Question

def decode_html(html_str):
    """Un-escape or decode HTML strings to more usable Python strings.
    From here: http://wiki.python.org/moin/EscapingHtml
    """
    return re.sub('&(%s);' % '|'.join(name2codepoint), 
            lambda m: unichr(name2codepoint[m.group(1)]), html_str)

def clear_questions():
    """Delete all questions from the database."""
    for question in Question.objects.all():
        question.delete()

def load_questions_xml(filename):
    """Load questions from the given XML file."""
    q_bank = parse(filename).getElementsByTagName("question")

    for question in q_bank:

        summary_node = question.getElementsByTagName("summary")[0]
        summary = (summary_node.childNodes[0].data).strip()

        desc_node = question.getElementsByTagName("description")[0]
        description = (desc_node.childNodes[0].data).strip()

        points_node = question.getElementsByTagName("points")[0]
        points = int((points_node.childNodes[0].data).strip()) \
                 if points_node else 1

        test_node = question.getElementsByTagName("test")[0]
        test = decode_html((test_node.childNodes[0].data).strip())

        new_question = Question(summary=summary,
                                description=description,
                                points=points,
                                test=test)
        new_question.save()
    
class Command(BaseCommand):
    args = '<q_file1.xml q_file2.xml>'
    help = 'loads the questions from given XML files'
    
    def handle(self, *args, **options):
        """Handle the command."""
        # Delete existing stuff.
        clear_questions()
        
        # Load from files.
        for fname in args:
            self.stdout.write('Importing from {0} ... '.format(basename(fname)))
            load_questions_xml(fname)
            self.stdout.write('Done\n')
            
