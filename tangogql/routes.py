#!/usr/bin/env python3

import asyncio
from aiohttp import web

import json
# import redis

from graphql_ws.aiohttp import AiohttpSubscriptionServer
from graphql import format_error
from graphql.execution.executors.asyncio import AsyncioExecutor

from tangogql.schema.tango import tangoschema
from tangogql.schema.mutations import UserUnauthorizedException

subscription_server = AiohttpSubscriptionServer(tangoschema)
routes = web.RouteTableDef()

# r = redis.StrictRedis(host='redis', port=6379)

# FIXME: aiohttp doesn't support automatic serving of index files when serving
#        directories statically, so we need to define a number of routes to
#        serve the GraphiQL interface. Is there a better way?
@routes.get('/graphiql')
async def graphiql_noslash(request):
    return web.HTTPFound('/graphiql/')


@routes.get('/graphiql/')
async def graphiql(request):
    return web.FileResponse("./static/graphiql/index.html")

routes.static('/graphiql/css', 'static/graphiql/css')
routes.static('/graphiql/js', 'static/graphiql/js')



@routes.post("/db")
async def db_handler(request):
    """Serve GraphQL queries."""
    loop = asyncio.get_event_loop()
    payload = await request.json()
    query = payload.get("query")
    variables = payload.get("variables")

    context = _build_context(request)

    # Spawn query as a coroutine using asynchronous executor
    response = await tangoschema.execute(
        query,
        variable_values=variables,
        context_value=context,
        return_promise=True,
        executor=AsyncioExecutor(loop=loop),
    )
    data = {}
    if response.errors:
        if isinstance(response.errors[0].original_error, UserUnauthorizedException):
            return web.HTTPUnauthorized()
        else:
            data['errors'] = [format_error(e) for e in response.errors]
    if response.data:
        data["data"] = response.data
    jsondata = json.dumps(data)

    return web.Response(
        text=jsondata, headers={"Content-Type": "application/json"}
    )


@routes.get("/socket")
async def socket_handler(request):
    ws = web.WebSocketResponse(protocols=("graphql-ws",))
    await ws.prepare(request)
    await subscription_server.handle(ws)
    return ws



def _build_context(request):
    user = None
    #
    # TODO: retrieve user information from JWT instead
    #
    # if 'webjive_token' in request.cookies:
    #     token = request.cookies['webjive_token']
    #
    #     user = r.get(token)
    #     if user != None:
    #         user = user.decode('UTF-8')
    #
    #     # For some reason, the redis module does not always return a proper
    #     # None value, but a string containing the value 'None'. Horrible.
    #     if user == 'None':
    #         user = None
    #
    return {
        "user": user
    }
