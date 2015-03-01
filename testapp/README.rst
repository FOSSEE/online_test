===============
Online Exam
===============

Online test application lets user(student) take an online programming test.
A special user called moderator can add questions, create question paper, 
conduct online test and monitor the test.


Quick start
------------

1. Add "testapp.exam", "taggit" and "taggit_autocomplete_modified" apps 
   to your INSTALLED_APPS setting as follows::

    INSTALLED_APPS =(
        'testapp.exam',
        'taggit',
        'taggit_autocomplete_modified',
    )

2. In project settings, add AUTH_PROFILE_MODULE = 'testapp.exam.Profile'
   You can change the testapp.exam.Profile to your desired app user profile.

3. Include the "testapp.exam" and taggit_autocomplete_modified URL configuration
   in your project urls.py as follows::

    url(r'^exam/', include('testapp.exam.urls')),
    url(r'^taggit_autocomplete_modified/', include\
                                        ('taggit_autocomplete_modified.urls'))


4. Run 'python manage.py syncdb' to create models for the new installed apps.

5. Start the development server and visit http://localhost:8000/exam/

6. In exam app run code_sever command  as superuser as follows::

       $ code_server

   Note: You must have a sudo access to run the above command.
