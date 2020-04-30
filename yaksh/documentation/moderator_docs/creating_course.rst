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
            Instructions for the course.
        * **Start Date and Time for enrollment of course**
            If the enrollment of the course should be available only after a set date and time.
        * **End Date and Time for enrollment of course**
            If the enrollment of the course should be available only before a set date and time.
        * **Grading System**
            Add a grading system to the course.
        * **View Grade**
            This field allows the student to view the grade if checked else grade is not visible to student.


Features in Courses
-------------------

     Click on the Courses link on the navigation bar.

     .. image:: ../images/course_features.jpg

     This page shows all the courses created by a moderator and all the courses allotted to a moderator.

     The following options are available in the courses page

        * **My Courses**
            Click to show all the courses created by you.
        * **Add/Edit Course**
            Click to add the details of a new course.
        * **Add/View Grading Systems**
            Add or view grading systems. More info on creating grading system
        * **Search/Filter Courses**
            Search the courses by name or filter the course with active and inactive status.
        * **Course Name**
            Shows course name of all the created and allotted courses.
        * **Edit Course**
            Click this button to edit the corresponding course details.
        * **Manage Course**
            This provides more options for the course. For e.g. setting up modules,
            lessons, quizzes, practice exercises, students enrollments etc.
        * **Download**
            This button provides two options. One is to download the course CSV containing student data, Other is to download entire course for offline viewing.
        * **Clone Course**
            Click to create a copy of a course along with its modules, lessons and quizzes.
        * **Activate/Deactivate Course**
            Toogle to activate or deactivate the course.
    

Manage Course
--------------------------

    Click on the Manage course button to view the course details page.

    .. image:: ../images/course_details_features.jpg

    Following are the features for course details -

        * **Enroll Students**
            * **Upload Users**
                Create and enroll users automatically by uploading a csv of the users. The mandatory fields for this csv are - **firstname, lastname, email**. Other fields like **username, password, institute, roll_no, department, remove** fields are optionals.
            * **Requests**
                This is a list of students who have requested to be enrolled in the course. Moderator can enroll or reject selected students.
            * **Enrolled**
                This is a list of students who have been enrolled in the course. Moderator can reject enrolled students.
            * **Rejected**
                This is a list of students who have been rejected for enrollment in a course. Moderator can enroll rejected students.
        * **Course Modules**
            Moderator can send mail to all enrolled students or selected students.

            .. image:: ../images/course_modules.jpg

            * **Add Module**
                Click on this button to add a module to the course. Fill the details
                of the module and save it.

                After creating a module for the course, following options are available:

                * **Add Lesson**
                    Add lesson to the corresponding module.

                * **Add Quiz**
                    Add a graded quiz to the correspoding module.

                * **Add Exercise**
                    Add a ungraded practice exercise to the corresponding module.

                * **Design Module**
                    This option allows you to change the order of the units added to
                    the module, check for prerequisites of the module and remove a unit from the module.
        * **Design Course**
            Clicking on **Design Course** will show the below page.

            .. image:: ../images/design_course.jpg

            * **Available Modules** contains all the modules that are not added to a course.

                To add a module to the course select the checkbox besides the desired module to be added and click **Add to course** button.

            * **Chosen Modules** contains all the modules that are added to a course.

                Following parameters can be changed while designing a course:

                * **Order**
                    Order in which modules are shown to a student.

                    To change a module's order change the value to a desired order in the textbox under **Order** column and click **Change order**.

                * **Check Prerequisite Completion**
                    Check if previous module is completed. Default value is **Yes**.

                    For e.g., Assuming a course contains modules **Demo Module** and **Trial for trial_course** in the given order; a student has to first complete **Demo module** to attempt **Trial for trial_course** if the **Check Prerequisite** value for **Trial for trial_course** is checked **Yes**.

                    **Currently** column shows the current value of **Change Prerequisite Completion** which in this case is **Yes**.

                    Select the checkbox from **Change** column under **Check Prerequisite Completion** and click **Change Prerequisite Completion** button to change the value.

                * **Check Prerequisite Passing**
                    Check if previous module is completed. Default value is **Yes**. This is similar to **Check Prerequisite Completion** except that it checks if all the quizzes in the module are passed or not.

                    **Currently** column shows the current value of **Change Prerequisite Passing** which in this case is **Yes**.

                    Select the checkbox from **Change** column under **Check Prerequisite Passing** and click **Change Prerequisite Passing** button to change the value.

                * **Remove Module**
                    To remove a module from the course select the checkbox beside every module and click **Remove from course** button.
        * **Course Progress**
            It shows progress made by the students in the course. Moderator can also
            download the course progress data.
        * **Send Mail**
            Moderator can send mail to all enrolled students or selected students.
        * **Add Teachers/TAs**
            Moderator can search for the users by username, email, first name and last name to add as Teacher/TA to the course.
        * **Current Teachers/TAs**
            It shows all the added Teachers/TAs to the course. Added users can view and edit the course, modules, lessons and quizzes available in the course.
