from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    """Profile for a user to store roll number etc."""
    user = models.ForeignKey(User)
    roll_number = models.CharField(max_length=20)

class Question(models.Model):
    """A question in the database."""
    # An optional one-line summary of the question.
    summary = models.CharField(max_length=256)
    # The question text.
    description = models.TextField()
    
    # Number of points for the question.
    points = models.IntegerField()
    
    # Test cases for the question in the form of code that is run.
    # This is simple Python code.
    test = models.TextField()
    
    def __unicode__(self):
        return self.summary
    

class Answer(models.Model):
    """Answers submitted by users.
    """
    question = models.ForeignKey(Question)
    # The last answer submitted by the user.
    answer = models.TextField()
    attempts = models.IntegerField()
    
    # Is the question correct.
    correct = models.BooleanField()
    # Marks obtained.
    marks = models.IntegerField()
    
    def __unicode__(self):
        return self.answer
    
class Quiz(models.Model):
    """A quiz for a student.
    """
    user = models.ForeignKey(User)
    user_ip = models.CharField(max_length=15)
    key = models.CharField(max_length=10)
    questions = models.CharField(max_length=128)
    questions_answered = models.CharField(max_length=128)
    
    def current_question(self):
        """Returns the current active question to display."""
        qs = self.questions.split('|')
        if len(qs) > 0:
            return qs[0]
        else:
            return ''
            
    def questions_left(self):
        """Returns the number of questions left."""
        qs = self.questions
        if len(qs) == 0:
            return 0
        else:
            return qs.count('|') + 1
            
    def answered_question(self, question_id):
        """Removes the question from the list of questions and returns
        the next."""
        qa = self.questions_answered
        if len(qa) > 0:
            self.questions_answered = '|'.join([qa, str(question_id)])
        else:
            self.questions_answered = str(question_id)
        qs = self.questions.split('|')
        qs.remove(unicode(question_id))
        self.questions = '|'.join(qs)
        self.save()
        if len(qs) == 0:
            return ''
        else:
            return qs[0]
            
    def skip(self):
        """Skip the current question and return the next available question."""
        qs = self.questions.split('|')
        if len(qs) == 0:
            return ''
        else:
            # Put head at the end.
            head = qs.pop(0)
            qs.append(head)
            self.questions = '|'.join(qs)
            self.save()
            return qs[0]
    
    def __unicode__(self):
        u = self.user
        return u'Quiz for {0} {1}'.format(u.first_name, u.last_name)
