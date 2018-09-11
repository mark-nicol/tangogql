# Tango GraphQL

A GraphQL interface for Tango.

## Description

This is an attempt at using "modern" web standards to make a TANGO web service. It provides websocket communication for subscribing to attributes, and a GraphQL interface to the TANGO database.

## Usage

> Warning: This project is still in an early face and under a heavy development going on.

The server is written in Python and currently requires python 3.6 or later.

It uses Taurus, which is not officially supporting python 3 yet, but Vincent Michel has made a port of the "core" part of Taurus (e.g. minus the Qt parts) which can be found at the internal MAXIV repository: https://gitlab.maxiv.lu.se/vinmic/python3-taurus-core

MAXIV don't make that version available due to an incoming support for Python 3 in the official Taurus project. More information available here: 
https://github.com/taurus-org/taurus/pull/703

__aiohttp__ is used for the web server part, "graphite" for the GraphQL part. "requirements.txt" should list the necessary libraries, which can be installed using "pip". Also, a Conda environment can be created using the *_environment.yml*_.

If preferred, a Dockerfile is provided and can be used to run the server.

If the intention is to run it manually, once all the dependencies are installed, you can start the server by doing:

```shell
$ python -m tangogql
```

The requests are made to the url: http://localhost:5004/db

## Installation

At the moment of writing this, there is no packaging system ready, making the best deployment option the usage of the Docker Container.

## License

TangoGQL is released under the license that can be found in the LICENCE file in the root directory of the project.

## Authors

Tango GraphQL was written by the KITS Group at MAX IV Laboratory.

Special thanks to:

- Johan Forsberg and Vincent Michel
- Linh Nguyen