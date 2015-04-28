Introduction
=============

This project provides an "exam" app that lets users take an online
programming quiz. 

#### Inspiration

At FOSSEE, Nishanth had implemented a nice django based app to
test for multiple-choice questions. I was inspired by a
programming contest that I saw at PyCon APAC 2011.  Chris Boesch, who
administered the contest, used a nice web application 
[Singpath](http://singpath.com) that he had built on top of GAE that 
basically checked your Python code, live. This made it fun and interesting.

I wanted an implementation that was not tied to GAE and decided to write
one myself and the result is the "exam" app.  The idea being that I can
use this to test students programming skills and not have to worry about
grading their answers myself and I can do so on my machines.

#### Features

 * Define fairly complicated programming problems and have users
 solve the problem. 
 * Immediate verification of code solution. 
 * Supports pretty much arbitrary coding questions in Python, C, C++ and 
 simple Bash and uses "test cases" to test the implementations of the students.
 * Supports simple multiple choice questions and File uploads.
 * Since it runs on your Python, you could technically test any Python based library.
 * Scales to over 500+ simultaneous users.
 * Distributed under the BSD license.

Quick Start for Users
======================

#### Pre-Requisite

1. [Install pip](https://pip.pypa.io/en/latest/installing.html) 

1. Install Virtual Environment using
    ```pip install virtualenv```

#### Installation

1. Run the install_script.py using
    ```python install_script.py```

    The script does the following;
    1. Creates a new virtual environment called online_test
    1. Installs Django 1.6 within that virtual environment
    1. Pulls from the online_test repository on [Github](https://github.com/FOSSEE/online_test)
    1. Creates a two users test moderator and a test examinee
    1. Loads demo questions
    1. Loads demo quiz

1. In your terminal run ```launch demo```

1. Open your browser and run http://localhost:8000/exam

1. Login with as a test_moderator to edit the quiz or as a test examinee to take the quiz

Production Deployment
======================

#### Pre-Requisite

 1. Install MySql Server
 
 1. Install Python MySql support
 
 1. Install Apache Server for deployment
 
#### Configure MySql server

 1. Create a database named ``online_test`` by following the steps below
    
    1. $> mysql -u root -p
    
    1. mysql> create database online_test
 
 1. Add a user named ```online_test_user``` and give access to it on the database ```online_test``` by following the steps below
 
    1. mysql> grant usage on online_test.* to online_test_user@localhost identified by 'mysecretpassword';
    
    1. mysql> grant all privileges on online_test.* to online_test_user@localhost;
 
 1. Create a file named `local.py` in folder `testapp` and insert `DATABASE_PASSWORD = 'mysecretpassword'`

To deploy this app follow the steps below:

 1. Clone this repository and cd to the cloned repo.
 
 1. Run:
 
        django syncdb
 
    1. Run:
    
            django migrate exam
    
 1.  Add questions by editing the "docs/sample_questions.py" or any other file in the same format and then run the following:

        django load_exam docs/sample_questions.py

	 Note that you can supply multiple Python files as arguments and all of
	 those will be added to the database.
    
 1. First run the python server provided. This ensures that the code is executed in a safe environment.  Do this like so:
    
        $ sudo python testapp/code_server.py
      
    Put this in the background once it has started since this will not
    return back the prompt.  It is important that the server be running
    *before* students start attempting the exam.  Using sudo is
    necessary since the server is run as the user "nobody".  This runs
    on the ports configured in the settings.py file in the variable
    "SERVER_PORTS".  The "SERVER_TIMEOUT" also can be changed there.
    This is the maximum time allowed to execute the submitted code.
    Note that this will likely spawn multiple processes as "nobody"
    depending on the number of server ports specified.
    
 1. The ```bin/django.wsgi``` script should make it 
 	easy to deploy this using mod_wsgi.  You will need to add a line of the form:

        WSGIScriptAlias / "/var/www/online_test/bin/django.wsgi"

	to your apache.conf.  For more details see the Django docs here:

	https://docs.djangoproject.com/en/1.3/howto/deployment/modwsgi/
	
 1. Go to http://desired_host_or_ip:desired_port/admin

 1. Login with your credentials and look at the questions and modify if
    needed.  Create a new Quiz, set the date and duration or
    activate/deactivate the quiz.

 1. Now ask users to login at:

        http://host:port/exam

    And you should be all set.
    
 1. Note that the directory "output" will contain directories, one for each
    user.  Users can potentially write output into these that can be used
    for checking later.

 1. As admin user you can visit http://host/exam/monitor  to view
     results and user data interactively. You could also "grade" the
     papers manually if needed.

 1. You may dump the results and user data using the results2csv and
     dump_user_data commands.
     
 1. The file docs/sample_questions.py is a template that you can use for your own questions.
     
 1. Sometimes you might be in the situation where you are not hosted as
    "host.org/exam/"  but as "host.org/foo/exam/" for whatever reason.  In
    this case edit "settings.py" and set the "URL_ROOT"  to the root you
    have to serve at.  In the above example for "host.org/foo/exam" set
    URL_ROOT='/foo'.
 
Development Settings
====================

To install this app follow the steps below:

 1. Clone this repository and cd to the cloned repo.
 
 1. Run:
 
        django syncdb
 
    Run:
    
        django migrate exam
    
 1.  Add questions by editing the "docs/sample_questions.py" or any other file in the same format and then run the following:

      django load_exam docs/sample_questions.py

     Note that you can supply multiple Python files as arguments and all of
     those will be added to the database.
    
 1. First run the python server provided. This ensures that the code is executed in a safe environment.  Do this like so:
    
      $ sudo python testapp/code_server.py
      
    Put this in the background once it has started since this will not
    return back the prompt.  It is important that the server be running
    *before* students start attempting the exam.  Using sudo is
    necessary since the server is run as the user "nobody".  This runs
    on the ports configured in the settings.py file in the variable
    "SERVER_PORTS".  The "SERVER_TIMEOUT" also can be changed there.
    This is the maximum time allowed to execute the submitted code.
    Note that this will likely spawn multiple processes as "nobody"
    depending on the number of server ports specified.
    
 1. Now, Run:

        $ django runserver <desired_ip>:<desired_port>
	
 1. Go to http://deserved_host_or_ip:desired_port/admin

 1. Login with your credentials and look at the questions and modify if
    needed.  Create a new Quiz, set the date and duration or
    activate/deactivate the quiz.

 1. Now ask users to login at:

        http://host:port/exam

    And you should be all set.
    
 1. Note that the directory "output" will contain directories, one for each
    user.  Users can potentially write output into these that can be used
    for checking later.

 1. As admin user you can visit http://host/exam/monitor  to view
     results and user data interactively. You could also "grade" the
     papers manually if needed.

 1. You may dump the results and user data using the results2csv and
     dump_user_data commands.
     
 1. The file docs/sample_questions.py is a template that you can use for your own questions.
     
 1. Sometimes you might be in the situation where you are not hosted as
    "host.org/exam/"  but as "host.org/foo/exam/" for whatever reason.  In
    this case edit "settings.py" and set the "URL_ROOT"  to the root you
    have to serve at.  In the above example for "host.org/foo/exam" set
    URL_ROOT='/foo'.

Additional commands available
==============================

We provide several convenient commands for you to use:

 - load_exam : load questions and a quiz from a python file.  See
   docs/sample_questions.py

 - load_questions_xml : load questions from XML file, see
   docs/sample_questions.xml  use of this is deprecated in favor of
   load_exam.

 - results2csv : Dump the quiz results into a CSV file for further
   processing.

 - dump_user_data : Dump out relevalt user data for either all users or
   specified users.

For more information on these do this:

        $ ./manage.py help [command]

where [command] is one of the above.

Contact
=======

For further information and support you can contact

* Forum Link
* Email Address

License
=======

This is distributed under the terms of the BSD license.  Copyright
information is at the bottom of this file.

Authors
=======

Main author: Prabhu Ramachandran

I gratefully acknowledge help from the following:

 - Nishanth Amuluru originally from FOSSEE who wrote bulk of the
   login/registration code.  He wrote an initial first cut of a quiz app
   which supported only simple questions which provided motivation for
   this app.  The current codebase does not share too much from his
   implementation although there are plenty of similarities.

 - Harish Badrinath (FOSSEE) -- who provided a first cut of the bash
   related scripts.

 - Srikant Patnaik and Thomas Stephen Lee, who helped deploy and test
   the code.


Copyright (c) 2011 Prabhu Ramachandran and FOSSEE (fossee.in)
