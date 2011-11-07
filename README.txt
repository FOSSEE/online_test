Installation
=============

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


WARNING:  django is running in debug mode for this currently, CHANGE it
during deployment

A sample question
==================

Here is an example of a good question and tests for it.  On the admin
interface after you login, add a new question with the following fields:

    Summary: Fibonnaci

    Question: Write function called "fib" which takes a single integer
    argument (say "n") and returns a list of the first "n" fibonacci
    numbers.  For example fib(3) -> [1, 1, 2].

    Points: 1

    Test:
    assert fib(3) == [1, 1, 2]
    assert fib(6) == [1, 1, 2, 3, 5, 8]
