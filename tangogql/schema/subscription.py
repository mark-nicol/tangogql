"""Module containing the Subscription implementation."""
from graphene import ObjectType, String, Float, Field, List
from tangogql.schema.types import ScalarTypes
from tangoql.base.proxies import subscriptions as subs


class AttributeFrame(ObjectType):
    attribute = String()
    device = String()
    full_name = String()
    value = ScalarTypes()
    write_value = ScalarTypes()
    quality = String()
    timestamp = Float()

    def resolve_full_name(self, info):
        return f"{self.device}/{self.attribute}"


SLEEP_DURATION = 3.0


class Subscription(ObjectType):
    attributes = Field(AttributeFrame, full_names=List(String, required=True))

    async def resolve_attributes(self, info, full_names):
        """ Setup attribute subscriibtion and return an async gen """
        async with subs.attribute_reads(full_names) as attribute_reads:
            async for evt in attribute_reads:
                read = evt.read
                sec = read.time.tv_sec
                micro = read.time.tv_usec
                timestamp = sec + micro * 1e-6
                value = read.value
                write_value = read.w_value
                quality = read.quality.name
                yield AttributeFrame(
                    device=evt.device,
                    attribute=read.name,
                    value=value,
                    write_value=write_value,
                    quality=quality,
                    timestamp=timestamp,
                )
