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
from aiohttp import web
import aiohttp_cors
import asyncio
from routes import routes

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    app = aiohttp.web.Application(debug=True)
    cors = aiohttp_cors.setup(app, defaults={
	"*": aiohttp_cors.ResourceOptions(
		allow_credentials=True,
		expose_headers="*",
		allow_headers="*",
	    )
    })
    app.router.add_routes(routes)
    for r in list(app.router.routes()):
        cors.add(r)
    app.router.add_static('/', 'static')
    loop = asyncio.get_event_loop()
    handler = app.make_handler(debug=True)
    f = loop.create_server(handler, '0.0.0.0', 8000)
    logging.info("Point your browser to http://w-v-kitslab-web-0:8000/graphiql")
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
