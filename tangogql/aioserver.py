#!/usr/bin/env python3

"""A simple http backend for communicating with a TANGO control system

The idea is that each client establishes a websocket connection with
this server (on /socket), and sets up a number of subscriptions to
TANGO attributes.  The server keeps track of changes to these
attributes and sends events to the interested clients. The server uses
Taurus for this, so polling, sharing listeners, etc is handled "under
the hood".

There is also a GraphQL endpoint (/db) for querying the TANGO database.
"""

import logging
import aiohttp
import aiohttp_cors
import asyncio
import uuid
import os
import json
import sys

__all__ = ['run']


def ensure_connectivity(retries=5, sleep_duration=5):
    """
    Attempt to connect to the TANGO host specified by the TANGO_HOST
    environment variable by instantiating a PyTango.Database object. Upon
    failure it will retry up to `retries` times, sleeping for `sleep_duration`
    seconds between attempts. If no connection can be established even after
    retrying, it will cause the program to exit with code 1. Progress is
    reported to stdout as follows:

    (1/5) Trying to connect to tango-host:10000... Failed! Retrying in 5 seconds.
    (2/5) Trying to connect to tango-host:10000... Failed! Retrying in 5 seconds.
    (3/5) Trying to connect to tango-host:10000... Connected!

    :param retries: The number of retries before exiting
    :param sleep_duration: The number of seconds to sleep between attempts.
    :returns: None
    """

    import PyTango, time
    host = os.getenv("TANGO_HOST")

    for retry in range(1, retries+1):
        print(f"({retry}/{retries}) Trying to connect to {host}...", end="")
        try:
            PyTango.Database()
        except PyTango.ConnectionFailed:
            print(f" Failed!", end="")
            if retry == retries:
                print()
                sys.exit(1)
            else:
                print(f" Retrying in {sleep_duration} seconds.")
                time.sleep(sleep_duration)
        else:
            print(" Connected!")
            break

# A factory function is needed to use aiohttp-devtools for live reload functionality.
def setup_server():
    ensure_connectivity()

    from tangogql.routes import routes
    from tangogql.config import Config

    app = aiohttp.web.Application(debug=True)

    config = Config(open("config.json"))
    app["config"] = config

    defaults_dict = {"*": aiohttp_cors.ResourceOptions(
                                            allow_credentials=True,
                                            expose_headers="*",
                                            allow_headers="*")
                     }

    cors = aiohttp_cors.setup(app, defaults=defaults_dict)
    app.router.add_routes(routes)
    for r in list(app.router.routes()):
        cors.add(r)
    app.router.add_static('/', 'static')

    return app

def setup_logger(logfile):
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    max_mega_bytes = 15
    log_file_size_in_bytes = max_mega_bytes * (1024*1024)

    # file_handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=log_file_size_in_bytes, backupCount=5)
    # file_handler.setLevel(logging.INFO)
    # file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    # logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logger.debug("Logging setup done. Logfile: " + logfile)

    return logger

def setup():
    logfile = None
    if os.environ.get("HOSTNAME"):
        logfile = os.environ.get("HOSTNAME")
    else:
        logfile = uuid.uuid4().hex

    if os.environ.get("LOG_PATH"):
        logfile = os.environ.get("LOG_PATH") + "/" + logfile
    else:
        logfile = "/tmp/" + logfile

    logfile = logfile + ".log"

    return (
        setup_server(),
        setup_logger(logfile)
    )

# Called by aiohttp-devtools when restarting the dev server.
# Not used in production
def dev_run():
    (app, _) = setup()
    return app

def run():
    (app, logger) = setup()

    # if is_configuration_corrupt("config.json"):
    #     sys.exit(1)

    loop = asyncio.get_event_loop()
    handler = app.make_handler(debug=True)
    f = loop.create_server(handler, '0.0.0.0', 5004)

    # TODO: Get this value from an environment variable
    # hostname = "http://w-v-kitslab-web-0:5004/graphiql"
    hostname = "http://localhost:5004/graphiql"

    logger.debug(f"Point your browser to {hostname}")
    srv = loop.run_until_complete(f)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Ctrl-C was pressed")
    finally:
        loop.run_until_complete(handler.shutdown())
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.cleanup())
    loop.close()

if __name__ == "__main__":
    run()
