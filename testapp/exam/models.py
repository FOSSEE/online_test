import datetime
from random import sample, shuffle
from django.db import models
from django.contrib.auth.models import User
from taggit_autocomplete_modified.managers import TaggableManagerAutocomplete\
as TaggableManager


###############################################################################
class Profile(models.Model):
    """Profile for a user to store roll number and other details."""
    user = models.OneToOneField(User)
    roll_number = models.CharField(max_length=20)
    institute = models.CharField(max_length=128)
    department = models.CharField(max_length=64)
    position = models.CharField(max_length=64)


LANGUAGES = (
        ("python", "Python"),
        ("bash", "Bash"),
        ("C", "C Language"),
        ("C++", "C++ Language"),
        ("java", "Java Language"),
        ("scilab", "Scilab"),
                            )


QUESTION_TYPES = (
        ("mcq", "Multiple Choice"),
        ("code", "Code"),
                        )


###############################################################################
class Question(models.Model):
    """Question for a quiz."""

    # A one-line summary of the question.
    summary = models.CharField(max_length=256)

    # The question text, should be valid HTML.
    description = models.TextField()

    # Number of points for the question.
    points = models.FloatField(default=1.0)

    # Test cases for the question in the form of code that is run.
    test = models.TextField(blank=True)

    # Any multiple choice options. Place one option per line.
    options = models.TextField(blank=True)

    # The language for question.
    language = models.CharField(max_length=24,
                                choices=LANGUAGES)

    # The type of question.
    type = models.CharField(max_length=24, choices=QUESTION_TYPES)

    # Is this question active or not. If it is inactive it will not be used
    # when creating a QuestionPaper.
    active = models.BooleanField(default=True)

    # Snippet of code provided to the user.
    snippet = models.CharField(max_length=256)

    # Tags for the Question.
    tags = TaggableManager()

    def __unicode__(self):
        return self.summary


###############################################################################
class Answer(models.Model):
    """Answers submitted by the users."""

    # The question for which user answers.
    question = models.ForeignKey(Question)

    # The answer submitted by the user.
    answer = models.TextField(null=True, blank=True)

    # Error message when auto-checking the answer.
    error = models.TextField()

    # Marks obtained for the answer. This can be changed by the teacher if the
    # grading is manual.
    marks = models.FloatField(default=0.0)

    # Is the answer correct.
    correct = models.BooleanField(default=False)

    def __unicode__(self):
        return self.answer


###############################################################################
class Quiz(models.Model):
    """A quiz that students will participate in. One can think of this
    as the "examination" event.
    """

    # The start date of the quiz.
    start_date = models.DateField("Date of the quiz")

    # This is always in minutes.
    duration = models.IntegerField("Duration of quiz in minutes", default=20)

    # Is the quiz active. The admin should deactivate the quiz once it is
    # complete.
    active = models.BooleanField(default=True)

    # Description of quiz.
    description = models.CharField(max_length=256)

    # Mininum passing percentage condition.
    pass_criteria = models.FloatField("Passing percentage", default=40)

    # List of prerequisite quizzes to be passed to take this quiz
    prerequisite = models.ForeignKey("self", null=True)

    # Programming language for a quiz
    language = models.CharField(max_length=20, choices=LANGUAGES)

    class Meta:
        verbose_name_plural = "Quizzes"

    def __unicode__(self):
        desc = self.description or 'Quiz'
        return '%s: on %s for %d minutes' % (desc, self.start_date,
                                             self.duration)


###############################################################################
class QuestionPaper(models.Model):
    """Question paper stores the detail of the questions."""

    # Question paper belongs to a particular quiz.
    quiz = models.ForeignKey(Quiz)

    # Questions that will be mandatory in the quiz.
    fixed_questions = models.ManyToManyField(Question)

    # Questions that will be fetched randomly from the Question Set.
    random_questions = models.ManyToManyField("QuestionSet")

    # Option to shuffle questions, each time a new question paper is created.
    shuffle_questions = models.BooleanField(default=False)

    # Total marks for the question paper.
    total_marks = models.FloatField()

    def update_total_marks(self):
        """ Updates the total marks for the Question Paper"""
        marks = 0.0
        questions = self.fixed_questions.all()
        for question in questions:
            marks += question.points
        for question_set in self.random_questions.all():
            marks += question_set.marks * question_set.num_questions
        self.total_marks = marks
        return None

    def _get_questions_for_answerpaper(self):
        """ Returns fixed and random questions for the answer paper"""
        questions = []
        questions = list(self.fixed_questions.all())
        for question_set in self.random_questions.all():
            questions += question_set.get_random_questions()
        return questions

    def make_answerpaper(self, user, ip):
        """Creates an  answer paper for the user to attempt the quiz"""
        ans_paper = AnswerPaper(user=user, profile=user.profile, user_ip=ip)
        ans_paper.start_time = datetime.datetime.now()
        ans_paper.end_time = ans_paper.start_time \
                             + datetime.timedelta(minutes=self.quiz.duration)
        ans_paper.question_paper = self
        questions = self._get_questions_for_answerpaper()
        question_ids = [str(x.id) for x in questions]
        if self.shuffle_questions:
            shuffle(question_ids)
        ans_paper.questions = "|".join(question_ids)
        ans_paper.save()
        return ans_paper


###############################################################################
class QuestionSet(models.Model):
    """Question set contains a set of questions from which random questions
       will be selected for the quiz.
    """

    # Marks of each question of a particular Question Set
    marks = models.FloatField()

    # Number of questions to be fetched for the quiz.
    num_questions = models.IntegerField()

    # Set of questions for sampling randomly.
    questions = models.ManyToManyField(Question)

    def get_random_questions(self):
        """ Returns random questions from set of questions"""
        return sample(self.questions.all(), self.num_questions)


###############################################################################
class AnswerPaper(models.Model):
    """A answer paper for a student -- one per student typically.
    """
    # The user taking this question paper.
    user = models.ForeignKey(User)

    # The user's profile, we store a reference to make it easier to access the
    # data.
    profile = models.ForeignKey(Profile)

    # All questions that remain to be attempted for a particular Student
    # (a list of ids separated by '|')
    questions = models.CharField(max_length=128)

    # The Quiz to which this question paper is attached to.
    question_paper = models.ForeignKey(QuestionPaper)

    # The time when this paper was started by the user.
    start_time = models.DateTimeField()

    # The time when this paper was ended by the user.
    end_time = models.DateTimeField()

    # User's IP which is logged.
    user_ip = models.CharField(max_length=15)

    # The questions successfully answered (a list of ids separated by '|')
    questions_answered = models.CharField(max_length=128)

    # All the submitted answers.
    answers = models.ManyToManyField(Answer)

    # Teacher comments on the question paper.
    comments = models.TextField()

    # Total marks earned by the student in this paper.
    marks_obtained = models.FloatField(null=True, default=None)

    # Marks percent scored by the user
    percent = models.FloatField(null=True, default=None)

    # Result of the quiz, either PASSED or FAILED.
    result = models.CharField(max_length=8, null=True, default=None)

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

    def completed_question(self, question_id):
        """
            Removes the completed question from the list of questions and
            returns the next question.
        """
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
        """
            Skips the current question and returns the next available question.
        """
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
        total = self.question_paper.quiz.duration*60.0
        remain = max(total - secs, 0)
        return int(remain)

    def get_answered_str(self):
        """Returns the answered questions, sorted and as a nice string."""
        qa = self.questions_answered.split('|')
        answered = ', '.join(sorted(qa))
        return answered if answered else 'None'

    def update_marks_obtained(self):
        """Updates the total marks earned by student for this paper."""
        marks = sum([x.marks for x in self.answers.filter(marks__gt=0.0)])
        self.marks_obtained = marks
        return None

    def update_percent(self):
        """Updates the percent gained by the student for this paper."""
        total_marks = self.question_paper.total_marks
        if self.marks_obtained is not None:
            percent = self.marks_obtained/self.question_paper.total_marks*100
            self.percent = round(percent, 2)
        return None

    def update_result(self):
        """
            Updates the result.
            It is either passed or failed, as per the quiz passing criteria
        """
        if self.percent is not None: 
            if self.percent >= self.question_paper.quiz.pass_criteria:
                self.result = "PASSED"
            else:
                self.result = "FAILED"
        return None

    def get_question_answers(self):
        """
            Return a dictionary with keys as questions and a list of the
            corresponding answers.
        """
        q_a = {}
        for answer in self.answers.all():
            question = answer.question
            if question in q_a:
                q_a[question].append(answer)
            else:
                q_a[question] = [answer]
        return q_a

    def __unicode__(self):
        u = self.user
        return u'Question paper for {0} {1}'.format(u.first_name, u.last_name)
