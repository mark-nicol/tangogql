FROM continuumio/miniconda3:4.5.12
EXPOSE 5004

SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
    apt-get -y install build-essential && \
    apt-get clean

COPY environment.yml /tmp/environment.yml

RUN conda update -n base conda && \
    conda env create --name graphql python=3.6 --file=/tmp/environment.yml && \
    git clone https://gitlab.maxiv.lu.se/vinmic/python3-taurus-core.git && \
    cd python3-taurus-core && \
    source activate graphql && \
    python setup.py install && \
    conda clean -a -y

WORKDIR /tangogql
COPY . .

CMD source activate graphql && python -m tangogql
