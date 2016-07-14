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

	* ** Snippet** - Snippet is used to give any default value or default code or command. This will be displayed in the answer form. This is used only for code questions.

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


	* **Create Standard out Based Test Case**

			Select Stdout Based TestCase from Test Case Type field and click on Save & Add Testcase button to save the question.

			In Expected Output Field type the expected output for a particular question. For e.g type 6 if the output of the user code is 6.

	* **Create MCQ Based Test Case**

		Select MCQ Based TestCase from Test Case Type field and click on Save & Add Testcase button to save the question.

		In Options Field type the option check the correct checkbox if the current option is correct and click on Save & Add Testcase button to save each option.


Features in Question
--------------------
	
	* **Download Questions**

			Select questions from the list of question displayed on the Questions page. Click on the Download Selected button to download the questions. This will create a json file of the Questions selected.

	* **Upload Questions**
			
			Click on the Upload File button. This will open up a window. Select the json file of questions and click Ok and the questions will be uploaded and displayed on the Questions page.

	* **Test Questions**
			
			Select questions from the list of question displayed on the Questions page. Click on Test selected button. This will take you to a quiz with the selected questions. **Note** - This will not create an actual quiz but a trial quiz. This quiz is hidden from the students and only for moderator to view. You can delete the quiz from moderator's dashboard. 