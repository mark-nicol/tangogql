"""Module containing the Subscription implementation."""

import time
import asyncio
# import taurus
import PyTango
import numpy

from graphene import ObjectType, String, Float, Field, List, Int
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


SLEEP_DURATION = 3.0


class Subscription(ObjectType):
    attributes = Field(AttributeFrame, full_names=List(String, required=True))

    async def resolve_attributes(self, info, full_names):
        device_proxies = {}
        name_pairs = []

        for full_name in full_names:
            *parts, attribute = full_name.split("/")
            device = "/".join(parts)
            device_proxies[device] = PyTango.DeviceProxy(device)
            name_pairs.append((device, attribute))

        while True:
            try:
                for device, attribute in name_pairs:
                    try:
                        proxy = device_proxies[device]
                        read = await proxy.read_attribute(
                            attribute, extract_as=PyTango.ExtractAs.List
                        )
                    except Exception:
                        continue

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

                await asyncio.sleep(SLEEP_DURATION)

            except StopAsyncIteration:
                break
