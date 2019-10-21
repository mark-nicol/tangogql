#!/usr/bin/env python3

"""A GraphQL schema for TANGO."""

import os
import graphene

from tangogql.schema.query import Query
from tangogql.schema.subscription import Subscription
from tangogql.schema.mutations import Mutations
from tangogql.schema.log import (
    ExcuteCommandUserAction,
    SetAttributeValueUserAction,
    PutDevicePropertyUserAction,
    DeleteDevicePropertyUserAction,
)

MODE = bool(os.environ.get("READ_ONLY"))

if MODE == True:
    mutation = None
else:
    mutation = Mutations

types = [
    ExcuteCommandUserAction,
    SetAttributeValueUserAction,
    PutDevicePropertyUserAction,
    DeleteDevicePropertyUserAction,
]

tangoschema = graphene.Schema(
    query=Query, mutation=mutation, subscription=Subscription, types=types
)
