=========
Questions
=========

Setting up questions
--------------------

    Setting up questions is the most important part of the Yaksh experience. Questions can be of multiple types i.e Multiple choice questions (MCQ), Multiple correct choices (MCC), Coding questions, assignment upload, fill in the blanks.

    To set up a question click on the questions link in the navigation bar.

    .. image:: ../images/questions.jpg 
    
    To add a question click on the **Add Question** button

    .. image:: ../images/add_question.jpg

    * **Summary**- Summary or the name of the question.

    * **Language** - Programming language on which the question is based.

    * **Type** - Type of the question. i.e Multiple Choice, Multiple Correct Choice, Code, Assignment Upload etc.

    * **Points** - Points is the marks for a question.

    * **Description** - The actual question description.

    * **Tags** - Type of label or metadata tag making it easier to find specific type of questions.

    * **Solution** - Add solution for the question.

    * **Snippet** - Snippet is used to give any default value or default code or command. This will be displayed in the students answer form. This is used only for code questions.

    * **Minimum time(in minutes)** - This value can be set for questions which will be added to a Exercise. Exercise time will depend on this time.

    * **Partial Grading** - Click this checkbox to enable partial grading feature.

    * **Grade Assignment Upload** - Click this checkbox if the assignment upload based question needs evaluation. Evaluation is done with **Hook based TestCase** only.

    * **File** - File field is used to upload files if there is any file based question.
        For e.g. The question is reading a file say **dummy.txt** and print its content.
        You can then upload a file **dummy.txt** which will be available to the student while attempting the quiz.

        * Some file features:
            1. To delete a file click the delete checkbox and click on **Delete Selected Files button**.
            2. To extract a file for e.g. say **dummy.zip** click the extract checkbox and click on Save button.
                If **extract** is selected, the file will be extracted while checking
                the student submitted code.
            3. To hide any file from student click the hide checkbox and click on Save button.

        .. Note::  We only support **zip** extension for **extract file** feature.


How to write Test cases
-----------------------
    After saving the question with the necessary details, you will be able to add
    the test cases. A drop down **Add Test case** will be available to add the test case in the Test Cases section.

    The following explains different methods to write test cases.

    * **Create Standard Test Case**

        Select Standard from Add Test Case field. Sample Testcases are given for all 
        languages.

        * **For Python:**
            .. image:: ../images/python_standard_testcase.jpg
               :width: 80%

            In the test case field write a python assert to check the user code.
            For e.g. :: 

                assert add(1, 2) == 3

            for program of addition.

        * **For C, C++:**

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

        * **For Java:**
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

            .. Note::   1. For Java, class name should always be **main** in testcase.

                        2. In the above example, **Test** is the class of student's code.
                        3. Please make sure that the student's code class and calling class in testcase is always **Test**. (square_num is the function inside Test class.)

        * **For Bash:**
            .. image:: ../images/bash_standard_testcase.jpg
                :width: 80%

            In **Test case** Field write your bash script.
                For e.g. the question is to move to a particular directory and read a file
                **test.txt**
                The Test case code shown is: ::

                    cd $1
                    cat $2

            In **Test case args** Field type your Command line arguments.

                In this case the test case args are: ::

                    somedata/  test.txt

                .. Note:: 1. **Test case args** field is used only for bash.
                          2. Each argument should be separated by **space**.
                          3. This field can be left blank.

        * **For Scilab**
            .. image:: ../images/scilab_standard_testcase.jpg
                :width: 80%

            Consider a Program to add two numbers.
            The code in the Test case Field should be as follows: ::

                mode(-1)
                exec("function.sci",-1);
                i = 0
                p = add(3,5);
                correct = (p == 8);
                if correct then
                 i=i+1
                end
                disp("Input submitted 3 and 5")
                disp("Expected output 8 got " + string(p))
                p = add(22,-20);
                correct = (p==2);
                if correct then
                 i=i+1
                end
                disp("Input submitted 22 and -20")
                disp("Expected output 2 got " + string(p))
                p =add(91,0);
                correct = (p==91);
                if correct then
                 i=i+1
                end
                disp("Input submitted 91 and 0")
                disp("Expected output 91 got " + string(p))
                if i==3 then
                 exit(5);
                else
                 exit(3);
                end

            Assuming Students answer to be as below: ::

                funcprot(0)
                function[c]=add(a,b)
                c=a+b;
                endfunction

        * **For R**
            .. image:: ../images/r_standard_testcase.jpg
                :width: 80%

            Consider a Program to print even or odd number.
            The code in the Test case Field should be as follows: ::

                source("function.r")
                check_empty = function(obj){
                    stopifnot(is.null(obj) == FALSE)
                }
                check = function(input, output){
                stopifnot(input == output)
                }
                is_correct = function(){
                if (count == 3){
                    quit("no", 31)
                }
                }
                check_empty(odd_or_even(3))
                check(odd_or_even(6), "EVEN")
                check(odd_or_even(1), "ODD")
                check(odd_or_even(10), "EVEN")
                check(odd_or_even(777), "ODD")
                check(odd_or_even(778), "EVEN")
                count = 3
                is_correct()

            Assuming Students answer to be as below: ::

                odd_or_even <- function(n){
                  if(n %% 2 == 0){
                    return("EVEN")
                  }
                  return("ODD")
                }


        Check **Delete** Field if a test case is to be removed.

        Finally click on **Save** to save the test case.


    * **Create Standard Input/Output Based Test Case**
            
            Select StdIO from Add Test Case field.

                .. image:: ../images/stdio_testcase.jpg
                    :width: 80%

            In Expected input field, enter the value(s) that will be passed to the students' code through a standard I/O stream.

            .. note::  If there are multiple input values in a test case, enter the values in new line.

            In Expected Output Field, enter the expected output for that test case. For e.g type 3 if the output of the user code is 3.

            Setting up Standard Input/Output Based questions is same for all languages.

            .. note:: Standard Input/Output Based questions is available only for the languages Python, C, C++, Java, Bash.

    * **Create Hook based Test Case**

        Select Hook from Add Test Case field.

        In Hook based test case type, moderator is provided with a evaluator function
        called **check_answer** which is provided with a parameter called **user_answer**.

        **user_answer** is the code of the student in string format.

        .. note :: For assignment upload type question there will be no **user answer** File uploaded by student will be the answer.

        Suppose the student needs to upload a file say **new.txt** as assignment.
        Sample Hook code for this will be as shown below. ::

            def check_answer(user_answer):
                ''' Evaluates user answer to return -
                success - Boolean, indicating if code was executed correctly
                mark_fraction - Float, indicating fraction of the weight to a test case
                error - String, error message if success is false

                In case of assignment upload there will be no user answer '''

                success = False
                err = "Incorrect Answer" # Please make this more specific
                mark_fraction = 0.0

                try:
                    with open('new.txt', 'r') as f:
                        if "Hello, World!" in f.read():
                            success = True
                            err = "Correct Answer"
                            mark_fraction = 1.0
                        else:
                            err = "Did not found string Hello, World! in file."
                except IOError:
                    err = "File new.txt not found."
                return success, err, mark_fraction


        A moderator can check the string for specific words in the user answer
        and/or compile and execute the user answer (using standard python libraries) to 
        evaluate and hence return the mark fraction.


        .. image:: ../images/hook_testcase.jpg
                :width: 80%

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

            Select questions from a list of questions displayed on the
            Questions page. Click on the Download Selected button to download
            the questions. This will create a zip file of the Questions
            selected. The zip will contain yaml file and an folder called
            **additional_files** which will contain files required by questions
            downloaded. Finally one can also download a template yaml file
            and modify it to add his/her questions.

    * **Upload Questions**
            
            Click on the **Upload Questions** tab in the
            **Question Page**.
            One can upload Yaml file with extensions .yaml or .yml.
            Please note that you cannot upload files associated to a question.
            Yaml file can have any name.

            One can also upload zip with the following zip structure -

            .. code::

                .zip
                |-- .yaml or .yml
                |-- .yaml or .yml
                |-- folder1
                |   |-- Files required by questions
                |-- folder2
                |   |-- Files required by questions


    * **Test Questions**
            
            Select questions from the list of question displayed on the Questions page. Click on Test selected button. This will take you to a quiz with the selected questions. 

            .. Note:: This will not create an actual quiz but a trial quiz. This quiz is hidden from the students and only for moderator to view.

    * **Filter Questions**
            
            You can filter questions based on type of question, language of question or marks of question.
                1. Click Select Question Type to filter question based on type of the question.
                2. Click Select Language to filter question based on language of the question.
                3. Click Select marks to filter question based on mark of the question.

    * **Search by tags**

            1. You can search the questions by tags added during question creation.
            2. Click on the Available tags to view all the available tags. Select any tag from available tags and click **Search**.
            3. Enter the tag in the search bar and click on **Search Icon** respective questions will be displayed.

