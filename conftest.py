#!/usr/bin/env python3

"""Configuration and commons for tests."""

# build-in modules

# third-party modules
import pytest
from graphene.test import Client
# changes to the path ...

# project modules
from tangogql.schema.tango import tangoschema
# import queries

import asyncio
from graphql.execution.executors.asyncio import AsyncioExecutor

__author__ = "antmil"
__docformat__ = "restructuredtext"


class TangogqlClient(object):
    def __init__(self):
        self.client = Client(tangoschema)

    def execute(self, query):
        loop = asyncio.get_event_loop()
        r =  self.client.execute(query, executor=AsyncioExecutor(loop=loop))
        return r["data"]

@pytest.fixture
def client():
    client = TangogqlClient()
    return client
