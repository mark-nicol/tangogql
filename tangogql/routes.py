#!/usr/bin/env python3

import asyncio
from aiohttp import web

import json
import jwt
import os

from graphql_ws.aiohttp import AiohttpSubscriptionServer
from graphql import format_error
from graphql.execution.executors.asyncio import AsyncioExecutor

from tangogql.schema.tango import tangoschema
from tangogql.schema.mutations import UserUnauthorizedException

from tangogql.schema.errors import ErrorParser

subscription_server = AiohttpSubscriptionServer(tangoschema)
routes = web.RouteTableDef()

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
<<<<<<< HEAD
            parsed_errors = [ErrorParser.parse(e) for e in(response.errors)]
            data['errors'] = ErrorParser.remove_duplicated_errors(parsed_errors)
=======
            data['errors'] = [ErrorParser.parse(e) for e in response.errors]
>>>>>>> 041a5f72cd080bb9836b75f51121c40f3b2100f3
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
    try:
        token = request.cookies.get("webjive_jwt", "")
        secret = os.environ.get("SECRET", "")
        claims = jwt.decode(token, secret)
        user = claims.get("username")
        groups = claims.get("groups", [])
    except jwt.InvalidTokenError:
        user = None
        groups = []

<<<<<<< HEAD
def _build_context(request):
    user = None
    if 'webjive_token' in request.cookies:
        token = request.cookies['webjive_token']

        user = r.get(token)
        if user != None:
            user = user.decode('UTF-8')

        # For some reason, the redis module does not always return a proper
        # None value, but a string containing the value 'None'. Horrible.
        if user == 'None':
            user = None

    return {
        "user": user
    }
=======
    return {"user": user, "groups": groups}
>>>>>>> 041a5f72cd080bb9836b75f51121c40f3b2100f3
