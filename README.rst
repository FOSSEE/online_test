Yaksh
=====

|Build Status| |Documentation Status| |Version Status| |Coverage Status|

To get an overview of the Yaksh interface please refer to the user documentation at `Yaksh Docs <http://yaksh.readthedocs.io>`_


This is a Quickstart guide to help users setup a trial instance. If you wish to deploy Yaksh in a production environment here is a `Production Deployment Guide <https://github.com/FOSSEE/online_test/blob/master/README_production.rst>`_

Introduction
^^^^^^^^^^^^

This project provides an "exam" app that lets users take an online
programming quiz.

Features
^^^^^^^^

-  Define fairly complicated programming problems and have users solve
   the problem.
-  Immediate verification of code solution.
-  Supports pretty much arbitrary coding questions in Python, C, C++ and
   simple Bash and uses "test cases" to test the implementations of the
   students.
-  Supports simple multiple choice questions and File uploads.
-  Since it runs on your Python, you could technically test any Python
   based library.
-  Scales to over 500+ simultaneous users.
-  Distributed under the BSD license.

Quick Start
===========

Pre-Requisites
^^^^^^^^^^^^^^

1. Ensure you have Python available.
2. Ensure `pip <https://pip.pypa.io/en/latest/installing.html>`__ is
   installed.

You can install Yaksh as a project or an app.
------------------------------------------------

1. Yaksh Installation as a Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install yaksh

   -  Clone the repository

      ::

          $ git clone https://github.com/FOSSEE/online_test.git

   -  Go to the online\_test directory

      ::

          $ cd ./online_test

   -  Install the dependencies for local setup

        ::

            $ pip install -r ./requirements/requirements-common.txt

Short instructions
^^^^^^^^^^^^^^^^^^

1. Start up the code server that executes the user code safely:

   -  To run the code server in a sandboxed docker environment, run the
      command:

      ::

          $ invoke start

   -  Make sure that you have Docker installed on your system
      beforehand. `Docker
      Installation <https://docs.docker.com/engine/installation/#desktop>`__

   -  To run the code server without docker, locally use:

      ::

          $ invoke start --unsafe

   -  Note this command will run the yaksh code server locally on your
      machine and is susceptible to malicious code. You will have to
      install the code server requirements in sudo mode.

2. On another terminal, run the application using the following command:

   ::

       $ invoke serve

   -  *Note:* The serve command will run the django application server
      on the 8000 port and hence this port will be unavailable to other
      processes.

3. Open your browser and open the URL ``http://localhost:8000/exam``

4. Login as a teacher to edit the quiz or as a student to take the quiz
   Credentials:

   -  Student - Username: student \| Password: student
   -  Teacher - Username: teacher \| Password: teacher

5. User can also login to the Default Django admin using;

   -  Admin - Username: admin \| Password: admin

2. Yaksh Installation as a django-app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. pip install git+https://github.com/FOSSEE/online_test

2. Add following apps to the INSTALLED_APPS in the project settings:
    - yaksh
    - taggit
    - grades
    - social.apps.django_app.default

3. On terminal, run the migrate command:

   ::

       $ python manage.py migrate

4. Add following in the project urls.py

   ::

        from django.conf.urls import url, include

        urlpatterns += [
            url(r'^exam/', include('yaksh.urls', namespace='yaksh', app_name='yaksh')),
            url(r'^exam/reset/', include('yaksh.urls_password_reset')),
            url(r'^', include('social.apps.django_app.urls', namespace='social')),
            url(r'^grades/', include('grades.urls', namespace='grades', app_name='grades')),
        ]

Note, here there should be static url for Media files,
this is necessary for file upload/download to work. Following is for reference:

   ::

        In project settings file

        MEDIA_URL = '/data/'
        MEDIA_ROOT = BASE_DIR

        In project root url

        from django.conf.urls.static import static
        from django.conf import settings

        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

5. You can create a moderator using the following command:

   ::

        $ python manage.py create_moderator <username>

6. You need to run the following command, for yaksh to do evaluation:

   ::

        $ sudo python -m yaksh.code_server

Note, if you are using a python virtualenv then run the above command as following:

    ::

        $ sudo <path-to-your-created-virtualenv>/bin/python -m yaksh.code_server

7. Visit ``http://localhost:8000/exam``

Note, for login redirect to work while accessing valid url by Anonymous user,
LOGIN_URL must be set in the project settings. Following is for reference:

    ::

        LOGIN_URL = '/exam/login/'

History
=======

At FOSSEE, Nishanth had implemented a nice django based app to test for
multiple-choice questions. Prabhu Ramachandran was inspired by a
programming contest that he saw at PyCon APAC 2011. Chris Boesch, who
administered the contest, used a nice web application
`Singpath <http://singpath.com>`__ that he had built on top of GAE that
basically checked your Python code, live. This made it fun and
interesting.

Prabhu wanted an implementation that was not tied to GAE and hence wrote
the initial cut of what is now 'Yaksh'. The idea being that anyone can
use this to test students programming skills and not have to worry about
grading their answers manually and instead do so on their machines.

The application has since been refactored and maintained by FOSSEE
Developers.

Contact
=======

For further information and support you can contact

Python Team at FOSSEE: pythonsupport@fossee.in

License
=======

This is distributed under the terms of the BSD license. Copyright
information is at the bottom of this file.

Authors
=======

`FOSSEE Developers <https://github.com/FOSSEE/online_test/graphs/contributors>`_

Copyright (c) 2011-2017 `FOSSEE <https://fossee.in>`_


.. |Build Status| image:: https://travis-ci.org/FOSSEE/online_test.svg?branch=master
   :target: https://travis-ci.org/FOSSEE/online_test
.. |Documentation Status| image:: https://readthedocs.org/projects/yaksh/badge/?version=latest
   :target: http://yaksh.readthedocs.io/en/latest/?badge=latest
.. |Version Status| image:: https://badge.fury.io/gh/fossee%2Fonline_test.svg
    :target: https://badge.fury.io/gh/fossee%2Fonline_test
.. |Coverage Status| image:: https://codecov.io/gh/fossee/online_test/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/fossee/online_test

