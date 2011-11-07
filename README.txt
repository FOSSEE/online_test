To install/deploy this app follow the steps below:

 1. Clone this repository.
 2. cd to the cloned repo.
 3. Run $ python manage.py syncdb
    [ enter password etc.]
 4. Run $ python manage.py runserver <desired_ip>:<desired_port>
 5. Go to http://server_ip:server_port/admin
 6. Login with your credentials and add questions to the database.
 7. Now ask users to login at:
    http://server_ip:server_port/exam

    And you should be all set.


