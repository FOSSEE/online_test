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
    - Clone the repository

            $ git clone https://github.com/FOSSEE/online_test.git

    - Go to the online_test directory

            $ cd ./online_test

    - Install the dependencies

            $ pip install -r ./requirements/requirements-py3.txt

#### Short instructions

1. To see a quick demo after installing yaksh do the following:

        $ invoke serve

1.  On another terminal start up the code server that executes the user code safely:

    - To run the code server in a sandboxed docker environment, run the command:

        $ invoke start

    - Make sure that you have docker installed on your system beforehand


    - To run the code server without docker, locally use:

        $ invoke start --unsafe

    - Note this command will run the yaksh code server locally on your machine
      and is susceptible to malicious code.



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
