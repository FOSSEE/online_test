============
Installation
============

Installing Yaksh
----------------


**Pre-Requisite**

* Ensure  `pip <https://pip.pypa.io/en/latest/installing.html>`_ is installed

**For installing Yaksh**

	1. **Clone the repository**::

            $ git clone https://github.com/FOSSEE/online_test.git

	2. **Go to the online_test directory**::

			$ cd ./online_test

	3. **Install the dependencies** -
		* For Python 2 use::

			$ pip install -r ./requirements/requirements-py2.txt

		* For Python 3 (recommended) use::

			$ pip install -r ./requirements/requirements-py3.txt


Quick Start
-----------

1. **Start up the code server that executes the user code safely**:
	* To run the code server in a sandboxed docker environment, run the command::

		$ invoke start

	.. note::

		Make sure that you have Docker installed on your system beforehand.
		Find docker installation guide `here <https://docs.docker.com/engine/installation/#desktop>`_.

	* To run the code server without docker, locally use::

		$ invoke start --unsafe

	.. note::

		Note this command will run the yaksh code server locally on your machine and is susceptible to malicious code. You will have to install the code server requirements in sudo mode.

2. **On another terminal, run the application using the following command**
	* To start the django server::

		$ invoke serve

	.. note::

		The serve command will run the django application server on the 8000 port and hence this port will be unavailable to other processes.

3. **Open your browser and open the URL** - ``http://localhost:8000/exam``

4. **Login as a teacher to edit the quiz or as a student to take the quiz**
	
	* Credentials:
		For Student:
			* Username: student
			* Password: student
		For Teacher:
			* Username: teacher
			* Password: teacher

5. **User can also login to the Default Django admin by going to URL and entering the following admin credentials** ``http://localhost:8000/admin``
	For admin:
		* Username: admin
		* Password: admin
