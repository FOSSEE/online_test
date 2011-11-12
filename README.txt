Installation
=============

To install/deploy this app follow the steps below:

 1. Clone this repository.

 2. cd to the cloned repo.

 3. Run::

      $ python manage.py syncdb
      [ enter password etc.]

 4. Add questions by editing the sample_questions.xml or any other xml
    file in the same format and then run the following::

      $ python manage.py load_questions sample_questions.xml

    Note that you can supply multiple xml files as arguments and all of
    those will be added to the database.
    
 5. First run the python server provided.  This ensures that the code is 
    executed in a safe environment.  Do this like so::
    
      $ sudo python python_server.py
      
    Using sudo is necessary since the server is run as the user "nobody".

 6. Now, run::
 
    $ python manage.py runserver <desired_ip>:<desired_port>

 7. Go to http://server_ip:server_port/admin

 8. Login with your credentials and look at the questions and modify if
    needed.

 9. Now ask users to login at:
    http://server_ip:server_port/exam

    And you should be all set.


WARNING:  django is running in debug mode for this currently, CHANGE it
during deployment

The file sample_questions.xml is a template that you can use for your
own questions.

