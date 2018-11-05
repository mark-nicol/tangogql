############################################################
# Dockerfile to build a deployment container for mtango-py
# Based on Ubuntu and miniconda
############################################################

# To build an image, e.g.:
# $ docker build . -t docker.maxiv.lu.se/graphql
#
# To run it, e.g.:
# $ docker run -d -p 5004:5004  -e TANGO_HOST=w-v-kitslab-csdb-0:10000 --name=graphql docker.maxiv.lu.se/graphql

FROM continuumio/miniconda3

RUN apt-get update && \
    apt-get -y install build-essential

COPY environment.yml /tmp/environment.yml

# Install pytango without specifying version:
# RUN /bin/bash -c "source activate graphql && conda install pytango -c tango-controls"
# COPY requirements.txt /tmp/requirements.txt
# RUN /bin/bash -c "source activate graphql && pip install -r /tmp/requirements.txt"

RUN conda update -n base conda && \
    conda env create --name graphql python=3.6 --file=/tmp/environment.yml

RUN git clone https://gitlab.maxiv.lu.se/vinmic/python3-taurus-core.git
WORKDIR python3-taurus-core
RUN  /bin/bash -c "source activate graphql && python setup.py install"

COPY . web-maxiv-graphql
WORKDIR web-maxiv-graphql

# run the web service
EXPOSE 5004

CMD  /bin/bash -c "source activate graphql && python -m tangogql"
