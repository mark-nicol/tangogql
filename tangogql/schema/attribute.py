"""Module defining the attributes."""

import PyTango
from graphene import Interface, String, Int

from tangogql.schema.base import proxies
from tangogql.schema.types import TangoNodeType
from tangogql.schema.types import ScalarTypes

import asyncio


async def collaborative_read_attribute(proxy, name):
    """
    Share one attribute request for value/wvalue/timestamp/quality

    The first asyncronous read request on an attribute create a Future that
    can be used by the other read request that arrive while riding.

    The idea is to not trigger a new read_attribute request if one is
    allready running, the result can be simply shared between requestors

    TODO: Refactor me !!"""
    # Hacky way, attached two attributes to the device proxy (device proxy is
    # the element shared between requestors.). One defining if someone is
    # already waiting for value, the other one is the asynchronous
    # shared result.
    reading_attr = "{}_reading".format(name)
    value_attr = "{}_value".format(name)
    if hasattr(proxy, reading_attr) and getattr(proxy, reading_attr):
        # Someone else is already reading the attribute, wait on the future
        response = await getattr(proxy, value_attr)
        if response is not None:
            return response
        else:
            #TODO add an TangogqlException for this case.
            raise Exception(response)
    else:
        # No one is reading this attribute. Let's read it and tag that
        # this context id awaiting data
        setattr(proxy, reading_attr, True)
        # Create the shared future
        future = asyncio.Future()
        setattr(proxy, value_attr, future)
        # Wait for data
        try:
            read_value = await proxy.read_attribute(name)
            # Set data for other requestors.
            future.set_result(read_value)
            setattr(proxy, reading_attr, False)
            # Return read content
            return read_value
        except PyTango.DevFailed as error:
            read_value = None
            future.set_result(read_value)
            setattr(proxy, reading_attr, False)
            PyTango.Except.re_throw_exception(error,"","","")
        except Exception as e:
            read_value = None
            future.set_result(read_value)
            setattr(proxy, reading_attr, False)

class DeviceAttribute(Interface):
    """This class represents an attribute of a device."""

    name = String()
    device = String()
    datatype = String()
    dataformat = String()
    writable = String()
    label = String()
    unit = String()
    description = String()
    value = ScalarTypes()
    writevalue = ScalarTypes()
    quality = String()
    timestamp = Int()
    displevel= String()
    minvalue = ScalarTypes()
    maxvalue = ScalarTypes()
    minalarm = ScalarTypes()
    maxalarm = ScalarTypes()

    async def resolve_writevalue(self, *args, **kwargs):
        """This method fetch the coresponding w_value of an attribute bases on its name.

        :return: W Value of the attribute.
        :rtype: Any
        """

        w_value = None
        proxy = proxies.get(self.device)
        # Read request is an io opreration, release the event loop
        att_data = await collaborative_read_attribute(proxy, self.name)
        temp_val = att_data.w_value
        if not temp_val is None:
            if att_data.data_format != 0:  # SPECTRUM and IMAGE
                if isinstance(temp_val, tuple):
                    w_value = list(temp_val)
                else:
                    w_value = att_data.w_value.tolist()
            else:  # SCALAR
                w_value = temp_val
        return w_value

    async def resolve_value(self, *args, **kwargs):
        """This method fetch the coresponding value of an attribute bases on its name.

        :return: Value of the attribute.
        :rtype: Any
        """

        value = None
        proxy = proxies.get(self.device)
        # Read request is an io opreration, release the event loop
        att_data = await collaborative_read_attribute(proxy, self.name)
        temp_val = att_data.value
        if not temp_val is None:
            if att_data.data_format != 0:  # SPECTRUM and IMAGE
                if isinstance(temp_val, tuple):
                    value = list(temp_val)
                else:
                    value = att_data.value.tolist()
            else:  # SCALAR
                value = att_data.value
        return value

    async def resolve_quality(self, *args, **kwargs):
        """This method fetch the coresponding quality of an attribute bases on its name.

        :return: The quality of the attribute.
        :rtype: str
        """

        value = None
        # try:
        proxy = proxies.get(self.device)
        # Read request is an io operation, release the event loop
        att_data = await collaborative_read_attribute(proxy, self.name)
        value = att_data.quality.name
        # TODO: Check this part, don't do anything on an exception?
        # NOTE: Better to propagate SystemExit and KeyboardInterrupt,
        # otherwise Ctrl+C may not work.
        return value

    async def resolve_timestamp(self, *args, **kwargs):
        """This method fetch the timestamp value of an attribute bases on its name.

        :return: The timestamp value
        :rtype: float
        """

        value = None
        # try:
        proxy = proxies.get(self.device)
        # Read request is an io operation, release the event loop
        att_data = await collaborative_read_attribute(proxy, self.name)
        value = att_data.time.tv_sec
        return value


class ScalarDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass


class ImageDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass


class SpectrumDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass
