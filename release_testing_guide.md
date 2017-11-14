Release testing guide:
======================
   To be followed before every release.

1. Installation and deployment:
   ----------------------------
   a. Follow the instruction guide to see if all steps work without issues.
   b. Try login in with admin, student, teacher
   c. Try removing any folder with code server inside docker.
   d. Repeat step c with `invoke --unsafe`

2. Authentication:
   ---------------
   a. **Signing up on Yaksh:**
      - On landing page, click on sign up button.
      - On the user registration form, try registering with an empty field.This should redirect to the same page with the field necessary notification.
      - Try the same thing with all fields filled. This should register and redirect to quizzes page.

   b. **Login with Google/Facebook oauth:**
   	  - Check if google facebook oauth authentication works or not.

   c. **Forgot Password:**
   	  - Click on the Forgot Password button.
   	  - Enter valid email id and click on reset.
   	  - Check mail, click on the link and change password.
   	  - Check if the new password is valid.

   d. **Change Password**
      - Log in as student and as moderator separately and click on change password.
      - Try to change password and check if the password is changed.


3. Exam interface.

4. Grading and answerpaper interface.

5. Regrading interface.
6. 