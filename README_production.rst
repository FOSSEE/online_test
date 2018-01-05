Production Deployment
=====================

This README provides documentation to help deploy Yaksh in a production
environment. If you wish to take Yaksh on a trial run, here is a
`Quickstart Guide <https://github.com/FOSSEE/online\_test/blob/master/README.rst>`__

###################
Deploying Locally
###################

Follow these steps to deploy locally on the server. For deployment instructions using Docker see `Deploying Multiple Dockers <https://github.com/FOSSEE/online_test/blob/add-docker-compose-test/README_production.rst#deploying-multiple-dockers>`__

Pre-Requisite
^^^^^^^^^^^^^

1. Ensure `pip <https://pip.pypa.io/en/latest/installing.html>`__ is
   installed
2. Install dependencies, Run;
   
   ::

       pip install -r requirements/requirements-py2.txt # For Python 2

       pip3 install -r requirements/requirements-py3.txt # For Python 3

3. Install MySql Server
4. Install Python MySql support
5. Install Apache Server for deployment

6. Create a database named ``yaksh`` by following the steps below

   ::

       $> mysql -u root -p    
       $> mysql> create database yaksh

7. Add a user named ``yaksh_user`` and give access to it on the database
   ``yaksh`` by following the steps below

   ::

      mysql> grant usage on yaksh to yaksh_user@localhost identified
      by 'mysecretpassword';

      mysql> grant all privileges on yaksh to yaksh_user@localhost;

8. Add ``DATABASE_PASSWORD = 'mysecretpassword'`` and
   ``DATABASE_USER = 'yaksh_user'`` to online\_test/settings.py


Installation & Usage
^^^^^^^^^^^^^^^^^^^^

To install this app follow the steps below:

1. Clone this repository and cd to the cloned repo.

   ::

       $ git clone  https://github.com/FOSSEE/online_test.git

2. Rename the ``.sampleenv`` to ``.env``

3. In the ``.env`` file, uncomment the following and replace the values (please keep the remaining settings as is);

   ::

       DB_ENGINE=mysql # Or psycopg (postgresql), sqlite3 (SQLite)
       DB_NAME=yaksh
       DB_USER=root
       DB_PASSWORD=mypassword # Or the password used while creating a Database
       DB_PORT=3306

4. Run:

   ::

       $ python manage.py makemigrations yaksh

       $ python manage.py migrate yaksh

5. Run the python server provided. This ensures that the code is
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

   You can also use a Dockerized code server, see `Dockerized Code Server <https://github.com/FOSSEE/online_test/blob/add-docker-compose-test/README_production.rst#using-dockerized-code-server>`__


6.  The ``wsgi.py`` script should make it easy to deploy this using
    mod\_wsgi. You will need to add a line of the form:

    ::

        WSGIScriptAlias / "/online_test/wsgi.py"

    to your apache.conf. For more details see the Django docs here:

    https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/

7. Create a Superuser/Administrator:

   ::

       python manage.py createsuperuser

8. Go to http://desired\_host\_or\_ip:desired\_port/exam

   And you should be all set.

9. Note that the directory "output" will contain directories, one for
   each user. Users can potentially write output into these that can be
   used for checking later.

10. As admin user you can visit http://desired\_host\_or\_ip/exam/monitor to view results and user data interactively. You could also "grade" the papers manually if needed.

.. _dockerized-code-server:

Using Dockerized Code Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install
   `Docker <https://docs.docker.com/engine/installation/>`__

2. Go to the directory where the project is located 

   ::

       cd /path/to/online_test

3. Create a docker image. This may take a few minutes,

   ::

       docker build -t yaksh_code_server -f ./docker/Dockerfile_codeserver

4. Check if the image has been created using the output of ``docker
   images``

5. Run the invoke script using the command ``invoke start`` The command
   will create and run a new docker container (that is running the
   code\_server.py within it), it will also bind the ports of the host
   with those of the container

6. You can use ``invoke --list`` to get a list of all the available commands


.. _deploying-multiple-dockers:

######################################
Deploying Multiple Dockers
######################################

Follow these steps to deploy and run the Django Server, MySQL instance and Code Server in seperate Docker instances.

1. Install `Docker <https://docs.docker.com/engine/installation/>`__

2. Install `Docker Compose <https://docs.docker.com/compose/install/>`__

3. Rename the ``.sampleenv`` to ``.env``

4. In the ``.env`` file, uncomment all the values and keep the default values as is.

5. Go to the ``docker`` directory where the project is located:
   
   ::

       cd /path/to/online_test/docker

6. Build the docker images

   ::

       invoke build

7. Run the containers and scripts necessary to deploy the web
   application

   ::

       invoke begin

8. Make sure that all the containers are ``Up`` and stable

   ::

       invoke status

8. Run the containers and scripts necessary to deploy the web
   application, ``--fixtures`` allows you to load fixtures.

   ::

       invoke deploy --fixtures

10. Stop the containers, you can use ``invoke restart`` to restart the containers without removing them

   ::

       invoke halt

11. Remove the containers

   ::

       invoke remove

12. You can use ``invoke --list`` to get a list of all the available commands


.. _add-commands:

######################################
Additional commands available
######################################

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
