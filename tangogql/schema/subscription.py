"""Module containing the Subscription implementation."""

import time
import asyncio
import taurus
import PyTango
import numpy


from graphene import ObjectType, String, Float, Interface, Field, List, Int
from tangogql.schema.types import ScalarTypes


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


SLEEP_DURATION = 1.0
GREEN_MODE = PyTango.GreenMode.Asyncio


class Subscription(ObjectType):
    attributes = Field(AttributeFrame, full_names=List(String, required=True))

    async def resolve_attributes(self, info, full_names):
        device_proxies = {}
        attributes = []
        ignore = []

        for full_name in full_names:
            *parts, attribute = full_name.split("/")
            device = "/".join(parts)
            device_proxies[device] = PyTango.DeviceProxy(device, green_mode=GREEN_MODE)
            attributes.append((device, attribute))

        while True:
            for i, (device, attribute) in enumerate(attributes):
                # Skip attributes that have been ignored due to their data format (see
                # comment below)
                if i in ignore:
                    continue

                try:
                    proxy = device_proxies[device]
                    read = await asyncio.shield(
                        proxy.read_attribute(
                            attribute, extract_as=PyTango.ExtractAs.List
                        )
                    )
                except Exception:
                    continue

                # Ignore attributes that aren't scalar after the first read, until
                # the performance issue of continuously transmitting spectrum and
                # image data in JSON has been addressed.
                if read.data_format != PyTango.AttrDataFormat.SCALAR:
                    ignore.append(i)

                sec = read.time.tv_sec
                micro = read.time.tv_usec
                timestamp = sec + micro * 1e-6

                value = read.value
                write_value = read.w_value
                quality = read.quality.name

                yield AttributeFrame(
                    device=device,
                    attribute=attribute,
                    value=value,
                    write_value=write_value,
                    quality=quality,
                    timestamp=timestamp,
                )

                await asyncio.shield(asyncio.sleep(SLEEP_DURATION))
