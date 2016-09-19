import os
import sys
from django.core.management.base import BaseCommand
from yaksh.models import Course, Question, Quiz, QuestionPaper, Profile, FileUpload
from yaksh.file_utils import extract_files
from yaksh.views import add_to_group
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import Group
from datetime import datetime, timedelta


def create_demo_course():
    """ creates a demo course, quiz """

    success = False
    group = Group.objects.filter(name="moderator")
    if group:
        print("Creating Demo User...")
        # create a demo user
        user, u_status = User.objects.get_or_create(username='yaksh_demo_user',
                                                    email='demo@test.com')
        user.set_password("demo")
        user.save()
        Profile.objects.get_or_create(user=user, roll_number=0,
                                      institute='demo_institute',
                                      department='demo_department',
                                      position='Faculty')
        # add demo user to moderator group
        demo_user = User.objects.filter(username='yaksh_demo_user')
        add_to_group(demo_user)
    else:
        print ("Please Create 'moderator' Group")
        print ("Unable to create Demo Course")
        sys.exit()

    print("Creating Demo Course...")
    # create a demo course
    course, c_status = Course.objects.get_or_create(name="Yaksh Demo course",
                                                    enrollment="open",
                                                    creator=user)

    print("Creating Demo Quiz...")
    demo_quiz = Quiz.objects.filter(course=course)
    if not demo_quiz:
    # create a demo quiz
        demo_quiz = Quiz.objects.get_or_create(start_date_time=timezone.now(),
                                        end_date_time=timezone.now() + timedelta(176590),
                                        duration=30, active=True,
                                        attempts_allowed=-1,
                                        time_between_attempts=0,
                                        description='Yaksh Demo quiz', pass_criteria=0,
                                        language='Python', prerequisite=None,
                                        course=course)
    else:
        print("Demo Quiz Already Created")

    print("Creating Demo Questions...")
    questions = Question.objects.filter(active=True, summary="Yaksh Demo Question")
    files = FileUpload.objects.filter(question__in=questions)
    if not files:
        #create demo question
        f_path = os.path.join(os.getcwd(), 'yaksh', 'fixtures', 'demo_questions.json')
        zip_file_path = os.path.join(os.getcwd(), 'yaksh', 'fixtures', 'demo_questions.zip')
        extract_files(zip_file_path)
        ques = Question()
        ques.read_json("questions_dump.json", user)

    if questions:
        print("Creating Demo Question Paper...")
        # create a demo questionpaper
        que_ppr = QuestionPaper.objects.filter(quiz=demo_quiz[0])
        if not que_ppr:
            question_paper, q_ppr_status = QuestionPaper.objects.get_or_create(quiz=demo_quiz[0],
                                                                 total_marks=5.0,
                                                                 shuffle_questions=True
                                                                 )
            # add fixed set of questions to the question paper
            for question in questions:
                question_paper.fixed_questions.add(question)
        else:
            print("Question Paper Already Created")
    else:
        print("Questions Not Found Please Check Question Summary")

    success = True
    return success


class Command(BaseCommand):
    help = "Create a Demo Course, Demo Quiz"

    def handle(self, *args, **options):
        """ Handle command to create demo course """
        status = create_demo_course()
        if status:
            self.stdout.write("Successfully Created")
        else:
            self.stdout.write("Unable to create Demo Course")
