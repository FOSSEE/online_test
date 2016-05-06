from datetime import datetime, timedelta
import json
from random import sample, shuffle
from itertools import islice, cycle
from collections import Counter
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import pytz
from taggit.managers import TaggableManager


###############################################################################
class ConcurrentUser(models.Model):
    concurrent_user = models.OneToOneField(User, null=False)
    session_key = models.CharField(null=False, max_length=40)


###############################################################################
class Profile(models.Model):
    """Profile for a user to store roll number and other details."""
    user = models.OneToOneField(User)
    roll_number = models.CharField(max_length=20)
    institute = models.CharField(max_length=128)
    department = models.CharField(max_length=64)
    position = models.CharField(max_length=64)
    timezone = models.CharField(max_length=64, choices=[(tz, tz) for tz in pytz.common_timezones])

languages = (
        ("python", "Python"),
        ("bash", "Bash"),
        ("c", "C Language"),
        ("cpp", "C++ Language"),
        ("java", "Java Language"),
        ("scilab", "Scilab"),
    )


question_types = (
        ("mcq", "Multiple Choice"),
        ("mcc", "Multiple Correct Choices"),
        ("code", "Code"),
        ("upload", "Assignment Upload"),
    )

enrollment_methods = (
    ("default", "Enroll Request"),
    ("open", "Open Course"),
    )

attempts = [(i, i) for i in range(1, 6)]
attempts.append((-1, 'Infinite'))
days_between_attempts = ((j, j) for j in range(401))

test_status = (
                ('inprogress', 'Inprogress'),
                ('completed', 'Completed'),
              )

# get current timezone info
tz = pytz.timezone(timezone.get_current_timezone_name())

def get_assignment_dir(instance, filename):
    return '%s/%s' % (instance.user.roll_number, instance.assignmentQuestion.id)


###############################################################################
class Course(models.Model):
    """ Course for students"""
    name = models.CharField(max_length=128)
    enrollment = models.CharField(max_length=32, choices=enrollment_methods)
    active = models.BooleanField(default=True)
    creator = models.ForeignKey(User, related_name='creator')
    students = models.ManyToManyField(User, related_name='students')
    requests = models.ManyToManyField(User, related_name='requests')
    rejected = models.ManyToManyField(User, related_name='rejected')
    created_on = models.DateTimeField(auto_now_add=True)
    teachers = models.ManyToManyField(User, related_name='teachers')


    def request(self, *users):
        self.requests.add(*users)

    def get_requests(self):
        return self.requests.all()

    def enroll(self, was_rejected, *users):
        self.students.add(*users)
        if not was_rejected:
            self.requests.remove(*users)
        else:
            self.rejected.remove(*users)

    def get_enrolled(self):
        return self.students.all()

    def reject(self, was_enrolled, *users):
        self.rejected.add(*users)
        if not was_enrolled:
            self.requests.remove(*users)
        else:
            self.students.remove(*users)

    def get_rejected(self):
        return self.rejected.all()

    def is_enrolled(self, user):
        return user in self.students.all()

    def is_creator(self, user):
        return self.creator == user

    def is_teacher(self, user):
        return True if user in self.teachers.all() else False

    def is_self_enroll(self):
        return True if self.enrollment == enrollment_methods[1][0] else False

    def get_quizzes(self):
        return self.quiz_set.all()

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def add_teachers(self, *teachers):
        self.teachers.add(*teachers)

    def get_teachers(self):
        return self.teachers.all()

    def remove_teachers(self, *teachers):
        self.teachers.remove(*teachers)

    def __unicode__(self):
        return self.name


###############################################################################
class Question(models.Model):
    """Question for a quiz."""

    # A one-line summary of the question.
    summary = models.CharField(max_length=256)

    # The question text, should be valid HTML.
    description = models.TextField()

    # Number of points for the question.
    points = models.FloatField(default=1.0)

    # Answer for MCQs.
    test = models.TextField(blank=True)

    # Test cases file paths (comma seperated for reference code path and test case code path)
    # Applicable for CPP, C, Java and Scilab
    ref_code_path = models.TextField(blank=True)

    # Any multiple choice options. Place one option per line.
    options = models.TextField(blank=True)

    # The language for question.
    language = models.CharField(max_length=24,
                                choices=languages)

    # The type of question.
    type = models.CharField(max_length=24, choices=question_types)

    # Is this question active or not. If it is inactive it will not be used
    # when creating a QuestionPaper.
    active = models.BooleanField(default=True)

    # Snippet of code provided to the user.
    snippet = models.CharField(max_length=256, blank=True)

    # Tags for the Question.
    tags = TaggableManager(blank=True)

    # user for particular question
    user = models.ForeignKey(User, related_name="user")

    def consolidate_answer_data(self, test_cases, user_answer):
        test_case_data_dict = []
        question_info_dict = {}

        for test_case in test_cases:
            kw_args_dict = {}
            pos_args_list = []

            test_case_data = {}
            test_case_data['test_id'] = test_case.id
            test_case_data['func_name'] = test_case.func_name
            test_case_data['expected_answer'] = test_case.expected_answer

            if test_case.kw_args:
                for args in test_case.kw_args.split(","):
                    arg_name, arg_value = args.split("=")
                    kw_args_dict[arg_name.strip()] = arg_value.strip()

            if test_case.pos_args:
                for args in test_case.pos_args.split(","):
                    pos_args_list.append(args.strip())

            test_case_data['kw_args'] = kw_args_dict
            test_case_data['pos_args'] = pos_args_list
            test_case_data_dict.append(test_case_data)

        # question_info_dict['language'] = self.language
        question_info_dict['id'] = self.id
        question_info_dict['user_answer'] = user_answer
        question_info_dict['test_parameter'] = test_case_data_dict
        question_info_dict['ref_code_path'] = self.ref_code_path
        question_info_dict['test'] = self.test

        return json.dumps(question_info_dict)

    def dump_into_json(self, question_ids, user):
        questions = Question.objects.filter(id__in = question_ids, user_id = user.id)
        questions_dict = []
        for question in questions:
            q_dict = {'summary': question.summary, 'description': question.description,
                        'points': question.points, 'test': question.test,
                        'ref_code_path': question.ref_code_path,
                        'options': question.options, 'language': question.language,
                        'type': question.type, 'active': question.active,
                        'snippet': question.snippet}
            questions_dict.append(q_dict)

        return json.dumps(questions_dict, indent=2)

    def load_from_json(self, questions_list, user):
        questions = json.loads(questions_list)
        for question in questions:
            question['user'] = user
            Question.objects.get_or_create(**question)

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

    # Whether skipped or not.
    skipped = models.BooleanField(default=False)

    def set_marks(self, marks):
        if marks > self.question.points:
            self.marks = self.question.points
        else:
            self.marks = marks

    def __unicode__(self):
        return self.answer

###############################################################################
class QuizManager(models.Manager):
    def get_active_quizzes(self):
        return self.filter(active=True)
###############################################################################
class Quiz(models.Model):
    """A quiz that students will participate in. One can think of this
    as the "examination" event.
    """

    course = models.ForeignKey(Course)

    # The start date of the quiz.
    start_date_time = models.DateTimeField("Start Date and Time of the quiz",
                                        default=timezone.now(),
                                        null=True)

    # The end date and time of the quiz
    end_date_time = models.DateTimeField("End Date and Time of the quiz",
                                        default=datetime(2199, 1, 1, tzinfo=tz),
                                        null=True)

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
    prerequisite = models.ForeignKey("Quiz", null=True, blank=True)

    # Programming language for a quiz
    language = models.CharField(max_length=20, choices=languages)

    # Number of attempts for the quiz
    attempts_allowed = models.IntegerField(default=1, choices=attempts)

    time_between_attempts = models.IntegerField("Number of Days",\
            choices=days_between_attempts)

    objects = QuizManager()

    class Meta:
        verbose_name_plural = "Quizzes"


    def is_expired(self):
        return not self.start_date_time <= timezone.now() < self.end_date_time

    def has_prerequisite(self):
        return True if self.prerequisite else False

    def __unicode__(self):
        desc = self.description or 'Quiz'
        return '%s: on %s for %d minutes' % (desc, self.start_date_time,
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

    def _get_questions_for_answerpaper(self):
        """ Returns fixed and random questions for the answer paper"""
        questions = []
        questions = list(self.fixed_questions.all())
        for question_set in self.random_questions.all():
            questions += question_set.get_random_questions()
        return questions

    def make_answerpaper(self, user, ip, attempt_num):
        """Creates an  answer paper for the user to attempt the quiz"""
        ans_paper = AnswerPaper(user=user, user_ip=ip, attempt_number=attempt_num)
        ans_paper.start_time = datetime.now()
        ans_paper.end_time = ans_paper.start_time \
                             + timedelta(minutes=self.quiz.duration)
        ans_paper.question_paper = self
        ans_paper.save()
        questions = self._get_questions_for_answerpaper()
        ans_paper.questions.add(*questions)
        ans_paper.questions_unanswered.add(*questions)
        return ans_paper

    def _is_questionpaper_passed(self, user):
        return  AnswerPaper.objects.filter(question_paper=self, user=user,
                                           passed = True).exists()

    def _is_attempt_allowed(self, user):
        attempts = AnswerPaper.objects.get_total_attempt(questionpaper=self,
                                                         user=user)
        return attempts != self.quiz.attempts_allowed

    def can_attempt_now(self, user):
        if self._is_attempt_allowed(user):
            last_attempt = AnswerPaper.objects.get_user_last_attempt(user=user,
                           questionpaper=self)
            if last_attempt:
                time_lag = (datetime.today() - last_attempt.start_time.replace(tzinfo=None)).days
                return time_lag >= self.quiz.time_between_attempts
            else:
                return True
        else:
            return False

    def _get_prequisite_paper(self):
        return self.quiz.prerequisite.questionpaper_set.get()

    def is_prerequisite_passed(self, user):
        if self.quiz.has_prerequisite():
            prerequisite = self._get_prequisite_paper()
            return prerequisite._is_questionpaper_passed(user)


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
class AnswerPaperManager(models.Manager):
    def get_all_questions(self, questionpaper_id, attempt_number,
                          status='completed'):
        ''' Return a dict of question id as key and count as value'''
        papers = self.filter(question_paper_id=questionpaper_id,
                             attempt_number=attempt_number, status=status)
        all_questions = list()
        questions = list()
        for paper in papers:
            all_questions += paper.get_questions()
        for question in all_questions:
            questions.append(question.id)
        return Counter(questions)

    def get_all_questions_answered(self, questionpaper_id, attempt_number,
                                   status='completed'):
        ''' Return a dict of answered question id as key and count as value'''
        papers = self.filter(question_paper_id=questionpaper_id,
                             attempt_number=attempt_number, status=status)
        questions_answered = list()
        for paper in papers:
            for question in filter(None, paper.get_questions_answered()):
                if paper.is_answer_correct(question):
                    questions_answered.append(question.id)
        return Counter(questions_answered)

    def get_attempt_numbers(self, questionpaper_id, status='completed'):
        ''' Return list of attempt numbers'''
        attempt_numbers = self.filter(
            question_paper_id=questionpaper_id, status=status
        ).values_list('attempt_number', flat=True).distinct()
        return attempt_numbers

    def has_attempt(self, questionpaper_id, attempt_number, status='completed'):
        ''' Whether question paper is attempted'''
        return self.filter(question_paper_id=questionpaper_id,
                           attempt_number=attempt_number, status=status).exists()

    def get_count(self, questionpaper_id, attempt_number, status='completed'):
        ''' Return count of answerpapers for a specfic question paper
            and attempt number'''
        return self.filter(question_paper_id=questionpaper_id,
                           attempt_number=attempt_number, status=status).count()

    def get_question_statistics(self, questionpaper_id, attempt_number,
                                status='completed'):
        ''' Return dict with question object as key and list as value
            The list contains two value, first the number of times a question
            was answered correctly, and second the number of times a question
            appeared in a quiz'''
        question_stats = {}
        questions_answered = self.get_all_questions_answered(questionpaper_id,
                                                             attempt_number)
        questions = self.get_all_questions(questionpaper_id, attempt_number)
        all_questions = Question.objects.filter(
            id__in=set(questions)
        ).order_by('type')
        for question in all_questions:
            if question.id in questions_answered:
                question_stats[question] = [questions_answered[question.id],
                                            questions[question.id]]
            else:
                question_stats[question] = [0, questions[question.id]]
        return question_stats

    def _get_answerpapers_for_quiz(self, questionpaper_id, status=False):
        if not status:
            return self.filter(question_paper_id=questionpaper_id)
        else:
            return self.filter(question_paper_id=questionpaper_id,
                                status="completed")


    def _get_answerpapers_users(self, answerpapers):
        return answerpapers.values_list('user', flat=True).distinct()

    def get_latest_attempts(self, questionpaper_id):
        papers = self._get_answerpapers_for_quiz(questionpaper_id)
        users = self._get_answerpapers_users(papers)
        latest_attempts = []
        for user in users:
            latest_attempts.append(self._get_latest_attempt(papers, user))
        return latest_attempts

    def _get_latest_attempt(self, answerpapers, user_id):
        return answerpapers.filter(user_id=user_id).order_by('-attempt_number')[0]

    def get_user_last_attempt(self, questionpaper, user):
        attempts = self.filter(question_paper=questionpaper,
                               user=user).order_by('-attempt_number')
        if attempts:
            return attempts[0]

    def get_user_answerpapers(self, user):
        return self.filter(user=user)

    def get_total_attempt(self, questionpaper, user):
        return self.filter(question_paper=questionpaper, user=user).count()

    def get_users_for_questionpaper(self, questionpaper_id):
        return self._get_answerpapers_for_quiz(questionpaper_id, status=True)\
            .values("user__id", "user__first_name", "user__last_name")\
            .distinct()

    def get_user_all_attempts(self, questionpaper, user):
        return self.filter(question_paper=questionpaper, user=user)\
                            .order_by('-attempt_number')

    def get_user_data(self, user, questionpaper_id, attempt_number=None):
        if attempt_number is not None:
            papers = self.filter(user=user, question_paper_id=questionpaper_id,
                                     attempt_number=attempt_number)
        else:
            papers = self.filter(user=user, question_paper_id=questionpaper_id)\
                                    .order_by("-attempt_number")
        data = {}
        profile = user.profile if hasattr(user, 'profile') else None
        data['user'] = user
        data['profile'] = profile
        data['papers'] = papers
        data['questionpaperid'] = questionpaper_id
        return data


###############################################################################
class AnswerPaper(models.Model):
    """A answer paper for a student -- one per student typically.
    """
    # The user taking this question paper.
    user = models.ForeignKey(User)

    questions = models.ManyToManyField(Question, related_name='questions')

    # The Quiz to which this question paper is attached to.
    question_paper = models.ForeignKey(QuestionPaper)

    # The attempt number for the question paper.
    attempt_number = models.IntegerField()

    # The time when this paper was started by the user.
    start_time = models.DateTimeField()

    # The time when this paper was ended by the user.
    end_time = models.DateTimeField()

    # User's IP which is logged.
    user_ip = models.CharField(max_length=15)

    # The questions unanswered
    questions_unanswered = models.ManyToManyField(Question,
                                            related_name='questions_unanswered')

    # The questions answered
    questions_answered = models.ManyToManyField(Question,
                                            related_name='questions_answered')

    # All the submitted answers.
    answers = models.ManyToManyField(Answer)

    # Teacher comments on the question paper.
    comments = models.TextField()

    # Total marks earned by the student in this paper.
    marks_obtained = models.FloatField(null=True, default=None)

    # Marks percent scored by the user
    percent = models.FloatField(null=True, default=None)

    # Result of the quiz, True if student passes the exam.
    passed = models.NullBooleanField()

    # Status of the quiz attempt
    status = models.CharField(max_length=20, choices=test_status,\
            default='inprogress')

    objects = AnswerPaperManager()

    def current_question(self):
        """Returns the current active question to display."""
        if self.questions_unanswered.all():
            return self.questions_unanswered.all()[0]

    def questions_left(self):
        """Returns the number of questions left."""
        return self.questions_unanswered.count()

    def completed_question(self, question_id):
        """
            Adds the completed question to the list of answered
            questions and returns the next question.
        """
        self.questions_answered.add(question_id)
        self.questions_unanswered.remove(question_id)

        return self.current_question()

    def skip(self, question_id):
        """
            Skips the current question and returns the next sequentially
             available question.
        """
        questions = self.questions_unanswered.all()
        question_cycle = cycle(questions)
        for question in question_cycle:
            if question.id==int(question_id):
                return question_cycle.next()

    def time_left(self):
        """Return the time remaining for the user in seconds."""
        dt = datetime.now() - self.start_time.replace(tzinfo=None)
        try:
            secs = dt.total_seconds()
        except AttributeError:
            # total_seconds is new in Python 2.7. :(
            secs = dt.seconds + dt.days*24*3600
        total = self.question_paper.quiz.duration*60.0
        remain = max(total - secs, 0)
        return int(remain)

    def _update_marks_obtained(self):
        """Updates the total marks earned by student for this paper."""
        marks = sum([x.marks for x in self.answers.filter(marks__gt=0.0)])
        if not marks:
            self.marks_obtained = 0
        else:
            self.marks_obtained = marks

    def _update_percent(self):
        """Updates the percent gained by the student for this paper."""
        total_marks = self.question_paper.total_marks
        if self.marks_obtained is not None:
            percent = self.marks_obtained/self.question_paper.total_marks*100
            self.percent = round(percent, 2)

    def _update_passed(self):
        """
            Checks whether student passed or failed, as per the quiz
            passing criteria.
        """
        if self.percent is not None:
            if self.percent >= self.question_paper.quiz.pass_criteria:
                self.passed = True
            else:
                self.passed = False

    def _update_status(self, state):
        """ Sets status as inprogress or completed """
        self.status = state

    def update_marks(self, state='completed'):
        self._update_marks_obtained()
        self._update_percent()
        self._update_passed()
        self._update_status(state)
        self.save()

    def set_end_time(self, datetime):
        """ Sets end time """
        self.end_time = datetime
        self.save()

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

    def get_questions(self):
        return self.questions.all()

    def get_questions_answered(self):
        return self.questions_answered.all()

    def get_questions_unanswered(self):
        return self.questions_unanswered.all()

    def is_answer_correct(self, question_id):
        ''' Return marks of a question answered'''
        return self.answers.filter(question_id=question_id,
                                   correct=True).exists()

    def is_attempt_inprogress(self):
        if self.status == 'inprogress':
            return self.time_left()> 0

    def get_previous_answers(self, question):
        if question.type == 'code':
            return self.answers.filter(question=question).order_by('-id')

    def __unicode__(self):
        u = self.user
        return u'Question paper for {0} {1}'.format(u.first_name, u.last_name)


###############################################################################
class AssignmentUpload(models.Model):
    user = models.ForeignKey(Profile)
    assignmentQuestion = models.ForeignKey(Question)
    assignmentFile = models.FileField(upload_to=get_assignment_dir)


################################################################################
class TestCase(models.Model):
    question = models.ForeignKey(Question, blank=True, null = True)

    # Test case function name
    func_name = models.CharField(blank=True, null = True, max_length=200)

    # Test case Keyword arguments in dict form
    kw_args = models.TextField(blank=True, null = True)

    # Test case Positional arguments in list form
    pos_args = models.TextField(blank=True, null = True)

    # Test case Expected answer in list form
    expected_answer = models.TextField(blank=True, null = True)
