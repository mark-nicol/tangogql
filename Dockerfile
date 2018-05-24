############################################################
# Dockerfile to build a deployment container for mtango-py
# Based on Ubuntu and miniconda
############################################################

# To build an image, e.g.:
# $ docker build . -t docker.maxiv.lu.se/dev-maxiv-graphql
#
# To run it, e.g.:
# $ docker run -d -p 5004:5004  -e TANGO_HOST=w-v-kitslab-csdb-0:10000 --name=graphql docker.maxiv.lu.se/dev-maxiv-graphql

FROM continuumio/miniconda3

RUN apt-get update
RUN apt-get -y install build-essential
ADD environment.yml /tmp/environment.yml
RUN conda env create --name graphql python=3.5 --file=/tmp/environment.yml

RUN git clone https://gitlab.maxiv.lu.se/vinmic/python3-taurus-core.git
WORKDIR python3-taurus-core
RUN  /bin/bash -c "source activate graphql && python setup.py install"

WORKDIR /
RUN git clone https://gitlab.maxiv.lu.se/kits-maxiv/web-maxiv-graphql.git

WORKDIR dev-maxiv-graphql

# run the web service
EXPOSE 5004
CMD  /bin/bash -c "source activate graphql && python aioserver.py"
