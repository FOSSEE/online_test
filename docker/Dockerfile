FROM ubuntu:16.04

MAINTAINER FOSSEE <pythonsupport@fossee.in>

# Update Packages and Install Python & net-tools
RUN apt-get update -y && apt-get install git python3-pip vim libmysqlclient-dev sudo -y

RUN apt-get install -y  software-properties-common && \
echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
add-apt-repository -y ppa:webupd8team/java && \
apt-get update && \
apt-get install -y oracle-java8-installer && \
apt-get install -y python net-tools scilab build-essential python3-numpy python3-scipy ipython3 ipython3-notebook python3-pandas python3-nose
