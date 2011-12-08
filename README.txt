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

Dependencies
=============

Before you install/deploy, make sure you have the following installed:

 - Django 1.3 or above.
 - South (tested with 0.7.3).

That and a running Python is pretty much all you need.  Of course, for
serious deployment you are going to need Apache or some other decent
webserver.


Installation and Deployment
=============================

To install/deploy this app follow the steps below:

 1. Clone this repository and cd to the cloned repo.

 2. Run::

      $ python manage.py syncdb
      [ enter password etc.]

      $ python manage.py migrate exam

 3. Add questions by editing the "docs/sample_questions.py" or any other
    file in the same format and then run the following::

      $ python manage.py load_exam docs/sample_questions.py

    Note that you can supply multiple Python files as arguments and all of
    those will be added to the database.
    
 4. First run the python server provided.  This ensures that the code is 
    executed in a safe environment.  Do this like so::
    
      $ sudo python code_server.py
      
    Put this in the background once it has started since this will not
    return back the prompt.  It is important that the server be running
    *before* students start attempting the exam.  Using sudo is
    necessary since the server is run as the user "nobody".  This runs
    on the ports configured in the settings.py file in the variable
    "SERVER_PORTS".  The "SERVER_TIMEOUT" also can be changed there.
    This is the maximum time allowed to execute the submitted code.
    Note that this will likely spawn multiple processes as "nobody"
    depending on the number of server ports specified.

 5. Now, run::
 
    $ python manage.py runserver <desired_ip>:<desired_port>
    
    For deployment use Apache or a real webserver, see below for more 
    information.

 6. Go to http://deserved_host_or_ip:desired_port/admin

 7. Login with your credentials and look at the questions and modify if
    needed.  Create a new Quiz, set the date and duration or
    activate/deactivate the quiz.

 8. Now ask users to login at:

        http://host:port/exam

    And you should be all set.
    
 9. Note that the directory "output" will contain directories, one for each
    user.  Users can potentially write output into these that can be used
    for checking later.

 10. As admin user you can visit http://host/exam/monitor  to view
     results and user data interactively. You could also "grade" the
     papers manually if needed.

 11. You may dump the results and user data using the results2csv and
     dump_user_data commands.

WARNING:  django is running in debug mode for this currently, CHANGE it
during deployment.  To do this, edit settings.py and set DEBUG to False.
Also look at other settings and change them suitably.

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

Deploying via Apache
=====================

For any serious deployment, you will need to deploy the app using a real
webserver like Apache.  The ``apache/django.wsgi`` script should make it
easy to deploy this using mod_wsgi.  You will need to add a line of the
form:

        WSGIScriptAlias / "/var/www/online_test/apache/django.wsgi"

to your apache.conf.  For more details see the Django docs here:

https://docs.djangoproject.com/en/1.3/howto/deployment/modwsgi/


Sometimes you might be in the situation where you are not hosted as
"host.org/exam/"  but as "host.org/foo/exam/" for whatever reason.  In
this case edit "settings.py" and set the "URL_ROOT"  to the root you
have to serve at.  In the above example for "host.org/foo/exam" set
URL_ROOT='/foo'.

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

