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