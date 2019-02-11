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


def normalize_value(value):
    if isinstance(value, numpy.ndarray):
        return value.tolist()
    return value


def parse_name(name):
    *parts, attribute = name.split("/")
    device = "/".join(parts)
    return device, attribute


SLEEP_DURATION = 1.0


class Subscription(ObjectType):
    attributes = Field(AttributeFrame, full_names=List(String, required=True))

    async def resolve_attributes(self, info, full_names):
        try:
            attrs = [(taurus.Attribute(name), name) for name in full_names]
            prev_frames = {}
            first_round = True

            while True:
                for attr, name in attrs:
                    # Only emit the first value unless the attribute is a scalar one, until
                    # the performance issue of continuously transmitting spectrum and
                    # image data in JSON has been addressed.
                    if not first_round:
                        if attr.getDataFormat() != PyTango.AttrDataFormat.SCALAR:
                            continue

                    try:
                        read = attr.read()
                    except Exception:
                        continue

                    value = normalize_value(read.value)
                    write_value = normalize_value(read.w_value)
                    quality = read.quality.name

                    sec = read.time.tv_sec
                    micro = read.time.tv_usec
                    timestamp = sec + micro * 1e-6

                    device, attribute = parse_name(name)
                    frame = dict(
                        device=device,
                        attribute=attribute,
                        value=value,
                        write_value=write_value,
                        quality=quality,
                    )

                    key = (device, attribute)
                    prev_frame = prev_frames.get(key)
                    if frame != prev_frame:
                        yield AttributeFrame(**frame, timestamp=timestamp)

                    prev_frames[key] = frame

                first_round = False
                await asyncio.sleep(SLEEP_DURATION)

        finally:
            for attr in attrs:
                attr.cleanUp()
