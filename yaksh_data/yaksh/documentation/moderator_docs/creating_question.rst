=========
Questions
=========

Setting up questions
--------------------

	Setting up questions is the most important part of the Yaksh experience. Questions can be of multiple types i.e Multiple choice questions (MCQ), Multiple correct choices (MCC), Coding questions and assignment upload types.

	To set up a question click on the questions link in the navigation bar.

	.. image:: ../images/questions.jpg 
	
	To add a question click on the **Add Question** button

	.. image:: ../images/add_question.jpg

	* **Summary**- Summary or the name of the question.

	* **Language** - Programming language on which the question is based.

	* **Type** - Type of the question. i.e Multiple Choice, Multiple Correct Choice, Code and Assignment Upload.

	* **Points** - Points is the marks for a question.

	* **Description** - The actual question description is to be written. 

		.. note::  To add code snippets in questions please use html <code> and <br> tags.

	* **Tags** - Type of label or metadata tag making it easier to find specific type of questions.

	* **Snippet** - Snippet is used to give any default value or default code or command. This will be displayed in the students answer form. This is used only for code questions.

	* **Partial Grading** - Click this checkbox to enable partial grading feature.

	* **File** - File field is used to upload files if there is any file based question.
		For e.g. The question is reading a file say **dummy.txt** and print its content.
		You can then upload a file **dummy.txt** which will be available to the student while attempting the quiz.

		* Some file features:
			1. To delete a file click the delete checkbox and click on Delete Selected Files button.
			2. To extract a file for e.g. say **dummy.zip** click the extract checkbox and click on Save button.
				If **extract** is selected, the file will be extracted while checking
				the student submitted code.
			3. To hide any file from student click the hide checkbox and click on Save button.

		.. Note::  We only support **zip** extension for **extract file** feature.


How to write Test cases
-----------------------
	
	The following explains different methods to write test cases.

	* **Create Standard Test Case**

		Select Standard from Add Test Case field.

		* For Python:
			.. image:: ../images/python_standard_testcase.jpg
			   :width: 80%

			In the test case field write a python assert to check the user code.
			For e.g. :: 
				
				assert add(1, 2) == 3
			
			for program of addition.

		* For C, C++, Java and Bash:
			Sample Moderator code

			For C and C++:
				.. image:: ../images/cpp_standard_testcase.jpg
					:width: 80%

				Consider a Program to add three numbers.
				The code in the Test case field should be as follows: ::

					#include <stdio.h>
					#include <stdlib.h>

					extern int add(int, int, int);

					template <class T>
					void check(T expect,T result)
					{
						if (expect == result)
						{
						printf("\nCorrect:\n Expected %d got %d \n",expect,result);
						}
						else
						{
						printf("\nIncorrect:\n Expected %d got %d \n",expect,result);
						exit (1);
						}
					}

					int main(void)
					{
						int result;
						result = add(0,0,0);
						printf("Input submitted to the function: 0, 0, 0");
						check(0, result);
						result = add(2,3,3);
						printf("Input submitted to the function: 2, 3, 3");
						check(8,result);
						printf("All Correct\n");
					}

				Assuming Students answer to be as below: ::

					int add(int a, int b, int c)
					{
						return a+b+c;
					}

				.. Note::  1. In the above example, **add** in the main function is obtained from student code.
						2. Please make sure that the student code function and testcase calling function should be same which in this case is **add**.

			For Java:
				.. image:: ../images/java_standard_testcase.jpg
					:width: 80%

				Consider a Program to find square of a number.
				The code in the Test case Field should be as follows: ::
					class main
					{
						public static <E> void check(E expect, E result)
						{
							if(result.equals(expect))
							{
								System.out.println("Correct:\nOutput expected "+expect+" and got "+result);
							}
							else
							{
								System.out.println("Incorrect:\nOutput expected "+expect+" but got "+result);
								System.exit(1);
							}
						}
						public static void main(String arg[])
						{
							Test t = new Test();
							int result, input, output;
							input = 0; output = 0;
							result = t.square_num(input);
							System.out.println("Input submitted to the function: "+input);
							check(output, result);
							input = 5; output = 25;
							result = t.square_num(input);
							System.out.println("Input submitted to the function: "+input);
							check(output, result);
							input = 6; output = 36;
							result = t.square_num(input);
							System.out.println("Input submitted to the function: "+input);
							check(output, result);
						}
					}

				Assuming Students answer to be as below: ::

					class Test
					{
						int square_num(int num)
						{
							return num*num;
						}
					}

				.. Note::	1. For Java, class name should always be **main** in testcase.

							2. In the above example, **Test** is the class of student's code.
							3. Please make sure that the student's code class and calling class in testcase is always **Test**. (square_num is the function inside Test class.)

			For Bash:
				.. image:: ../images/bash_standard_testcase.jpg
					:width: 80%

				In **Test case** Field write your bash script.
					For e.g. the question is to move to a particular directory and read a file
					**test.txt**
					The Test case code shown is: ::

						#!/bin/bash
						cd $1
						cat $2

				In **Test case args** Field type your Command line arguments.

					In this case the test case args are: ::

						somedata/  test.txt

					.. Note:: 1. **Test case args** field is used only for bash.
							  2. Each argument should be separated by **space**.
							  3. This field can be left blank.


		Check Delete Field if a test case is to be removed.

		Finally click on Save to save the test case.


	* **Create Standard Input/Output Based Test Case**
            
			Select StdIO from Add Test Case field.

				.. image:: ../images/stdio_testcase.jpg
					:width: 80%

			In Expected input field, enter the value(s) that will be passed to the students' code through a standard I/O stream.

			.. note::  If there are multiple input values in a test case, enter the values in new line.

			In Expected Output Field, enter the expected output for that test case. For e.g type 3 if the output of the user code is 3.

			Setting up Standard Input/Output Based questions is same for all languages.

	* **Create MCQ or MCC Based Test Case**

		Select MCQ/MCC from Add Test Case field.

			Fig (a) showing MCQ based testcase

			.. image:: ../images/mcq_testcase.jpg
				:width: 80%

			Fig (b) showing MCC based testcase

			.. image:: ../images/mcc_testcase.jpg
				:width: 80%

		In Options Field type the option check the correct checkbox if the current option is correct and click on Save button to save each option.

		For MCC based question, check the correct checkbox for multiple correct options.

	* **Create Hook based Test Case**

		Select Hook from Add Test Case field.

		In Hook based test case type, moderator is provided with a evaluator function
		called **check_answer** which is provided with a parameter called **user_answer**.

		**user_answer** is the code of the student in string format.

		A moderator can check the string for specific words in the user answer
		and/or compile and execute the user answer (using standard python libraries) to 
		evaluate and hence return the mark fraction.


		.. image:: ../images/hook_testcase.jpg
				:width: 80%

	* **Create Integer Based Test Case**

			Select **Answer in Integer** from Type field.

			Select Integer from Add Test Case field.

			In the Correct field, add the correct integer value for the question.

			.. image:: ../images/integer_testcase.jpg
				:width: 80%

	* **Create String Based Test Case**

			Select **Answer in String** from Type field.

			Select **String** from Add Test Case field.

			In the **Correct** field, add the exact string answer for the question.

			In **String Check** field, select if the checking of the string answer
			 should be case sensitive or not.

			.. image:: ../images/string_testcase.jpg
				:width: 80%

	* **Create Float Based Test Case**

			Select **Answer in Float** from Type field.

			Select **Float** from Add Test Case field.

			In the **Correct** field, add the correct float value for the question.

			In the **Error Margin** field, add the margin of error that will be allowed.

			.. image:: ../images/float_testcase.jpg
				:width: 80%


Features in Question
--------------------
	
	* **Download Questions**

			Select questions from the list of questions displayed on the Questions page. Click on the Download Selected button to download the questions. This will create a zip file of the Questions selected.

	* **Upload Questions**
			
			Click on the browse button. This will open up a window. Select the zip file of questions and click Ok and then click on Upload file button, questions will be uploaded and displayed on the Questions page.

				Zip file should contain **questions_dump.yaml** from which questions will be loaded.
				Zip file can contain files related to questions.

	* **Test Questions**
			
			Select questions from the list of question displayed on the Questions page. Click on Test selected button. This will take you to a quiz with the selected questions. 

			.. Note:: This will not create an actual quiz but a trial quiz. This quiz is hidden from the students and only for moderator to view. You can delete the quiz from moderator's dashboard.

	* **Filter Questions**
			
			You can filter questions based on type of question, language of question or marks of question.
				1. Click Select Question Type to filter question based on type of the question.
				2. Click Select Language to filter question based on language of the question.
				3. Click Select marks to filter question based on mark of the question.

