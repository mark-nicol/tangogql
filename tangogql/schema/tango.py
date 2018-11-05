#!/usr/bin/env python3

"""A GraphQL schema for TANGO."""

import graphene

from tangogql.schema.query import Query
from tangogql.schema.subscription import Subscription
from tangogql.schema.mutations import DatabaseMutations
from tangogql.schema.attribute import ScalarDeviceAttribute
from tangogql.schema.attribute import ImageDeviceAttribute
from tangogql.schema.attribute import SpectrumDeviceAttribute


tangoschema = graphene.Schema(query=Query, mutation=DatabaseMutations,
                              subscription=Subscription,
                              types=[ScalarDeviceAttribute,
                                     ImageDeviceAttribute,
                                     SpectrumDeviceAttribute]
                              )
