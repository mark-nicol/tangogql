"""Module defining the attributes."""

import PyTango
from graphene import String, Float, ObjectType
import asyncio

from tangogql.schema.base import proxies
from tangogql.schema.types import ScalarTypes, TypeConverter

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
            read_value = await proxy.read_attribute(name, extract_as=PyTango.ExtractAs.List)
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


class DeviceAttribute(ObjectType):
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
    timestamp = Float()
    displevel= String()
    minvalue = ScalarTypes()
    maxvalue = ScalarTypes()
    minalarm = ScalarTypes()
    maxalarm = ScalarTypes()

    _attr_read = None
    _attr_info = None

    async def resolve_writevalue(self, *args, **kwargs):
        """This method fetch the coresponding w_value of an attribute bases on its name.

        :return: W Value of the attribute.
        :rtype: Any
        """

        read = await self._get_attr_read()
        return read.w_value

    async def resolve_value(self, *args, **kwargs):
        """This method fetch the coresponding value of an attribute bases on its name.

        :return: Value of the attribute.
        :rtype: Any
        """

        read = await self._get_attr_read()
        return read.value

    async def resolve_quality(self, *args, **kwargs):
        """This method fetch the coresponding quality of an attribute bases on its name.

        :return: The quality of the attribute.
        :rtype: str
        """

        read = await self._get_attr_read()
        return read.quality.name

    async def resolve_timestamp(self, *args, **kwargs):
        """This method fetch the timestamp value of an attribute bases on its name.

        :return: The timestamp value
        :rtype: float
        """

        read = await self._get_attr_read()
        sec = read.time.tv_sec
        usec = read.time.tv_usec
        return sec + usec * 1e-6

    def resolve_dataformat(self, info):
        return self._get_attr_info().data_format

    def resolve_label(self, info):
        return self._get_attr_info().label

    def resolve_unit(self, info):
        return self._get_attr_info().unit

    def resolve_description(self, info):
        return self._get_attr_info().description

    def resolve_displevel(self, info):
        return self._get_attr_info().disp_level

    def resolve_writable(self, info):
        return str(self._get_attr_info().writable)

    def resolve_datatype(self, info):
        return self._get_datatype()

    def resolve_minvalue(self, info):
        return self._convert_value("min_value")

    def resolve_maxvalue(self, info):
        return self._convert_value("max_value")

    def resolve_minalarm(self, info):
        return self._convert_value("min_alarm")

    def resolve_maxalarm(self, info):
        return self._convert_value("max_alarm")

    async def _get_attr_read(self):
        if self._attr_read is None:
            proxy = proxies.get(self.device)
            read_coro = proxy.read_attribute(self.name, extract_as=PyTango.ExtractAs.List)
            self._attr_read = asyncio.ensure_future(read_coro)
        return await self._attr_read

    def _get_attr_info(self):
        proxy = proxies.get(self.device)
        return proxy.attribute_query(self.name)

    def _get_datatype(self):
        return PyTango.CmdArgType.values[self._get_attr_info().data_type]

    def _convert_value(self, key):
        attr_info = self._get_attr_info()
        value = getattr(attr_info, key)

        if value == "Not specified":
            return None
        else:
            datatype = self._get_datatype()
            return TypeConverter.convert(datatype, value)
