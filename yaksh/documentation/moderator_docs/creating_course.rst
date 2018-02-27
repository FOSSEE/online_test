=======
Courses
=======

For students to take a quiz, it is imperative for the moderator to create a course first. 
A course can contain several modules and a module can contain several lessons and/or quizzes.

To create modules, lessons and quizzes go to the :doc:`creating_lessons_modules`
and :doc:`creating_quiz` section of the documentation.

Setting up a new course
-----------------------
    To create a course, click on the Add New Course button on the moderator's dashboard. This will lead you to a create add course page, where you need to fill in the following fields.

        .. image:: ../images/create_course.jpg

        * **Name**
            Name of the Course
        * **Enrollment**
             Open enrollment is open to all students. Enroll Request requires students to send a request which the moderator can accept or reject.
        * **Active**
            If the course should be active for students to take the quiz. The status of the course can be edited later.
        * **Code**
            If the course should be hidden and only accessible to students possessing the correct course code.
        * **Instructions**
            Instructions for the course
        * **Start Date and Time for enrollment of course**
            If the enrollment of the course should be available only after a set date and time
        * **End Date and Time for enrollment of course**
            If the enrollment of the course should be available only before a set date and time


Features in Courses
-------------------

     Click on the Courses link on the navigation bar.

     .. image:: ../images/course_features.jpg

     This page shows all the courses created by a moderator and all the courses allotted to a moderator.

     The following features are available for courses

        * **Course Name**
            Click on course name link to view all the enrolled, rejected and requested students list. Moderator can accept or reject the student.
        * **Module Name**
            Click to edit a module added to the course
        * **Lesson or Quiz Name**
            Click to edit a Lesson or Quiz added to the course

            In edit quiz you can also attempt the quiz in two modes - 
                * **God Mode** - In God mode you can attempt quiz without any time or eligibilty constraints.
                * **User Mode** - In user mode you can attempt quiz the way normal users will attempt i.e.
                    
                    * Quiz will have the same duration as that of the original quiz.
                    * Quiz won't start if the course is inactive or the quiz time has expired.
        * **Add Quizzes/Lessons for <module-name>**
            Click to add/delete lessons or quizzes.
        * **Design Course**
            Click to add/delete modules of a course.
        * **Add Teacher**
            Click to add teachers for the course. The teachers can edit and modify only the specific course that are allotted to them.
        * **Clone Course**
            Click to create a copy of a course along with its modules, lessons and quizzes.
        * **Teachers added to the course**
            This shows all the teachers added to a particular course.
        * **Download CSV for the entire course**
            This downloads the CSV file containing the performance of all students in every quiz for a given course.
        * **Edit Course**
            Click to edit the details of an existing course.
        * **Deactivate/Activate Course**
            Click to deactivate or activate the course.
        * **My Courses**
            Click to show all the courses created by you.
        * **Allotted courses**
            Click to view all the courses allotted to you.
        * **Add New Course**
            Click to open course form to create new course.
        * **Add/View Quizzes**
            Click to view all the quizzes created by you or add new quiz.
        * **Add/View Lessons**
            Click to view all the lessons created by you or add new lesson.
        * **Add/View Modules**
            Click to view all the modules created by you or add new module.


Design a Course
---------------
    
    Clicking on **Design Course** will show the below page.

    .. image:: ../images/design_course.jpg

    **Available Modules** contains all the modules that are not added to a course.

    To add a module to the course select the checkbox besides the desired module to be added and click **Add to course** button.

    **Chosen Modules** contains all the modules that are added to a course.

    Following parameters can be changed while designing a course:

        **Order** - Order in which modules are shown to a student.

            To change a module's order change the value to a desired index/order in the textbox under **Order** column and click **Change order**.

        **Check Prerequisite** - Check if previous module is completed. Default value is **Yes**.
            For e.g., Assuming a course contains modules **Demo Module** and **Python module** in the given order; a student has to first complete **Demo module** to attempt **Python Module** if the value is **Yes**.

            **Currently** column shows the current value of **Check Prerequisite** which in this case is **Yes**.

            Select the checkbox from **Change** column under **Check Prerequisite** and click **Change Prerequisite** button to change the value.

    To remove a module from the course select the checkbox beside every module and click **Remove from course** button.
    

Features in Course Details
--------------------------

    Click on a given course name to go to the course details page.

    .. image:: ../images/course_details_features.jpg

    Following are the features for course details -

        * **Requests**
            This is a list of students who have requested to be enrolled in the course. Moderator can enroll or reject selected students.
        * **Enrolled**
            This is a list of students who have been enrolled in the course. Moderator can reject enrolled students.
        * **Rejected**
            This is a list of students who have been rejected for enrollment in a course. Moderator can enroll rejected students.
        * **Upload Users**
            Create and enroll users automatically by uploading a csv of the users. The mandatory fields for this csv are - **firstname, lastname, email**. Other fields like **username, password, institute, roll_no, department, remove** fields are optionals.
        * **Send Mail**
            Moderator can send mail to all enrolled students or selected students.
        * **View Course Status**
            View students' progress through the course.
