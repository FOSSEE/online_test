FROM debian:8.2
MAINTAINER FOSSEE <pythonsupport@fossee.in>

# Update Packages and Install Python & net-tools
RUN apt-get update && apt-get install -y python net-tools \
    python-pip openjdk-7-jdk openjdk-7-jre python-pip

RUN pip install numpy pandas scipy matplotlib

# Copy the project folder from host into container
COPY ./yaksh /src/yaksh

# Run Yaksh code server
CMD ["python", "/src/yaksh/code_server.py"]
