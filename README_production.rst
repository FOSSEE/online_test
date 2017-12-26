Production Deployment
=====================

This README provides documentation to help deploy Yaksh in a production
environment. If you wish to take Yaksh on a trial run, here is a
[Quickstart Guide]
(https://github.com/FOSSEE/online\_test/blob/master/README.md)

Pre-Requisite
^^^^^^^^^^^^^

1. Ensure `pip <https://pip.pypa.io/en/latest/installing.html>`__ is
   installed
2. Install dependencies using pip install -r requirements.txt
3. Install MySql Server
4. Install Python MySql support
5. Install Apache Server for deployment

Configure MySql server
^^^^^^^^^^^^^^^^^^^^^^

1. Create a database named ``yaksh`` by following the steps below

   ::

       $> mysql -u root -p    
       $> mysql> create database yaksh

2. Add a user named ``yaksh_user`` and give access to it on the database
   ``yaksh`` by following the steps below

   ::

      mysql> grant usage on yaksh to yaksh_user@localhost identified
      by 'mysecretpassword';

      mysql> grant all privileges on yaksh to yaksh_user@localhost;

3. Add ``DATABASE_PASSWORD = 'mysecretpassword'`` and
   ``DATABASE_USER = 'yaksh_user'`` to online\_test/settings.py

To deploy this app follow the steps below:

1.  Clone this repository and cd to the cloned repo. 

   ::

       $ git clone https://github.com/FOSSEE/online\_test.git

2.  Run:

   ::

       python manage.py makemigrations yaksh

       python manage.py migrate yaksh 

4.  First run the python server provided. This ensures that the code is
    executed in a safe environment. Do this like so:

    ::

        $ sudo python yaksh/code_server.py

    Put this in the background once it has started since this will not
    return back the prompt. It is important that the server be running
    *before* students start attempting the exam. Using sudo is necessary
    since the server is run as the user "nobody". This runs on the ports
    configured in the settings.py file in the variable "SERVER\_PORTS".
    The "SERVER\_TIMEOUT" also can be changed there. This is the maximum
    time allowed to execute the submitted code. Note that this will
    likely spawn multiple processes as "nobody" depending on the number
    of server ports specified.

5.  The ``wsgi.py`` script should make it easy to deploy this using
    mod\_wsgi. You will need to add a line of the form:

    ::

        WSGIScriptAlias / "/online_test/wsgi.py"

    to your apache.conf. For more details see the Django docs here:

    https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/

6.  Go to http://desired\_host\_or\_ip:desired\_port/admin

7.  Login with your credentials and look at the questions and modify if
    needed. Create a new Quiz, set the date and duration or
    activate/deactivate the quiz.

8.  Now ask users to login at:

    ::

        http://host:port/exam

    And you should be all set.

9.  Note that the directory "output" will contain directories, one for
    each user. Users can potentially write output into these that can be
    used for checking later.

10. As Moderator user you can visit http://host/exam/monitor to view
    results and user data interactively. You could also "grade" the
    papers manually if needed.

11. You may dump the results and user data using the results2csv and
    dump\_user\_data commands.

12. The file docs/sample\_questions.py is a template that you can use
    for your own questions.

13. Sometimes you might be in the situation where you are not hosted as
    "host.org/exam/" but as "host.org/foo/exam/" for whatever reason. In
    this case edit "settings.py" and set the "URL\_ROOT" to the root you
    have to serve at. In the above example for "host.org/foo/exam" set
    URL\_ROOT='/foo'.

Installation & Usage
^^^^^^^^^^^^^^^^^^^^

To install this app follow the steps below:

1. Clone this repository and cd to the cloned repo.
   ``$ git clone  https://github.com/FOSSEE/online_test.git``

2. Run:

   ::

       $ python manage.py makemigrations yaksh

       $ python manage.py migrate yaksh

3. Run the python server provided. This ensures that the code is
   executed in a safe environment. Do this like so:

   ::

       $ sudo python -m yaksh.code_server # For Python 2.x


       $ sudo python3 -m yaksh.code_server # For Python 3.x

   Put this in the background once it has started since this will not
   return back the prompt. It is important that the server be running
   *before* students start attempting the exam. Using sudo is necessary
   since the server is run as the user "nobody". This runs the number
   ports configured in the settings.py file in the variable
   "N\_CODE\_SERVERS". The "SERVER\_TIMEOUT" also can be changed there.
   This is the maximum time allowed to execute the submitted code. Note
   that this will likely spawn multiple processes as "nobody" depending
   on the number of server ports specified.

   You can also use a Dockerized code server (see below)

4. Now, Run:

   ::

          python manage.py runserver <desired_ip>:<desired_port>

5. Create a Superuser/Administrator:

   ::

       python manage.py createsuperuser

6. Go to http://desired\_host\_or\_ip:desired\_port/exam

   And you should be all set.

7. Note that the directory "output" will contain directories, one for
   each user. Users can potentially write output into these that can be
   used for checking later.

8. As admin user you can visit http://desired\_host\_or\_ip/exam/monitor to view results
   and user data interactively. You could also "grade" the papers
   manually if needed.

Using Dockerized Code Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install
   `Docker <https://docs.docker.com/engine/installation/>`__

2. Go to the directory where the project is located cd
   /path/to/online\_test

3. Create a docker image. This may take a few minutes docker build -t
   yaksh\_code\_server ./docker/Dockerfile\_codeserver

4. Check if the image has been created using the output of, docker
   images

5. Run the invoke script using the command ``invoke start`` The command
   will create and run a new docker container (that is running the
   code\_server.py within it), it will also bind the ports of the host
   with those of the container

Deploying Multiple Dockers
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install
   `Docker <https://docs.docker.com/engine/installation/>`__

2. Go to the directory where the project is located at:
   
   ::

       cd /path/to/online_test

3. Build the docker images

   ::

       invoke build

4. Run the containers and scripts necessary to deploy the web
   application

   ::

       invoke deploy

5. Use ``invoke deploy --fixtures`` to load the fixtures

6. Create the superuser and moderator group
   ::

       invoke createsuperuser

7. Stop the containers

   ::

       invoke halt

8. Remove the containers

   ::

       invoke clean


Additional commands available
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We provide several convenient commands for you to use:

-  load\_exam : load questions and a quiz from a python file. See
   docs/sample\_questions.py

-  load\_questions\_xml : load questions from XML file, see
   docs/sample\_questions.xml use of this is deprecated in favor of
   load\_exam.

-  results2csv : Dump the quiz results into a CSV file for further
   processing.

-  dump\_user\_data : Dump out relevalt user data for either all users
   or specified users.

For more information on these do this:

::

        $ python manage.py help [command]

where [command] is one of the above.
