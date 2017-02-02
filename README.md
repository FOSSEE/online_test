Yaksh
========

[![Build Status](https://travis-ci.org/FOSSEE/online_test.svg?branch=master)](https://travis-ci.org/FOSSEE/online_test)
[![Documentation Status](https://readthedocs.org/projects/yaksh/badge/?version=latest)](http://yaksh.readthedocs.io/en/latest/?badge=latest)

To get an overview of the Yaksh interface please refer to the user documentation at [Yaksh Docs] (http://yaksh.readthedocs.io)

This is a Quickstart guide to help users setup a trial instance. If you wish to deploy Yaksh in a production environment here is a [Production Deployment Guide] (https://github.com/FOSSEE/online_test/blob/master/README_production.md)


#### Introduction

This project provides an "exam" app that lets users take an online
programming quiz.

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

Quick Start
===========

#### Pre-Requisites

1. Ensure you have Python available.
1. Ensure [pip](https://pip.pypa.io/en/latest/installing.html) is installed.

#### Installation

1. Install yaksh
    - For latest stable release

            $ pip install yaksh

    - For the development version

            $ pip install git+https://github.com/FOSSEE/online_test.git

#### Short instructions

To see a quick demo after installing yaksh do the following:

    $ yaksh create_demo yaksh_demo
    $ yaksh run yaksh_demo

On another terminal start up the code server that executes the user code safely:

    $ sudo yaksh run_code_server

Now point your browser to ```http://localhost:8000/exam```.

#### More detailed instructions

1. On the terminal run:

        $ yaksh create_demo [project_path]

    - `project_path` is the desired directory of the django project the
      basename of which is also the Django project name. This can be a
      relative directory.

    - In case a `project_path` is not specified, the project is created
      in a `yaksh_demo` subdirectory of the current directory.

1. The script does the following;
    1. Creates a new django project with name as the basename of the specified
       `project_path`
    1. Creates a new demo database.
    1. Creates two users, teacher and student.
    1. Loads demo questions.
    1. Loads demo quiz.

1. To run the server, run:

        $ yaksh run relpath/or/abspath/to/demo

1. In a new terminal run the following command which executes user submitted
   code safely:

        $ sudo yaksh run_code_server

1. Open your browser and open the URL ```http://localhost:8000/exam```

1. Login as a teacher to edit the quiz or as a student to take the quiz
    Credentials:
    - Student - Username: student | Password: student
    - Teacher - Username: teacher | Password: teacher

1. User can also login to the Default Django admin using;
    - Admin - Username: admin | Password: admin


History
=======

At FOSSEE, Nishanth had implemented a nice django based app to
test for multiple-choice questions. Prabhu Ramachandran was inspired by a
programming contest that he saw at PyCon APAC 2011.  Chris Boesch, who
administered the contest, used a nice web application
[Singpath](http://singpath.com) that he had built on top of GAE that
basically checked your Python code, live. This made it fun and interesting.

Prabhu wanted an implementation that was not tied to GAE and hence wrote
the initial cut of what is now 'Yaksh'. The idea being that
anyone can use this to test students programming skills and not have to worry
about grading their answers manually and instead do so on their machines.

The application has since been refactored and maintained by FOSSEE Developers.

Contact
=======

For further information and support you can contact

Python Team at FOSSEE: pythonsupport@fossee.in

License
=======

This is distributed under the terms of the BSD license.  Copyright
information is at the bottom of this file.

Authors
=======

 [FOSSEE Developers] (https://github.com/FOSSEE/online_test/graphs/contributors)


Copyright (c) 2011-2017 FOSSEE (fossee.in)
