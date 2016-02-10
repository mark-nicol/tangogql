import json
import time
from weakref import WeakSet, WeakValueDictionary

import asyncio
import aiohttp
from aiohttp import web
import bson
from PyTango import DeviceProxy, set_green_mode, GreenMode, ExtractAs
from PyTango import DeviceAttributeConfig, DeviceAttribute
from PyTango import EventType, DevFailed
import PyTango

from schema import tangoschema

# requires vinmic's "asyncio-support" PR
set_green_mode(GreenMode.Asyncio)


def dictify(attr, event):
    "Turn an event into a dict action"
    if isinstance(event, DeviceAttribute):
        return {
            "type": "CHANGE",
            "data": {
                attr: {
                    "name": event.name,
                    "value": event.value,
                    "type": event.type,
                    "format": event.data_format
                }
            }
        }


def serialize(events, protocol="json"):
    "Returns event data in a serialized form according to a protocol"
    if protocol == "json":
        return json.dumps({
            "events": [dictify(attr, event) for attr, event in events]
        })
    elif protocol == "bson":
        # "Binary JSON" protocol. A lot more space efficient than
        # encoding as JSON, especially for float values and arrays.
        # There's very little size overhead.
        # Have not looked into encoding performance.
        return bson.dumps({
            "events": [dictify(attr, event) for attr, event in events]
        })
    raise ValueError("Unknown protocol '%s'" % protocol)


class Listener():

    """This thing reads TANGO device attributes and sends the results
    to websocket clients."""

    _readers = {}
    _sockets = {}
    _queues = WeakValueDictionary()

    def __init__(self, period=0.1, rate_limit=0.2):
        self.period = period
        self.rate_limit = rate_limit

    async def _subscribe(self, name):
        device, attr = name.rsplit("/", 1)
        proxy = DeviceProxy(device)
        try:
            await proxy.subscribe_event(attr, EventType.CHANGE_EVENT,
                                        self,  # PyTango.utils.EventCallBack(),
                                        extract_as=ExtractAs.Bytes)
            print("successfully subscribed to %s/%s" % (device, attr))
        except DevFailed:
            print("could not subscribe to %s/%s; polling" % (device, attr))
            reader = self._reader(proxy, attr)
            loop = asyncio.get_event_loop()
            loop.create_task(reader)

    async def _reader(self, proxy, attr):
        """Coroutine that periodically reads an attribute and puts the
        result on the queues of all listening sockets, as long as there
        are any. One reader per attribute."""
        # this is a bit over complicated; shouldn't have to care about
        # sockets at all? Also, inefficient to read one attribute at a time.
        fullname = "%s/%s" % (proxy.dev_name(), attr)
        while True:
            await asyncio.sleep(self.period)  # TODO: take read time into account
            sockets = self._sockets.get(fullname)
            if not sockets:
                # nobody listening to this attribute; we're done here
                break
            try:
                result = await proxy.read_attribute(
                    attr, extract_as=ExtractAs.Bytes)
            except Exception as e:
                print(e)
                continue
            for socket in sockets:
                try:
                    self._queues[socket].put_nowait((fullname, result))
                except asyncio.QueueFull:
                    pass
                except KeyError:
                    pass
                del socket  # let go of the reference
        print("listener %s exited" % fullname)

    async def _sender(self, queue, socket):
        """A coroutine that monitors a queue, collecting events into buckets
        that are periodically sent to a socket. It acts as a rate limiter
        and smooths out the traffic over the websocket.  Note that all
        received data is sent, it's just delayed and chunked."""
        # there shoud be one sender per ws client
        while True:
            t0 = time.time()
            events = []
            while time.time() - t0 < self.rate_limit:
                # TODO: improve this inner loop
                try:
                    event = queue.get_nowait()
                    events.append(event)
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0.01)
            if not events:
                continue
            try:
                data = serialize(events, socket.protocol)
                if isinstance(data, bytes):
                    socket.send_bytes(data)
                else:
                    socket.send_str(data)
            except RuntimeError as e:
                # guess the client must be gone. Maybe there's a neater
                # way to detect this.
                print(e)
                break
        print("Sender for %r exited" % socket)

    def push_event(self, event):
        "Receives all events and puts them on the appropriate queues"
        if event.attr_value:
            device = event.device.dev_name()
            attr = event.attr_value.name
            name = "%s/%s" % (device, attr)
            sockets = self._sockets[name]
            for socket in sockets:
                self._queues[socket].put_nowait((name, event.attr_value))

    async def subscribe_attribute(self, attr, socket):
        "Start listening to the given attribute with the given socket"
        if socket not in self._queues:
            queue = self._queues[socket] = asyncio.Queue(maxsize=100)
            sender = self._sender(queue, socket)
            loop = asyncio.get_event_loop()
            loop.create_task(sender)
        if attr in self._sockets:
            self._sockets[attr].add(socket)
        else:
            self._sockets[attr] = WeakSet([socket])
            await self.add_reader(attr)

    def unsubscribe_attribute(self, attr, socket):
        "Stop listening to an attribute from a socket"
        self._sockets.get(attr, {}).remove(socket)

    async def add_reader(self, fullname):
        await self._subscribe(fullname)

    async def handle_websocket(self, request):

        "Handles a websocket to a client over its lifetime"

        ws = web.WebSocketResponse(protocols=("json", "bson"))
        await ws.prepare(request)

        print("Listener has connected; protocol %s" % ws.protocol)

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
                            await self.subscribe_attribute(attr, ws)
                            print("add listener for '%s'" % attr)
                    elif action["type"] == "UNSUBSCRIBE":
                        for attr in action["models"]:
                            print("remove listener for '%s'" % attr)
                            self.unsubscribe_attribute(attr, ws)
                elif msg.tp == aiohttp.MsgType.error:
                    print('websocket closed with exception %s' %
                          ws.exception())
            except RuntimeError as re:
                print("websocket died: %s" % re)

        print('websocket connection closed')

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

    listener = Listener(period=1.0)

    app.router.add_route('GET', '/socket', listener.handle_websocket)
    app.router.add_route('POST', '/db', db_handler)
    app.router.add_static('/', "static")

    loop = asyncio.get_event_loop()
    handler = app.make_handler(debug=True)
    f = loop.create_server(handler, '127.0.0.1', 5003)
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
