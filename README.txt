Experimental web backend for TANGO


DESCRIPTION

This is an attempt at using "modern" - perhaps too modern - web standards to make a TANGO web service. It provides websocket communication for subscribing to attributes, and an (incomplete) GraphQL interface to the TANGO database.

BUILDING/RUNNING

The server is written in Python and currently requires python 3.4 or later (I think).

It uses Taurus, which is not officially supporting python 3 yet, but Vincent Michel has made a port of the "core" part of Taurus (e.g. minus the Qt parts) which can be found at https://gitlab.maxiv.lu.se/vinmic/python3-taurus-core

"aiohttp" is used for the web server part, "graphite" for the GraphQL part. "requirements.txt" should list the necessary libraries, which can be installed using "pip".

Once all is installed, start the server by doing:

  $ python3.5 aioserver.py

The server can be accessed at http://localhost:5004/graphiql.html

