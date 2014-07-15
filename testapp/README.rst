===============
Online Exam
===============

Online test application lets user(student) take an online programming test.
A special user called moderator can add questions, create question paper, 
conduct online test and monitor the test.


Quick start
------------

1. Add "exam", "taggit" and "taggit_autocomplete_modified" apps 
   to your INSTALLED_APPS setting as follows:

    INSTALLED_APPS =(
        'exam',
        'taggit',
        'taggit_autocomplete_modified',
    )

2. In project settings, add AUTH_PROFILE_MODULE = 'exam.Profile'
   You can change the exam.Profile to your desired app user profile.

3. Include the "exam" and taggit_autocomplete_modified URL configuration
   in your project urls.py as follows:

    url(r'^exam/', include('exam.urls')),
    url(r'^taggit_autocomplete_modified/', include\
                                        ('taggit_autocomplete_modified.urls'))

4. Since taggit_autocomplete_modified version for django=>1.5 is not available
   you have to do one change manually. In taggit_autocomplete_modified app url,
   remove "default" from the import statement as follows:

    Change:  from django.conf.urls.defaults import *
    to    :  from django.conf.urls import *

    Note: location of the above file will probably be as 
        ../lib/python2.7/site-packages/taggit_autocomplete_modified/urls.py

5. Run 'python manage.py syncdb' to create "exam" models.

6. Start the development server and visit http://localhost:8000/exam/

7. In exam app run code sever as superuser as follows:

   sudo python code_server.py

   Note: location of the above file will probably be as 
        ../lib/python2.7/site-packages/exam/code_server.py
