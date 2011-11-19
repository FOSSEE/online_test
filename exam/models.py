import datetime
from django.db import models
from django.contrib.auth.models import User

################################################################################
class Profile(models.Model):
    """Profile for a user to store roll number and other details."""
    user = models.ForeignKey(User)
    roll_number = models.CharField(max_length=20)

################################################################################
class Question(models.Model):
    """A question in the database."""
    # An optional one-line summary of the question.
    summary = models.CharField(max_length=256)
    # The question text.
    description = models.TextField()
    
    # Number of points for the question.
    points = models.IntegerField(default=1)
    
    # Test cases for the question in the form of code that is run.
    # This is simple Python code.
    test = models.TextField()
    
    def __unicode__(self):
        return self.summary


################################################################################
class Answer(models.Model):
    """Answers submitted by users.
    """
    # The question for which we are an answer.
    question = models.ForeignKey(Question)
    
    # The last answer submitted by the user.
    answer = models.TextField()
    
    # Is the answer correct.
    correct = models.BooleanField(default=False)
        
    def __unicode__(self):
        return self.answer

################################################################################
class Quiz(models.Model):
    """A quiz that students will participate in.  One can think of this 
    as the "examination" event.
    """
    
    # The starting/ending date of the quiz.
    start_date = models.DateField("Date of the quiz")
    
    # This is always in minutes.
    duration = models.IntegerField("Duration of quiz in minutes", default=20)
    
    # Is the quiz active.  The admin should deactivate the quiz once it is 
    # complete.
    active = models.BooleanField(default=True)
    
    # Description of quiz.
    description = models.CharField(max_length=256)
    
    class Meta:
        verbose_name_plural = "Quizzes"
    
    def __unicode__(self):
        desc = self.description or 'Quiz'
        return '%s: on %s for %d minutes'%(desc, self.start_date, self.duration)

    
################################################################################
class QuestionPaper(models.Model):
    """A question paper for a student -- one per student typically.
    """
    # The user taking this question paper.
    user = models.ForeignKey(User)
    
    # The Quiz to which this question paper is attached to.
    quiz = models.ForeignKey(Quiz)
    
    # The time when this paper was started by the user.
    start_time = models.DateTimeField()
    
    # User's IP which is logged.
    user_ip = models.CharField(max_length=15)
    # Unused currently.
    key = models.CharField(max_length=10)

    # used to allow/stop a user from retaking the question paper.
    active = models.BooleanField(default = True)
    
    # The questions (a list of ids separated by '|')
    questions = models.CharField(max_length=128)
    # The questions successfully answered (a list of ids separated by '|')
    questions_answered = models.CharField(max_length=128)
    
    # All the submitted answers.
    answers = models.ManyToManyField(Answer)
    
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
            
    def time_left(self):
        """Return the time remaining for the user in seconds."""
        dt = datetime.datetime.now() - self.start_time
        try:
            secs = dt.total_seconds()
        except AttributeError:
            # total_seconds is new in Python 2.7. :(
            secs = dt.seconds + dt.days*24*3600
        total = self.quiz.duration*60.0
        remain = max(total - secs, 0)
        return int(remain)
    
    def __unicode__(self):
        u = self.user
        return u'Question paper for {0} {1}'.format(u.first_name, u.last_name)

