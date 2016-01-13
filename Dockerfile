FROM debian:8.2
MAINTAINER FOSSEE <pythonsupport@fossee.in>

# Update Packages and Install Python & net-tools
RUN apt-get update && apt-get install -y python net-tools

# Copy the project folder from host into container
COPY ./yaksh /src/yaksh

# Run Yaksh code server
CMD ["python", "/src/yaksh/code_server.py"]
