Production Deployment
======================

This README provides documentation to help deploy Yaksh in a production environment. If you wish to take Yaksh on a trial run, here is a [Quickstart Guide] (https://github.com/FOSSEE/online_test/blob/master/README.md)

#### Pre-Requisite

 1. Ensure [pip](https://pip.pypa.io/en/latest/installing.html) is installed
 1. Install dependencies using
     pip install -r requirements.txt
 1. Install MySql Server
 1. Install Python MySql support
 1. Install Apache Server for deployment
 
#### Configure MySql server

 1. Create a database named ``yaksh`` by following the steps below
    
        $> mysql -u root -p    
        mysql> create database yaksh
 
 1. Add a user named ```yaksh_user``` and give access to it on the database ```yaksh``` by following the steps below
 
    1. mysql> grant usage on yaksh.* to yaksh_user@localhost identified by 'mysecretpassword';
    
    1. mysql> grant all privileges on yaksh.* to yaksh_user@localhost;
 
 1. Add `DATABASE_PASSWORD = 'mysecretpassword'` and `DATABASE_USER = 'yaksh_user'` to online_test/settings.py

To deploy this app follow the steps below:

 1. Clone this repository and cd to the cloned repo.
        $ git clone  https://github.com/FOSSEE/online_test.git

 1. Run:
        python manage.py syncdb
    
 1.  Add questions by editing the "docs/sample_questions.py" or any other file in the same format and then run the following:

        python manage.py load_exam docs/sample_questions.py

     Note that you can supply multiple Python files as arguments and all of
     those will be added to the database.
    
 1. First run the python server provided. This ensures that the code is executed in a safe environment.  Do this like so:
    
        $ sudo python yaksh/code_server.py
      
    Put this in the background once it has started since this will not
    return back the prompt.  It is important that the server be running
    *before* students start attempting the exam.  Using sudo is
    necessary since the server is run as the user "nobody".  This runs
    on the ports configured in the settings.py file in the variable
    "SERVER_PORTS".  The "SERVER_TIMEOUT" also can be changed there.
    This is the maximum time allowed to execute the submitted code.
    Note that this will likely spawn multiple processes as "nobody"
    depending on the number of server ports specified.
    
 1. The ```wsgi.py``` script should make it 
    easy to deploy this using mod_wsgi.  You will need to add a line of the form:

        WSGIScriptAlias / "/online_test/wsgi.py"

    to your apache.conf.  For more details see the Django docs here:

    https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
    
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

 1. As Moderator user you can visit http://host/exam/monitor  to view
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
 
#### Installation & Usage

To install this app follow the steps below:

 1. Clone this repository and cd to the cloned repo.
        ```$ git clone  https://github.com/FOSSEE/online_test.git```
 
 1. Run:
 
        python manage.py syncdb
    
 1.  Add questions by editing the "docs/sample_questions.py" or any other file in the same format and then run the following:

      python manage.py load_exam docs/sample_questions.py

     Note that you can supply multiple Python files as arguments and all of
     those will be added to the database.
    
 1. First run the python server provided. This ensures that the code is executed in a safe environment.  Do this like so:
    
      $ sudo python yaksh/code_server.py
      
    Put this in the background once it has started since this will not
    return back the prompt.  It is important that the server be running
    *before* students start attempting the exam.  Using sudo is
    necessary since the server is run as the user "nobody".  This runs
    on the ports configured in the settings.py file in the variable
    "SERVER_PORTS".  The "SERVER_TIMEOUT" also can be changed there.
    This is the maximum time allowed to execute the submitted code.
    Note that this will likely spawn multiple processes as "nobody"
    depending on the number of server ports specified.

    You can also use a Dockerized code server (see below)
    
 1. Now, Run:

        python manage.py runserver <desired_ip>:<desired_port>
    
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

#### Using Dockerized Code Server

 1. Install [Docker](https://github.com/FOSSEE/online_test/blob/master/README.md)

 1. Got to the directory where the project is located
        cd /path/to/online_test

 1. Create a docker image. This may take a few minutes
        docker build -t yaksh_code_server .

 1. Check if the image has been created using the output of,
        docker images

 1. Run the invoke script using the command ```invoke start```
    The command will create and run a new docker container (that is running the code_server.py within it), it will also bind the ports of the host with those of the container

#### Additional commands available

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

        $ python manage.py help [command]

where [command] is one of the above.
