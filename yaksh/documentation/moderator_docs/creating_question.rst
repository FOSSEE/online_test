=========
Questions
=========

Setting up questions
--------------------

	Setting up questions is the most important part of the Yaksh experience. Questions can be of multiple types i.e Multiple choice questions (MCQ), multiple correct choices (MCC), Coding questions and assignment upload types.

	To set up a question click on the questions link in the navigation bar.

	.. image:: ../images/questions.jpg 
	
	To add a question click on the **Add Question** button

	.. image:: ../images/add_question.jpg

	* **Summary**- Summary or the name of the question.

	* **Language** - Programming language on which the question is based.

	* **Active** -  If the question is active to attempt or not.

	* **Type** - Type of the question. i.e Multiple Choice, Multiple Correct Choice, Code and Assignment Upload.

	* **Description** - The actual question description is to be written. 

	.. note::  To add codes in questions please use html <code> and <br> tags.

	* **Tags** - Type of label or metadata tag making it easier to find specific type of questions.

	* **Snippet** - Snippet is used to give any default value or default code or command. This will be displayed in the answer form. This is used only for code questions.

	* **Test case type** - Test cases or answers are to be added. There are multiple type of test cases - 
		
		* Standard Test Case which is an assertion based testcase.
		* Stdout Based Test Case is stdout based test where moderator can provide expected output (Only for Python).
		* MCQ Based Test Case is testcase for Mcqs and Mccs.

How to write Test cases
-----------------------
	
	The following explains different methods to write test cases.

	* **Create Standard Test Case**

		Select Standard Test Case and click on Save & Add Testcase button to save the question.

		* For Python:
			In the test case field write a python assert to check the user code.
			For e.g. :: 
				
				assert fact(3) == 6
			
			for program of factorial.

		* For C, C++ and Java:
			In Test Case Field add the test case file path.

		Check Delete Field if a test case is to be removed.

		Finally click on Save & Add Testcase Button to save the test case.


	* **Create Standard Input/Output Based Test Case**

			Select StdIO Based TestCase from Test Case Type field and click on Save & Add Testcase button to save the question.

			In Expected input field, enter the value(s) that will be passed to the students' code through a standard I/O stream.

			.. note::  If there are multiple input values in a test case, enter the values in new line.

			In Expected Output Field, enter the expected output for that test case. For e.g type 6 if the output of the user code is 6.

	* **Create MCQ Based Test Case**

		Select MCQ Based TestCase from Test Case Type field and click on Save & Add Testcase button to save the question.

		In Options Field type the option check the correct checkbox if the current option is correct and click on Save & Add Testcase button to save each option.

	* **Create Python Hook Based Questions**

		.. note:: Current implementation of this works only on Standard I/O based test case type questions. Also, **No expected input and output can be given to the question if its Python hook based type.** A Feature to add expected input is in progress.

		To create a Python Hook Based Question, select test case type as StdIO test case. This will enable the Hook text box. The function **python_hook** is passed with arguments, user_answer and user_output, where user_answer is the code that the student typed and user_output is the standard output of the code. The moderator can then examine these two parameters by writing rigorous test cases and finally returning success and err.

		success, err will be True and "Correct answer" respectively if the checker passes. If the checker fails, success will be False and err will be "Incorrect answer".

		Lastly, click on Save & Add Testcase button to save the question.

		.. note:: It is advisible to pass the user output and the moderator expected output in the err string variable, for better understanding to students.




Features in Question
--------------------
	
	* **Download Questions**

			Select questions from the list of question displayed on the Questions page. Click on the Download Selected button to download the questions. This will create a json file of the Questions selected.

	* **Upload Questions**
			
			Click on the Upload File button. This will open up a window. Select the json file of questions and click Ok and the questions will be uploaded and displayed on the Questions page.

	* **Test Questions**
			
			Select questions from the list of question displayed on the Questions page. Click on Test selected button. This will take you to a quiz with the selected questions. 

			.. Note:: This will not create an actual quiz but a trial quiz. This quiz is hidden from the students and only for moderator to view. You can delete the quiz from moderator's dashboard. 

