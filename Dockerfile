FROM debian:8.2
MAINTAINER FOSSEE <pythonsupport@fossee.in>

# Update Packages and Install Python & net-tools
RUN apt-get update && apt-get install -y python net-tools python-pip && pip install tornado

# Copy the project folder from host into container
COPY ./yaksh /src/yaksh

WORKDIR /src

# Run Yaksh code server
CMD ["python", "-m", "yaksh.code_server"]
