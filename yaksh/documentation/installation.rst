============
Installation
============

Installing Yaksh
----------------


**Pre-Requisite**

* Ensure  `pip <https://pip.pypa.io/en/latest/installing.html>`_ is installed

**For installing Yaksh**

	* For latest stable release::
    
            $ pip install yaksh

	* For the development version::

			$ pip install git+https://github.com/FOSSEE/online_test.git

Quick Start
-----------

**In the terminal run**::

	yaksh create_demo [-p PATH] [project_name]

* **project_name** 
	The desired name of the django project. In case a project_name is not specified, the project is initialised with the name yaksh_demo
* **PATH**
	 An optional flag to specify where the django project will be installed.  If PATH is not provided, the project is created in the current directory

**Now execute**::

	$ yaksh run_demo

This starts the web server at localhost

**In a new terminal, execute**::

	$ sudo yaksh run_code_server

This starts the code server

**Open your browser and go to URL** ::
	
	http://localhost:8000/exam

**Login as a teacher to edit the quiz or as a student to take the quiz Credentials:**

	For Student:
		* Username: student
		* Password: student

	For Teacher:
		* Username: teacher 
		* Password: teacher

**User can also login to the Default Django admin by going to URL**:: 

		http://localhost:8000/admin

**And entering the following admin credentials**
	* Username: admin
	* Password: admin

Running The Code Server
-----------------------

**Local Instance**:

In a new terminal run the command::

	sudo python /path/to/code_server.py

Keep this instance running in the background

**Using Docker**:

1. Install docker 

2. Create a Docker Image using the Docker file:

	* Go to the directory where the project is located::

		cd /path/to/online_test

	* Build a docker image using the Dockerfile::

		sudo docker build --tag=yaksh_code_server:v1 .

3. Start a Docker container::

		docker run -d -p 8001:8001 -p 53579:53579 -v /path/to/online_test/yaksh/output:/src/yaksh/output yaksh_code_server:v1

**Note**:
	* The default ports on which the code server runs and the pool port on which the former ports are available is specified in online_test/yaksh/settings.py. The code server also supports multiple ports

	* The server port is 8001 by default, this can be changed in the settings::
	
		SERVER_PORTS = 8001

	* Multiple ports can be specified as::
	
		SERVER_PORTS = [8001, 8002, 8003, 8004, 8005] # Or use range(8001, 8040) for larger number of ports

	* The default pool port is 53579 by default, this can be changed in the settings::
	
		SERVER_POOL_PORT = 53579

	* The docker command to start a docker container when using multiple ports is::
	
		docker run -d -p 8001-8039:8001-8039 -p 53579:53579 yaksh_code_server:v1
