#!/usr/bin/env python3

"""A GraphQL schema for TANGO."""

import os
import graphene

from tangogql.schema.query import Query
from tangogql.schema.subscription import Subscription
from tangogql.schema.mutations import DatabaseMutations
from tangogql.schema.attribute import ScalarDeviceAttribute
from tangogql.schema.attribute import ImageDeviceAttribute
from tangogql.schema.attribute import SpectrumDeviceAttribute


MODE = bool(os.environ.get('READ_ONLY'))

if MODE == True:
    mutation=None
else:
    mutation=DatabaseMutations

tangoschema = graphene.Schema(query=Query, mutation=mutation,
                              subscription=Subscription,
                              types=[ScalarDeviceAttribute,
                                     ImageDeviceAttribute,
                                     SpectrumDeviceAttribute]
                             )
