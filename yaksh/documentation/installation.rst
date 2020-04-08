============
Installation
============

Requirements
------------

Python 3.6, 3.7, 3.8

Django 3.0.3

Installing Yaksh
----------------

If Python 3.6 and above is not available in the system, then we recommend using
miniconda

**Installing Miniconda**

1. Download miniconda from https://docs.conda.io/en/latest/miniconda.html according to the OS version.

2. Follow the installation instructions as given in https://conda.io/projects/conda/en/latest/user-guide/install/index.html#regular-installation

3. Restart the Terminal.

**Pre-Requisite**

* Ensure  `pip <https://pip.pypa.io/en/latest/installing.html>`_ is installed

**Installing Yaksh**

    1. **Clone the repository**::

            git clone https://github.com/FOSSEE/online_test.git

    2. **Go to the online_test directory**::

            cd ./online_test

    3. **Install the dependencies**:

        * Install Django and dependencies::

            pip install -r ./requirements/requirements-common.txt

        * Install Code Server dependencies::

            sudo pip3 install -r requirements/requirements-codeserver.txt

Quick Start
-----------

1. **Start up the code server that executes the user code safely**:
    * To run the code server in a sandboxed docker environment, run the command::

        $ invoke start

    .. note::

        Make sure that you have Docker installed on your system beforehand.
        Find docker installation guide `here <https://docs.docker.com/engine/installation/#desktop>`_.

    * To run the code server without docker, locally use::

        $ invoke start --unsafe

    .. note::

        Note this command will run the yaksh code server locally on your machine and is susceptible to malicious code. You will have to install the code server requirements in sudo mode.

2. **On another terminal, run the application using the following command**
    * To start the django server::

        $ invoke serve

    .. note::

        The serve command will run the django application server on the 8000 port and hence this port will be unavailable to other processes.

3. **Open your browser and open the URL** - ``http://localhost:8000/exam``

4. **Login as a teacher to edit the quiz or as a student to take the quiz**
    
    * Credentials:
        For Student:
            * Username: student
            * Password: student
        For Teacher:
            * Username: teacher
            * Password: teacher

5. **User can also login to the Default Django admin by going to URL and entering the following admin credentials** ``http://localhost:8000/admin``
    For admin:
        * Username: admin
        * Password: admin


Production Deployment
---------------------

* **Deploying Locally**

    Follow these steps to deploy locally on the server.

    * **Pre-Requisite**

        1. Ensure `pip <https://pip.pypa.io/en/latest/installing.html>`__ is
           installed
        2. Install dependencies, Run;
           
           ::

               pip3 install -r requirements/requirements-py3.txt # For Python 3.x

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


    * **Installation & Usage**

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

           You can also use a Dockerized code server, see `Dockerized Code Server`


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

        10. As a moderator you can visit http://desired\_host\_or\_ip/exam/monitor to view results and user data interactively. You could also "grade" the papers manually if needed.

.. _dockerized-code-server:

* **Using Dockerized Code Server**

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


* **Deploying Multiple Dockers**

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

* **Additional commands available**

    * **create_moderator** : Use this command to make a user as moderator.

      ::

        python manage.py create_moderator <username>

    For more information on the command:

    ::

      python manage.py help [command-name]
