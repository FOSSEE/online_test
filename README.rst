Introduction
============

This app provides an "exam" app that lets users take an online
programming quiz.  Currently only Python and simple Bash scripts can be
tested.  At FOSSEE, Nishanth had implemented a nice django based app to
test for multiple-choice questions.  However, I was inspired by a
programming contest that I saw at PyCon APAC 2011.  Chris Boesch, who
administered the contest, used a nice web application that he had built
on top of GAE that basically checked your Python code, live.  This made
it fun and interesting.  Their application can be seen at
http://singpath.com

I wanted an implementation that was not tied to GAE and decided to write
one myself and the result is the "exam" app.  The idea being that I can
use this to test students programming skills and not have to worry about
grading their answers myself and I can do so on my machines.

You can define fairly complicated programming problems and have users
solve the problem and the solution is checked immediately. The system
supports pretty much arbitrary Python and uses "test cases" to test the
implementations of the students.  It also supports simple bash scripts
-- see the sample questions in "docs/".  In addition it supports simple
multiple choice questions.  Since it runs on your Python, you could
technically test any Python based library.  It is distributed under the
BSD license.

It can use a lot more work but the basics work and the app scales to
over 500+ simultaneous users. :)

Pre-Requisite
=============

 #. Install MySql Server
 
 #. Install Python MySql support
 
 #. Install Apache Server for deployment
 
Configure MySql server
----------------------

 #. Create a database named ``online_test``
 
 #. Add a user named ``online_test_user`` and give access to it on the database ``online_test``
 
 #. Create a file named `local.py` in folder `testapp` and insert `DATABASE_PASSWORD = 'yourpassword'`
  

Production Deployment
=====================

To deploy this app follow the steps below:

 #. Clone this repository and cd to the cloned repo.
 
 #. run:: 
 
 python bootstrap.py
 
 #. run::
 
  ./bin/buildout -c production.cfg
 
 #. run::
 
  ./bin/django syncdb
   
   [ enter password etc.]
 
    run::
    
     ./bin/django migrate exam
    
 #.  Add questions by editing the "docs/sample_questions.py" or any other file in the same format and then run the following::

      ./bin/django load_exam docs/sample_questions.py

    Note that you can supply multiple Python files as arguments and all of
    those will be added to the database.
    
 #. First run the python server provided. This ensures that the code is executed in a safe environment.  Do this like so::
    
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
    
 #. The ``bin/django.wsgi`` script should make it 
 	easy to deploy this using mod_wsgi.  You will need to add a line of the form:

        WSGIScriptAlias / "/var/www/online_test/bin/django.wsgi"

	to your apache.conf.  For more details see the Django docs here:

	https://docs.djangoproject.com/en/1.3/howto/deployment/modwsgi/
	
 #. Go to http://deserved_host_or_ip:desired_port/admin

 #. Login with your credentials and look at the questions and modify if
    needed.  Create a new Quiz, set the date and duration or
    activate/deactivate the quiz.

 #. Now ask users to login at:

        http://host:port/exam

    And you should be all set.
    
 #. Note that the directory "output" will contain directories, one for each
    user.  Users can potentially write output into these that can be used
    for checking later.

 #. As admin user you can visit http://host/exam/monitor  to view
     results and user data interactively. You could also "grade" the
     papers manually if needed.

 #. You may dump the results and user data using the results2csv and
     dump_user_data commands.
 
Development Settings
====================

To install this app follow the steps below:

  #. Clone this repository and cd to the cloned repo.
 
 #. run:: 
 
 python bootstrap.py
 
 #. run::
 
  ./bin/buildout -c production.cfg
 
 #. run::
 
  ./bin/django syncdb
   
   [ enter password etc.]
 
    run::
    
     ./bin/django migrate exam
    
 #.  Add questions by editing the "docs/sample_questions.py" or any other file in the same format and then run the following::

      ./bin/django load_exam docs/sample_questions.py

    Note that you can supply multiple Python files as arguments and all of
    those will be added to the database.
    
 #. First run the python server provided. This ensures that the code is executed in a safe environment.  Do this like so::
    
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
    
 #. Now, run::

	$ ./bin/django runserver <desired_ip>:<desired_port>
	
 #. Go to http://deserved_host_or_ip:desired_port/admin

 #. Login with your credentials and look at the questions and modify if
    needed.  Create a new Quiz, set the date and duration or
    activate/deactivate the quiz.

 #. Now ask users to login at:

        http://host:port/exam

    And you should be all set.
    
 #. Note that the directory "output" will contain directories, one for each
    user.  Users can potentially write output into these that can be used
    for checking later.

 #. As admin user you can visit http://host/exam/monitor  to view
     results and user data interactively. You could also "grade" the
     papers manually if needed.

 #. You may dump the results and user data using the results2csv and
     dump_user_data commands.
     
     
     The file docs/sample_questions.py is a template that you can use for your
own questions.

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

For more information on these do this::

  $ ./manage.py help [command]

where [command] is one of the above.

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