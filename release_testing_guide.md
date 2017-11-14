Release testing guide:
======================
   To be followed before every release.

1. Installation and deployment:
   ----------------------------
   a. Follow the instruction guide to see if all steps work without issues.

   b. Try login in with admin, student, teacher individually.

   c. Try to run `rm -rf ../*` from quiz interface for bash to check if student is nobody
      inside docker.

   d. Try to run `rm -rf ../*` from quiz interface for bash with `invoke start --unsafe`
      to check if student is not nobody.


2. Authentication:
   ---------------
   a. **Signing up on Yaksh:**
      - On landing page, click on sign up button.
      - On the user registration form, try registering with an empty field.This should redirect to the same page with the field necessary notification.
      - Try the same thing with all fields filled. This should register and redirect to quizzes page.

   b. **Login with Google/Facebook oauth:**
         (To be done from live server only)
   	  - Check if google facebook oauth authentication works or not.

   c. **Forgot Password:**
   	  - Click on the Forgot Password button.
   	  - Enter valid email id and click on reset.
   	  - Check mail, click on the link and change password.
   	  - Check if the new password is valid.

   d. **Change Password**
      - Log in as student and as moderator separately and click on change password.
      - Try to change password and check if the password is changed.

   e. **Edit Profile**
      - Try to edit profile and check if data is being updated properly.

3. Student interface.
   ------------------

   a. Search for a course using course code.

   b. Try to attempt Demo Quiz.

   c. In quiz attempt all types of questions. Try to attempt same questions with right answer
      and then wrong answer and vice versa.

   d. Try to quit the quiz in between with some questions still remaining and comeback to
      the interface by clicking no to check if it safely goes back to the quiz.

   e. Try to quit the quiz in between, with some questions still remaining and quit the quiz by
      clicking yes to check if it safely quits the quiz. 

   f. Try to close the browser in between the quiz and restart quiz again to check if quiz
      resumes properly.

   g. Try to move back and forth using browser back button to check if multiple objects
      error occurs.

   h. Attempt all the questions and check if revisiting questions works.

   i. Attempt all the questions and try to quit and click on no and comeback to interface.

   j. Attempt all the questions and try to quit and click on yes and quit the quiz.

   k. Try steps c to g for single question in a quiz.

   l. Try to attempt the questions until time runs out and check if timeout closes the quiz
      safely.

   m. Try view answerpaper if student is getting proper marks.


4. Moderator Interface.
   --------------------

   a. Try to hit the quiz link from moderator dashboard to check if it redirects properly to
      monitor page for that quiz.

   b. Click on create demo course and check if course and quizzes are created.

   c. **Monitor**
      - Click on download csv link and check if user data is being recorded properly.
      - Click on student name link and check if user answers are being submitted properly,
         marks are being updated properly.
      - Click on question statistics to check proper statistics are being shown.

   d. **Grade User**
      - Click on quiz link and then click on student name link and check
         if user answers are being shown properly.
      - Try to update marks and add comments for a student.
      - Check marks for each question and total marks to make sure marks are updated properly.
      - For non coding questions make sure the latest attempt is given marks.
      - Try to check multiple attempts for a user.
      - Check for partial grading marks for a question.
      - Try to download assignments per quiz and per user.

   e. **Courses**
      - Try to enroll/reject few students for a course.
      - Create some quizzes for a course.
      - Try to add teachers to the course.
      - Download course csv to get enrolled students list and quiz marks.
      - Check if teachers have all privileges which a moderator has for a course.
      - Set enrollment time for a course and check if students are not enrolled after the
         end time.

   f. **Regrade**
      - Try to regrade papers per user, per question and per quiz

   g. **Questions**
      - Try to create some questions.
      - Try to upload questions.
      - Try to download questions.
      - Try to filter questions using filters and tags.
      - Select some questions and test selected questions. 

   h. **Quiz**
      - Try to attempt user mode and god mode for a quiz.
      - Try to change active status, start time, end time and attempt the quiz.

   i. **Question Paper**
      - Add fixed questions, random questions in a questionpaper and attempt the quiz.
      - Enable auto shuffle and try to attempt the quiz.

