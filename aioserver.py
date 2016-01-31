import asyncio
import aiohttp
from aiohttp import web
import json

from listener import TaurusWebAttribute
from schema import tangoschema


async def websocket_handler(request):

    "Handles a websocket to a client over its lifetime"

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # keep track of attribute listeners
    attributes = {}

    def send(evt):
        data = json.dumps(evt)
        loop.call_soon_threadsafe(ws.send_str, data)

    # wait for messages over the socket
    async for msg in ws:
        try:
            if msg.tp == aiohttp.MsgType.text:
                action = json.loads(msg.data)
                if action["type"] == 'SUBSCRIBE':
                    for attr in action["models"]:
                        attributes[attr] = TaurusWebAttribute(attr, send)
                        print("add listener for '%s'" % attr)
                elif action["type"] == "UNSUBSCRIBE":
                    for attr in action["models"]:
                        print("remove listener for '%s'" % attr)
                        attributes.pop(attr).clear()
            elif msg.tp == aiohttp.MsgType.error:
                print('websocket closed with exception %s' %
                      ws.exception())
        except RuntimeError as re:
            print("websocket died: %s" % re)

    print('websocket connection closed')

    # clean up after us
    for listener in attributes.values():
        listener.clear()

    return ws


async def db_handler(request):
    "serve GraphQL queries"
    post_data = await request.json()
    query = post_data["query"]
    loop = asyncio.get_event_loop()  # TODO: this looks stupid
    # guess we wouldn't have to do this if the client was async...
    result = await loop.run_in_executor(None, tangoschema.execute, query)
    data = (json.dumps({"data": result.data or {}}, indent=4))
    return web.Response(body=data.encode("utf-8"),
                        content_type="application/json")


if __name__ == "__main__":

    app = aiohttp.web.Application(debug=True)

    app.router.add_route('GET', '/socket', websocket_handler)
    app.router.add_route('POST', '/db', db_handler)
    app.router.add_static('/', "static")

    loop = asyncio.get_event_loop()
    handler = app.make_handler(debug=True)
    f = loop.create_server(handler, '127.0.0.1', 5002)
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
    # FIXME: Sometimes when websockets were used, we get stuck here, only another
    # ctrl-c seems to help.
