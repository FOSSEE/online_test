Installation
=============

To install/deploy this app follow the steps below:

 1. Clone this repository and cd to the cloned repo.

 2. Run::

      $ python manage.py syncdb
      [ enter password etc.]

 3. Add questions by editing the sample_questions.xml or any other xml
    file in the same format and then run the following::

      $ python manage.py load_questions sample_questions.xml

    Note that you can supply multiple xml files as arguments and all of
    those will be added to the database.
    
 4. First run the python server provided.  This ensures that the code is 
    executed in a safe environment.  Do this like so::
    
      $ sudo python python_server.py
      
    Using sudo is necessary since the server is run as the user "nobody".

 5. Now, run::
 
    $ python manage.py runserver <desired_ip>:<desired_port>

 6. Go to http://server_ip:server_port/admin

 7. Login with your credentials and look at the questions and modify if
    needed.

 8. Now ask users to login at:
    http://server_ip:server_port/exam

    And you should be all set.
    
 9. Note that the directory "output" will contain directories, one for each
    user.  Users can potentially write output into these that can be used
    for checking later.


WARNING:  django is running in debug mode for this currently, CHANGE it
during deployment.  To do this, edit settings.py and set DEBUG to False.

The file sample_questions.xml is a template that you can use for your
own questions.

Deploying via Apache
=====================

For any serious deployment, you will need to deploy the app using a real
webserver like Apache.  The ``apache/django.wsgi`` script should make it
easy to deploy this using mod_wsgi.  You will need to add a line of the
form:

        WSGIScriptAlias / "/var/www/online_test/apache/django.wsgi"

to your apache.conf.  For more details see the Django docs here:

https://docs.djangoproject.com/en/1.3/howto/deployment/modwsgi/

