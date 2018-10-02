# Tango GraphQL

A GraphQL interface for Tango.

## Description

This is an attempt at using "modern" web standards to make a TANGO web service. It provides websocket communication for subscribing to attributes, and a GraphQL interface to the TANGO database.

## Usage

> Warning: This project is still in an early face and under a heavy development going on.

The server is written in Python and currently requires python 3.6 or later.

It uses Taurus, which is not officially supporting Python 3 yet, but a port of the Taurus Core has been done at MAX IV, and can be found at the repository: https://gitlab.com/MaxIV/python3-taurus-core

That repository is unofficial and not supported, it's only used while the official Taurus project is moving to Python 3. Once Taurus will be supporting Python 3 officially, that repository will be removed. More information about Taurus and Python 3 can be found here: https://github.com/taurus-org/taurus/pull/703

__aiohttp__ is used for the web server part, "graphite" for the GraphQL part. "requirements.txt" should list the necessary libraries, which can be installed using "pip". Also, a Conda environment can be created using the *_environment.yml*_.

If preferred, a Dockerfile is provided and can be used to run the server.

If the intention is to run it manually, once all the dependencies are installed, you can start the server by doing:

```shell
$ python -m tangogql
```

The requests are made to the url: http://localhost:5004/db

## Installation

At the moment of writing this, there is no packaging system ready, making the best deployment option the usage of the Docker Container.

1. `cd` into the `web-maxiv-tangoql` directory and run `docker-compose up`.
2. Wait
3. Open your browser to [localhost:5004/graphiql](http://localhost:5004/graphiql) to verify that it works.

A tool called [aiohttp-devtools](https://github.com/aio-libs/aiohttp-devtools) is used to auto-reload the server inside the Docker container whenever the code changes.

## License

TangoGQL is released under the license that can be found in the LICENCE file in the root directory of the project.

## Authors

Tango GraphQL was written by the KITS Group at MAX IV Laboratory.

Special thanks to:

- Johan Forsberg and Vincent Michel
- Linh Nguyen
