Production Deployment
=====================

This README provides documentation to help deploy Yaksh in a production
environment. If you wish to take Yaksh on a trial run, here is a
`Quickstart Guide <https://github.com/FOSSEE/online\_test/blob/master/README.rst>`__


Requirements
============

Python 3.6, 3.7, 3.8

Django 3.0.3


###################
Deploying Locally
###################

Follow these steps to deploy locally on the server. For deployment instructions using Docker see `Deploying Multiple Dockers <https://github.com/FOSSEE/online_test/blob/add-docker-compose-test/README_production.rst#deploying-multiple-dockers>`__

Pre-Requisite
^^^^^^^^^^^^^

1. Ensure `pip <https://pip.pypa.io/en/latest/installing.html>`__ is
   installed

2. Install MySQL Server

3. Install Python MySQL system dependencies

4. Install Apache Server for deployment

5. Create a database named ``yaksh`` by following the steps below

   ::

      $> mysql -u root -p
      $> mysql> create database yaksh

6. Add a user named ``yaksh_user`` and give access to it on the database
   ``yaksh`` by following the steps below

   ::

      mysql> grant usage on yaksh to yaksh_user@localhost identified
      by 'mysecretpassword';

      mysql> grant all privileges on yaksh to yaksh_user@localhost;


Installation & Usage
^^^^^^^^^^^^^^^^^^^^

To install this app follow the steps below:

1. Clone this repository and cd to the cloned repo.

   ::

      git clone  https://github.com/FOSSEE/online_test.git

   ::

      cd online_test

2. Install Yaksh dependencies, Run

   ::

      pip3 install -r requirements/requirements-common.txt

   ::

      pip3 install -r requirements/requirements-production.txt

   ::

      sudo pip3 install -r requirements/requirements-codeserver.txt


3. Rename the ``.sampleenv`` to ``.env``

4. In the ``.env`` file, uncomment the following and replace the values
(please keep the remaining settings as is);

   ::

      DB_ENGINE=mysql # Or psycopg (postgresql), sqlite3 (SQLite)
      DB_NAME=yaksh
      DB_USER=root
      DB_PASSWORD=mypassword # Or the password used while creating a Database
      DB_PORT=3306

5. Run:

   ::

        $ python manage.py migrate

6. Run the python server provided. This ensures that the code is
   executed in a safe environment. Do this like so:

   ::

        $ sudo python3 -m yaksh.code_server # For Python 3.x

    Put this in the background once it has started since this will not
    return back the prompt. It is important that the server be running
    *before* students start attempting the exam. Using sudo is necessary
    since the server is run as the user "nobody". Code server requires several
    parameters specified in `.env` file such as "N\_CODE\_SERVERS",
    "SERVER\_TIMEOUT", "SERVER\_POOL\_PORT", "SERVER\_HOST\_NAME"
    set to some default values.

    These parameters can be changed to different values based on your
    requirement. Multiple code server processes are spawned based on
    "N\_CODE\_SERVERS" value.
    The "SERVER\_TIMEOUT" also can be changed. This is the maximum time allowed
    to execute the submitted code.

    You can also use a Dockerized code server,
    see :ref:`Dockerized Code Server <https://github.com/FOSSEE/online_test/blob/add-docker-compose-test/README_production.rst#using-dockerized-code-server>`__


7.  The ``wsgi.py`` script should make it easy to deploy this using
    mod\_wsgi. You will need to add a line of the form:

    ::

        WSGIScriptAlias / "/online_test/wsgi.py"

    to your apache.conf. For more details see the Django docs here:

    https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/

8. Create a Superuser/Administrator:

   ::

        python manage.py createsuperuser

9. Go to http://desired\_host\_or\_ip:desired\_port/exam

   And you should be all set.

10. Note that the "output" directory present in "yaksh_data" folder will
    contain directories, one for each user.
    Users' code files are created in "output" directory that can be used for
    checking later.

11. As admin user, you can visit http://desired\_host\_or\_ip/exam/monitor to
    view results and user data interactively. You could also "grade" the papers
    manually if needed.

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

5. Run the invoke script using the command ``invoke start``. The command
   will create and run a new docker container (that is running the
   code\_server.py within it), it will also bind the ports of the host
   with those of the container

6. You can use ``invoke --list`` to get a list of all the available commands


.. _deploying-multiple-dockers:

######################################
Deploying Multiple Dockers
######################################

Follow these steps to deploy and run the Django Server, MySQL instance and
Code Server in seperate Docker instances.

1. Install `Docker <https://docs.docker.com/engine/installation/>`__

2. Install `Docker Compose <https://docs.docker.com/compose/install/>`__

3. Rename the ``.sampleenv`` to ``.env``

4. In the ``.env`` file, uncomment all the values and keep the default values
   as is.

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

10. To stop the containers, run

   ::

        invoke halt

11. You can use ``invoke restart`` to restart the containers without
    removing them.

12. Remove the containers

   ::

        invoke remove

13. You can use ``invoke --list`` to get a list of all the available commands.
