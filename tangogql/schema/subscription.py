"""Module containing the Subscription implementation."""

import time
import asyncio
import taurus
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
    print(type(value))
    if isinstance(value, numpy.ndarray):
        return value.tolist()
    return value


def parse_name(name):
    *parts, attribute = name.split("/")
    device = "/".join(parts)
    return device, attribute


SLEEP_DURATION = 1.0


class Subscription(ObjectType):
    attributes = Field(AttributeFrame, full_names=List(String))

    async def resolve_attributes(self, info, full_names=[]):
        try:
            attrs = [(name, taurus.Attribute(name)) for name in full_names]
            prev_frames = {}

            while True:
                for name, attr in attrs:
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

                    prev_frame = prev_frames.get((device, attribute))
                    if frame != prev_frame:
                        yield AttributeFrame(**frame, timestamp=timestamp)

                    prev_frames[(device, attribute)] = frame

                await asyncio.sleep(SLEEP_DURATION)

        except Exception as e:
            raise
