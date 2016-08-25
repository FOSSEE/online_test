import os
from django.core.management.base import BaseCommand
from yaksh.models import Course, Question, Quiz, QuestionPaper, Profile, FileUpload
from yaksh.views import extract_files, read_json
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files import File
from datetime import datetime, timedelta
import pytz
import zipfile


def create_demo_course():
    """ creates a demo course, quiz """

    success = False
    print("Creating Demo User...")
    # create a demo user
    user, u_status = User.objects.get_or_create(username='demo_user',
                                                password='demo',
                                                email='demo@test.com')
    Profile.objects.get_or_create(user=user, roll_number=0,
                                  institute='demo_institute',
                                  department='demo_department',
                                  position='Faculty')

    print("Creating Demo Course...")
    # create a demo course
    course, c_status = Course.objects.get_or_create(name="Demo_course",
                                                    enrollment="open",
                                                    creator=user)

    print("Creating Demo Quiz...")
    # create a demo quiz
    quiz, q_status = Quiz.objects.get_or_create(start_date_time=timezone.now(),
                                      end_date_time=timezone.now() + timedelta(176590),
                                      duration=30, active=True,
                                      attempts_allowed=-1,
                                      time_between_attempts=0,
                                      description='Demo_quiz', pass_criteria=0,
                                      language='Python', prerequisite=None,
                                      course=course)

    print("Creating Demo Questions...")
    #create demo question
    f_path = os.path.join(os.getcwd(), 'yaksh', 'fixtures', 'demo_questions.json')
    zip_file_path = os.path.join(os.getcwd(), 'yaksh', 'fixtures', 'demo_questions.zip')
    extract_files(zip_file_path)
    read_json("questions_dump.json", user)

    questions = Question.objects.filter(active=True, summary="Demo_Question")

    print("Creating Demo Question Paper...")
    # create a demo questionpaper
    question_paper, q_ppr_status = QuestionPaper.objects.get_or_create(quiz=quiz,
                                                         total_marks=5.0,
                                                         shuffle_questions=True
                                                         )
    # add fixed set of questions to the question paper
    for question in questions:
        question_paper.fixed_questions.add(question)

    success = True
    return success


class Command(BaseCommand):
    help = "Create a Demo Course, Demo Quiz"

    def handle(self, *args, **options):
        """ Handle command to create demo course """
        status = create_demo_course()
        if status:
            self.stdout.write("Successfully Created")
