#### Pre-Requisites

	1. Install Docker https://docs.docker.com/engine/installation/
	2. Install Docker Compose https://docs.docker.com/compose/install/#install-compose
	3. install git 


#### Help for deploying Yaksh interface.

	- To get help while deployment
		$ make help

	- Clone yaksh form github:
		$ make clone

	- Build docker images:
		$ make build

	- To run containers:
		$ make start

	- You need to create super a user to work with yaksh:
		$ make createsuperuser

	- Now Your interface is ready. You can access it using browser just go to http://localhost:8000

	- Clean your docker containers:
		$ make clean

	- other utilities like restart, tail, status
