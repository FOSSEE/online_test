Yaksh
========
[![Build Status](https://travis-ci.org/FOSSEE/online_test.svg?branch=master)](https://travis-ci.org/FOSSEE/online_test)

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

#### Pre-Requisite

1. Ensure [pip](https://pip.pypa.io/en/latest/installing.html) is installed

#### Installation

1. Install the yaksh
    - For latest stable release
    
            pip install yaksh

    - For the development version

            pip install git+https://github.com/FOSSEE/online_test.git

1. In the terminal run
        
        yaksh create_demo [-p PATH] [project_name]
    - ```project_name``` is the desired name of the django project.
    - In case a ```project_name``` is not specified, the project is initialised with the name ```yaksh_demo```
    - PATH is an optional flag to specify where the django project will be installed
    - If PATH is not provided, the project is created in the current directory

1. The script does the following;
    1. Creates a new django project called `project_name`
    1. Creates a new demo database
    1. Creates two users, test moderator and test examinee
    1. Loads demo questions
    1. Loads demo quiz

1. Run:

        yaksh run_demo

1. In a new terminal run:

        sudo yaksh run_code_server

1. Open your browser and open the URL ```http://localhost:8000/exam```

1. Login as a teacher to edit the quiz or as a student to take the quiz
    Credentials:
    - Student - Username: student | Password: student
    - Teacher - Username: teacher | Password: teacher

Inspiration
===========

At FOSSEE, Nishanth had implemented a nice django based app to
test for multiple-choice questions. I was inspired by a
programming contest that I saw at PyCon APAC 2011.  Chris Boesch, who
administered the contest, used a nice web application 
[Singpath](http://singpath.com) that he had built on top of GAE that 
basically checked your Python code, live. This made it fun and interesting.

I wanted an implementation that was not tied to GAE and decided to write
one myself and the result is the "exam" app.  The idea being that I can
use this to test students programming skills and not have to worry about
grading their answers myself and I can do so on my machines.


Contact
=======

For further information and support you can contact

* Forum Link
* Email Address

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
