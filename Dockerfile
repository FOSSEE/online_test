FROM ubuntu:16.04
MAINTAINER FOSSEE <pythonsupport@fossee.in>

# Update Packages and Install Python & net-tools
RUN apt-get update && \
apt-get install -y  software-properties-common && \
add-apt-repository ppa:webupd8team/java -y && \
apt-get update && \
apt-get install -y software-properties-common python net-tools git python3-pip vim libmysqlclient-dev scilab build-essential oracle-java8-installer && \
mkdir /Sites

VOLUME /src/online_test

WORKDIR /src/online_test
