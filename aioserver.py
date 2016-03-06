import json
import logging
import time
from weakref import WeakSet, WeakValueDictionary

import asyncio
import aiohttp
from aiohttp import web
from PyTango import DeviceProxy
from PyTango import DeviceAttributeConfig, DeviceAttribute
from PyTango import EventType, DevFailed
import PyTango

from schema import tangoschema
from listener import TaurusWebAttribute


def serialize(attr, event, protocol="json"):
    "Returns event data in a serialized form according to a protocol"
    if protocol == "json":
        # default protocol; simplest, human readable, but also very inefficient
        # in particular for spectrum/image data
        return json.dumps({"events": [event]})
    elif protocol == "bson":
        # "Binary JSON" protocol. A lot more space efficient than
        # encoding as JSON, especially for float values and arrays.
        # There's very little size overhead.
        # Have not looked into encoding performance.
        return bson.dumps({"events": event})
    raise ValueError("Unknown protocol '%s'" % protocol)


async def handle_websocket(request):

    "Handles a websocket to a client over its lifetime"

    ws = web.WebSocketResponse(protocols=("json", "bson"))
    await ws.prepare(request)

    logging.info("Listener has connected; protocol %s" % ws.protocol)

    listeners = {}

    def send(attr, event):
        "send an event over the websocket"
        data = serialize(attr, event, ws.protocol)
        if isinstance(data, bytes):
            ws.send_bytes(data)
        else:
            ws.send_str(data)

    # wait for messages over the socket
    # A message must be JSON, in the format:
    #   {"type": "SUBSCRIBE", "models": ["sys/tg_test/double_scalar"]}
    # where "type" can be "SUBSCRIBE" or "UNSUBSCRIBE" and models is a list of
    # device attributes.
    async for msg in ws:
        try:
            if msg.tp == aiohttp.MsgType.text:
                action = json.loads(msg.data)
                if action["type"] == 'SUBSCRIBE':
                    for attr in action["models"]:
                        listener = TaurusWebAttribute(attr, send)
                        listeners[attr] = listener
                        logging.debug("add listener for '%s'", attr)
                elif action["type"] == "UNSUBSCRIBE":
                    for attr in action["models"]:
                        logging.debug("remove listener for '%s'", attr)
                        listener = listeners.pop(attr, None)
                        if listener:
                            listener.clear()
            elif msg.tp == aiohttp.MsgType.error:
                logging.warn('websocket closed with exception %s',
                             ws.exception())
        except RuntimeError as e:
            logging.warn("websocket died: %s", e)

    # wipe all the client's subscriptions
    for listener in listeners.values():
        listener.clear()
    listeners.clear()

    logging.info('websocket connection %s closed' % ws)

    return ws


async def db_handler(request):
    "serve GraphQL queries"
    post_data = await request.json()
    query = post_data["query"]
    loop = asyncio.get_event_loop()  # TODO: this looks stupid
    try:
        # guess we wouldn't have to do this if the client was async...
        result = await loop.run_in_executor(None, tangoschema.execute, query)
        data = (json.dumps({"data": result.data or {}}, indent=4))
        return web.Response(body=data.encode("utf-8"),
                            content_type="application/json")
    except Exception as e:
        print(e)


if __name__ == "__main__":

    app = aiohttp.web.Application(debug=True)

    app.router.add_route('GET', '/socket', handle_websocket)
    app.router.add_route('POST', '/db', db_handler)
    app.router.add_static('/', 'static')

    loop = asyncio.get_event_loop()
    handler = app.make_handler(debug=True)
    f = loop.create_server(handler, '127.0.0.1', 5003)
    logging.info("Point your browser to http://localhost:5003/index.html")
    srv = loop.run_until_complete(f)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Ctrl-C was pressed")
    finally:
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(handler.finish_connections(1.0))
        loop.run_until_complete(app.finish())

    loop.close()
