Yaksh
=====

|Build Status| |Documentation Status| |Version Status| |Coverage Status|

To get an overview of the Yaksh interface please refer to the user documentation at `Yaksh Docs <http://yaksh.readthedocs.io>`_


This is a Quickstart guide to help users setup a trial instance. If you wish to deploy Yaksh in a production environment here is a `Production Deployment Guide <https://github.com/FOSSEE/online\_test/blob/master/README\_production.rst>`_

Introduction
============

This project provides an "exam" app that lets users take an online
programming quiz.

Features
========

-  Define fairly complicated programming problems and have users solve
   the problem.
-  Immediate verification of code solution.
-  Supports pretty much arbitrary coding questions in Python, C, C++, Java, R, Scilab and
   Bash.
-  Supports Multiple choice, Fill in the blanks, Arrange options and File upload based questions.
-  Since it runs on Python, you could technically test any Python
   based library.
-  Create course with lessons and quiz for online learning.
-  Almost real-time monitoring for quiz.
-  Supports automatic and manual grading, regrading of quiz.
-  Add grading system to the course.
-  Scales to over 500+ simultaneous users.
-  Distributed under the BSD license.

To get a glimpse of all the available features check our demo website https://yaksh-demo.fossee.in. It has 50 teacher and student login.

**Sample teacher login**

Username:- teacher1
Password:- teacher1

**Sample student login**

Username:- student1
Password:- student1

Requirements
============

Python 3.6, 3.7, 3.8

Django 3.0.3

Celery 4.4.2

Installation
============

**Note**: Currently, only Linux and MacOS is supported for the project.

If Python 3.6 and above is not available in the system, then we recommend using
miniconda. Download miniconda with Python 3.6 and above.

**Installing Miniconda**

1. Download miniconda from https://docs.conda.io/en/latest/miniconda.html according to the OS version.

2. Follow the installation instructions as given in https://conda.io/projects/conda/en/latest/user-guide/install/index.html#regular-installation

3. Restart the Terminal.

**Pre-Requisite**

* **Install redis server**

  Redis is required for celery. Celery runs a background task to re-evaluate the submissions.

  ::

      sudo apt install redis-server (Debian/Ubuntu)

      yum install redis (Centos)

* **Start redis server**

  ::
     
      systemctl start redis

* **Check redis server status**

  ::

      systemctl status redis

* **Run celery worker**
  
  ::

      celery -A online_test worker -B

* Ensure  `pip <https://pip.pypa.io/en/latest/installing.html>`_ is installed

**Installing Yaksh**

* **Clone the repository**

  ::

      git clone https://github.com/FOSSEE/online_test.git

* **Go to the online_test directory**

  ::

      cd online_test

* **Install the dependencies**:

  * Install Django and dependencies

    ::

        pip3 install -r requirements/requirements-common.txt

  * Install Code Server dependencies

    ::

        sudo pip3 install -r requirements/requirements-codeserver.txt


Quick Start
^^^^^^^^^^^

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
