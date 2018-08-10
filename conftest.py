#!/usr/bin/env python3

"""Configuration and commons for tests."""

# build-in modules

# third-party modules
import pytest
from graphene.test import Client
# changes to the path ...

# project modules
from tangogql.schema import tangoschema
# import queries

__author__ = "antmil"
__docformat__ = "restructuredtext"


class TangogqlClient(object):
    def __init__(self):
        self.client = Client(tangoschema)

    def execute(self, query):
        return self.client.execute(query)['data']


@pytest.fixture
def client():
    client = TangogqlClient()
    return client
