from aiohttp import web
import logging
from schema import tangoschema
import json
from graphql_ws.aiohttp import AiohttpSubscriptionServer
from graphql import format_error

subscription_server = AiohttpSubscriptionServer(tangoschema)
routes = web.RouteTableDef()

@routes.get('/graphiql')
async def graphiql(request):
    return web.FileResponse("./static/graphiql.html")
    
@routes.post('/db')
async def db_handler(request):
    "serve GraphQL queries"
    payload = await request.json()
    print (payload)
    response = await tangoschema. execute(payload.get('query'),variable_values=payload.get('variables'),return_promise = True)
    data = {}
    if response.errors:
        data['errors'] = [format_error(e) for e in response.errors]
    if response.data:
        data['data'] = response.data
    jsondata = json.dumps(data,)
    return web.Response(text=jsondata,headers= {'Content-Type': "appication/json"})

@routes.get('/socket')
async def socket_handler(request):
    ws = web.WebSocketResponse(protocols=('graphql-ws',))
    await ws.prepare(request)
    await subscription_server.handle(ws)
    return ws