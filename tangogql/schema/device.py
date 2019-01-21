"""Device Schema."""

import re
import fnmatch
import PyTango
from operator import attrgetter
from graphene import Interface, String, Int, List, Boolean, Field, ObjectType
from tangogql.schema.base import db, proxies
from tangogql.schema.types import TypeConverter
from tangogql.schema.attribute import DeviceAttribute
from tangogql.schema.attribute import ScalarDeviceAttribute
from tangogql.schema.attribute import ImageDeviceAttribute
from tangogql.schema.attribute import SpectrumDeviceAttribute

class DeviceProperty(ObjectType, Interface):
    """ This class represents a property of a device.  """

    name = String()
    device = String()
    value = List(String)

    def resolve_value(self, info):
        """ This method fetch the value of the property by its name.

        :return: A list of string contains the values corespond to the name of
                 the property.
        :rtype: str
        """

        device = self.device
        name = self.name
        value = db.get_device_property(device, name)
        if value:
            return [line for line in value[name]]


class DeviceCommand(ObjectType, Interface):
    """This class represents an command and its properties."""

    name = String()
    tag = Int()
    displevel = String()
    intype = String()
    intypedesc = String()
    outtype = String()
    outtypedesc = String()


class DeviceInfo(ObjectType, Interface):
    """ This class represents info of a device.  """

    id = String()       # server id
    host = String()     # server host


class Device(ObjectType, Interface):
    """This class represent a device."""

    name = String()
    state = String()
    connected = Boolean()
    properties = List(DeviceProperty, pattern=String())
    attributes = List(DeviceAttribute, pattern=String())
    commands = List(DeviceCommand, pattern=String())
    server = Field(DeviceInfo)
    
    # device_class = String()
    # server = String()
    pid = Int()
    started_date = String()
    stopped_date = String()
    exported = Boolean()

    async def resolve_state(self, info):
        """This method fetch the state of the device.

        :return: State of the device.
        :rtype: str
        """
        try:
            proxy = self._get_proxy()
            return await proxy.state()
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked):
            return "UNKNOWN"
        except Exception as e:
            return str(e)

    def resolve_properties(self, info, pattern="*"):
        """This method fetch the properties of the device.

        :param pattern: Pattern for filtering the result.
                        Returns only properties that matches the pattern.
        :type pattern: str

        :return: List of properties for the device.
        :rtype: List of DeviceProperty
        """
        #TODO:Db calls are not asynchronous in tango
        props = db.get_device_property_list(self.name, pattern)
        return [DeviceProperty(name=p, device=self.name) for p in props]

    async def resolve_attributes(self, info, pattern="*"):
        """This method fetch all the attributes and its' properties of a device.

        :param pattern: Pattern for filtering the result.
                        Returns only properties that match the pattern.
        :type pattern: str

        :return: List of attributes of the device.
        :rtype: List of DeviceAttribute
        """ 
        # TODO: Ensure that result is passed properly, refresh mutable
        #       arguments copy or pointer ...? Tests are passing ...
        def append_to_result(result, klass, attr_info):
            if attr_info.writable == PyTango._tango.AttrWriteType.WT_UNKNOWN:
                wt = 'READ_WITH_WRITE'
            else:
                wt = attr_info.writable
            
            data_type = PyTango.CmdArgType.values[attr_info.data_type]
            
            result.append(klass(
                          name=attr_info.name,
                          device=self.name,
                          writable=wt,
                          datatype=data_type,
                          dataformat=attr_info.data_format,
                          label=attr_info.label,
                          unit=attr_info.unit,
                          description=attr_info.description,
                          displevel=attr_info.disp_level,
                          minvalue=None if attr_info.min_value  == "Not specified" else TypeConverter.convert(data_type,attr_info.min_value),
                          maxvalue=None if attr_info.max_value  == "Not specified" else TypeConverter.convert(data_type,attr_info.max_value),
                          minalarm=None if attr_info.min_alarm  == "Not specified" else TypeConverter.convert(data_type,attr_info.min_alarm),
                          maxalarm=None if attr_info.max_alarm  == "Not specified" else TypeConverter.convert(data_type,attr_info.max_alarm)
                          )
                          )
        result = []
        if await self._get_connected():
            proxy = self._get_proxy()
            attr_infos = proxy.attribute_list_query()

            rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
            sorted_info = sorted(attr_infos, key=attrgetter("name"))
            for attr_info in sorted_info:
                if rule.match(attr_info.name):
                    if str(attr_info.data_format) == "SCALAR":
                        append_to_result(result,
                                        ScalarDeviceAttribute, attr_info)

                    if str(attr_info.data_format) == "SPECTRUM":
                        append_to_result(result,
                                        SpectrumDeviceAttribute, attr_info)

                    if str(attr_info.data_format) == "IMAGE":
                        append_to_result(result,
                                        ImageDeviceAttribute, attr_info)
        return result

    async def resolve_commands(self, info, pattern="*"):
        """This method fetch all the commands of a device.

        :param pattern: Pattern for filtering of the result.
                        Returns only commands that match the pattern.
        :type pattern: str

        :return: List of commands of the device.
        :rtype: List of DeviceCommand
        """
        if await self._get_connected():
            proxy = self._get_proxy()
            cmd_infos = proxy.command_list_query()
            rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)

            def create_device_command(cmd_info):
                return DeviceCommand(name=cmd_info.cmd_name,
                                    tag=cmd_info.cmd_tag,
                                    displevel=cmd_info.disp_level,
                                    intype=cmd_info.in_type,
                                    intypedesc=cmd_info.in_type_desc,
                                    outtype=cmd_info.out_type,
                                    outtypedesc=cmd_info.out_type_desc
                                    )

            return [create_device_command(a)
                    for a in sorted(cmd_infos, key=attrgetter("cmd_name"))
                    if rule.match(a.cmd_name)]
        else:
            return []

    async def resolve_server(self, info):
        """ This method fetch the server infomation of a device.

        :return: List server info of a device.
        :rtype: List of DeviceInfo
        """
        if await self._get_connected():
            proxy = self._get_proxy()
            dev_info = proxy.info()
            return DeviceInfo(id=dev_info.server_id,
                            host=dev_info.server_host)
            
    def resolve_exported(self, info):
        """ This method fetch the infomation about the device if it is exported or not.

        :return: True if exported, False otherwise.
        :rtype: bool
        """

        return self._get_info().exported

    def resolve_pid(self, info):
        return self._get_info().pid

    def resolve_started_date(self, info):
        return self._get_info().started_date

    def resolve_stopped_date(self, info):
        return self._get_info().stopped_date

    async def resolve_connected(self, info):
        return await self._get_connected()

    def _get_proxy(self):
        if not hasattr(self, "_proxy"):
            self._proxy = proxies.get(self.name)
        return self._proxy

    async def _get_connected(self):
        if not hasattr(self, "_connected"):
            try:
                proxy = self._get_proxy()
                await proxy.state()
                self._connected = True
            except (PyTango.DevFailed, PyTango.ConnectionFailed):
                self._connected = False
        return self._connected


    def _get_info(self):
        """This method fetch all the information of a device."""

        if not hasattr(self, "_info"):
            self._info = db.get_device_info(self.name)
        return self._info
