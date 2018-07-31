.. _creating_lessons_modules:

===================
Lessons and Modules
===================

Courses can have lessons and quizzes encapsulated using a module.

	* **What is a lesson?**
		A lesson can be any markdown text with/or an embedded video of a particular topic.

	* **What is a module?**
		A Module is a collection of lessons and courses clubbed together by similar idea/content. A module can have its own description as a markdown text with/or an embedded video.


Setting up a Lesson
-----------------------

	To create a new lesson or edit any existing lesson click on **Add/View Lessons** from courses page.

	.. image:: ../images/view_lessons.jpg

	This page shows all the lessons created by you.

	Click on **Add new Lesson** to add new lesson. Click on the **lesson name** to edit a lesson.

	.. image:: ../images/add_lesson.jpg

	* **Name** - Name of the lesson.
	* **Description** - Description can be any markdown text or embedded video link.
	* **Active** - Activate/Deactivate a lesson
	* **Lesson files** - Add files to the lesson which will be available for students to view and download. All the uploaded files will be shown below.

	Click on **Save** to save a lesson.

	Click on **Preview Lesson Description** to preview lesson description. Markdown text from the description is converted to html and is displayed below.

	Select the checkbox beside each uploaded file and click on **Delete files** to remove files from the lesson.

	Click on **Embed Video Link** to embed a video. On clicking a pop-up will be shown.

	.. image:: ../images/embed_video.jpg

	Enter the url and click on **Submit** a html div is generated in the text area below.
	Click on the button below the textarea to copy the textarea content. This html div can then be added in the lesson description.


Setting up a Module
-----------------------

	To create a new module or edit any existing module click on **Add/View Modules** from courses page.

	.. image:: ../images/view_modules.jpg

	This page shows all the modules created by you.

	Creating a new module or editing an existing module is similar to a lesson creation with a difference that a module has no option to upload files.


Design a Module
---------------

	To add lessons or quizzes to a module click on **Add Quizzes/Lessons for <module-name>**.

	.. image:: ../images/design_module.jpg

	**Available Lessons and quizzes** contains all the lessons and quizzes that are not added to a module.

	To add a lesson or a quiz to the module select the checkbox beside every lesson or quiz and click **Add to Module** button.

	**Chosen Lesson and quizzes** contains all the lessons and quizzes that are added to a module.

	A lesson or quiz added to a module becomes a unit. A unit has following parameters to change:

		**Order** - Order in which units are shown to a student.

			To change a unit's order change the value in the textbox under **Order** column and click **Change order**.

		**Check Prerequisite** - Check if previous unit is completed. Default value is **Yes**.
			For e.g. A student has to first complete **Yaksh Demo quiz** to attempt **Demo Lesson** if the **Check Prerequisite** value for **Demo Lesson** is checked **Yes**.

			**Currently** column shows the current value of **Check Prerequisite** which in this case is **Yes**.

			Select the checkbox from **Change** column under **Check Prerequisite** and click **Change Prerequisite** button to change the value.

	To remove a lesson or a quiz from the module select the checkbox beside every lesson or quiz and click **Remove from Module** button.





