#!/usr/bin/env python3

"""A GraphQL schema for TANGO."""

import math
import fnmatch
import re
from operator import attrgetter
import json

import asyncio
from collections import defaultdict
import time

import PyTango

import graphene
from graphene import (Boolean, Field, Float, Int, Interface, List, Mutation,
                      ObjectType, String, Union, Scalar, Dynamic)
# TODO: check which Scalar is the one to be used and remove the other.
from graphene.types import Scalar
from graphql.language import ast

from tangogql.listener import TaurusWebAttribute
from tangogql.tangodb import CachedDatabase, DeviceProxyCache


db = CachedDatabase(ttl=10)
proxies = DeviceProxyCache()


class TangoNodeType(ObjectType):
    """This class represents type of a node in Tango."""

    nodetype = String()

    def resolve_nodetype(self, info):
        """This method gets the type of the node in Tango.

        :return: Name of the type.
        :rtype: str
        """

        return type(self).__name__.lower()


class DeviceProperty(TangoNodeType, Interface):
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


class ScalarTypes(Scalar):
    """
    This class makes it possible to have input and output of different types.

    The ScalarTypes represents a generic scalar value that could be:
    Int, String, Boolean, Float, List.
    """

    @staticmethod
    def coerce_type(value):
        """This method just return the input value.

        :param value: Any

        :return: Value (any)
        """

        # value of type DevState should return as string
        if type(value).__name__ == "DevState":
            return str(value)
        # json don't have support on infinity
        elif isinstance(value, float):
            if math.isinf(value):
                return str(value)
        return value

    # TODO: Check if the following static methods really need to be static.
    @staticmethod
    def serialize(value):
        return ScalarTypes.coerce_type(value)

    @staticmethod
    def parse_value(value):
        """This method is called when an assignment is made.

        :param value: value(any)

        :return: value(any)
        """

        return ScalarTypes.coerce_type(value)

    # Called for the input
    @staticmethod
    def parse_literal(node):
        """This method is called when the value of type *ScalarTypes* is used
        as input.

        :param node: value(any)

        :return: Return an exception when it is not possible to parse the value
                 to one of the scalar types.
        :rtype: bool, str, int, float or Exception
        """

        try:
            if isinstance(node, ast.IntValue):
                return int(node.value)
            elif isinstance(node, ast.FloatValue):
                return float(node.value)
            elif isinstance(node, ast.BooleanValue):
                return node.value
            elif isinstance(node, ast.ListValue):
                return [ScalarTypes.parse_literal(value)
                        for value in node.values]
            elif isinstance(node, ast.StringValue):
                return str(node.value)
            else:
                raise ValueError('The input value is not of acceptable types')
        except Exception as e:
            return e


class ExecuteDeviceCommand(Mutation):
    """This class represent a mutation for executing a command."""

    class Arguments:
        device = String(required=True)
        command = String(required=True)
        argin = ScalarTypes()

    ok = Boolean()
    message = List(String)
    output = ScalarTypes()

    def mutate(self, info, device, command, argin=None):
        """ This method executes a command.

        :param device: Name of the device that the command will be executed.
        :type device: str

        :param command: Name of the command
        :type command: str

        :param argin: The input argument for the command
        :type argin: str or int or bool or float

        :return: Return ok = True and message = Success
                 if the command executes successfully, False otherwise.
                 When an input is not one of the scalar types or an exception
                 has been raised while executing the command, it returns
                 message = error_message.
        :rtype: ExecuteDeviceCommand
        """

        if type(argin) is ValueError:
            return ExecuteDeviceCommand(ok=False, message=[str(argin)])
        try:
            proxy = proxies.get(device)
            result = proxy.command_inout(command, argin)
            return ExecuteDeviceCommand(ok=True,
                                        message=["Success"],
                                        output=result)
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return ExecuteDeviceCommand(ok=False, message=[e.desc, e.reason])
        except Exception as e:
            return ExecuteDeviceCommand(ok=False, message=[str(e)])


class SetAttributeValue(Mutation):
    """This class represents the mutation for setting value to an attribute."""

    class Arguments:
        device = String(required=True)
        name = String(required=True)
        value = ScalarTypes(required=True)

    ok = Boolean()
    message = List(String)

    def mutate(self, info, device, name, value):
        """ This method sets value to an attribute.

        :param device: Name of the device
        :type device: str

        :param name: Name of the attribute
        :type name: str
        :param value: The value to be set
        :type value: int, str, bool or float

        :return: Return ok = True and message = Success if successful,
                 False otherwise.
                 When an input is not one the scalar types or an exception has
                 been raised while setting the value returns 
                 message = error_message.
        :rtype: SetAttributeValue
        """

        if type(value) is ValueError:
            return SetAttributeValue(ok=False, message=[str(value)])
        try:
            proxy = proxies.get(device)
            proxy.write_attribute(name, value)
            return SetAttributeValue(ok=True, message=["Success"])
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return SetAttributeValue(ok=False, message=[e.desc, e.reason])
        except Exception as e:
            return SetAttributeValue(ok=False, message=[str(e)])


class PutDeviceProperty(Mutation):
    """This class represents mutation for putting a device property."""

    class Arguments:
        device = String(required=True)
        name = String(required=True)
        value = List(String)
        # async = Boolean()

    ok = Boolean()
    message = List(String)

    def mutate(self, info, device, name, value=""):
        """ This method adds property to a device.

        :param device: Name of a device
        :type device: str
        :param name: Name of the property
        :type name: str
        :param value: Value of the property
        :type value: str

        :return: Returns ok = True and message = Success if successful,
                 False otherwise.
                 If an exception has been raised returns 
                 message = error_message.
        :rtype: PutDeviceProperty
        """

        # wait = not args.get("async")
        try:
            db.put_device_property(device, {name: value})
            return PutDeviceProperty(ok=True, message=["Success"])
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return SetAttributeValue(ok=False, message=[e.desc, e.reason])
        except Exception as e:
            return SetAttributeValue(ok=False, message=[str(e)])


class DeleteDeviceProperty(Mutation):
    """This class represents mutation for deleting property of a device."""

    class Arguments:
        device = String(required=True)
        name = String(required=True)
    ok = Boolean()
    message = List(String)

    def mutate(self, info, device, name):
        """This method delete a property of a device.

        :param device: Name of the device
        :type device: str
        :param name: Name of the property
        :type name: str

        :return: Returns ok = True and message = Success if successful,
                 ok = False otherwise.
                 If exception has been raised returns message = error_message.
        :rtype: DeleteDeviceProperty
        """

        try:
            db.delete_device_property(device, name)
            return DeleteDeviceProperty(ok=True, message=["Success"])
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return DeleteDeviceProperty(ok=False, message=[e.desc, e.reason])
        except Exception as e:
            return DeleteDeviceProperty(ok=False, message=[str(e)])


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
    quality = String()
    timestamp = Int()

    def resolve_value(self, *args, **kwargs):
        """This method fetch the coresponding value of an attribute bases on its name.

        :return: Value of the attribute.
        :rtype: Any
        """

        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            if att_data.data_format != 0:  # SPECTRUM and IMAGE
                temp_val = att_data.value
                if isinstance(temp_val, tuple):
                    value = list(temp_val)
                else:
                    value = att_data.value.tolist()
            else:  # SCALAR
                    value = att_data.value
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return [e.desc, e.reason]
        except Exception as e:
            return str(e)
        return value

    def resolve_quality(self, *args, **kwargs):
        """This method fetch the coresponding quality of an attribute bases on its name.

        :return: The quality of the attribute.
        :rtype: str
        """

        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            value = att_data.quality.name
        # TODO: Check this part, don't do anything on an exception?
        # NOTE: Better to propagate SystemExit and KeyboardInterrupt,
        # otherwise Ctrl+C may not work.
        except Exception as e:
            pass
        return value

    def resolve_timestamp(self, *args, **kwargs):
        """This method fetch the timestamp value of an attribute bases on its name.

        :return: The timestamp value
        :rtype: float
        """

        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            value = att_data.time.tv_sec
        except Exception as e:
            pass
        return value


class ScalarDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass


class ImageDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass


class SpectrumDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass


class DeviceCommand(TangoNodeType, Interface):
    """This class represents an command and its properties."""

    name = String()
    tag = Int()
    displevel = String()
    intype = String()
    intypedesc = String()
    outtype = String()
    outtypedesc = String()


class DeviceInfo(TangoNodeType, Interface):
    """ This class represents info of a device.  """

    id = String()       # server id
    host = String()     # server host


class Device(TangoNodeType, Interface):
    """This class represent a device."""

    name = String()
    state = String()
    properties = List(DeviceProperty, pattern=String())
    attributes = List(DeviceAttribute, pattern=String())
    commands = List(DeviceCommand, pattern=String())
    server = List(DeviceInfo)

    # device_class = String()
    # server = String()
    pid = Int()
    started_date = String()
    stopped_date = String()
    exported = Boolean()

    def resolve_state(self, info):
        """This method fetch the state of the device.

        :return: State of the device.
        :rtype: str
        """
        try:
            proxy = proxies.get(self.name)
            return proxy.state()
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

        props = db.get_device_property_list(self.name, pattern)
        return [DeviceProperty(name=p, device=self.name) for p in props]

    def resolve_attributes(self, info, pattern="*"):
        """This method fetch all the attributes and its' properties of a device.

        :param pattern: Pattern for filtering the result.
                        Returns only properties that match the pattern.
        :type pattern: str

        :return: List of attributes of the device.
        :rtype: List of DeviceAttribute
        """

        proxy = proxies.get(self.name)
        attr_infos = proxy.attribute_list_query()
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        sorted_info = sorted(attr_infos, key=attrgetter("name"))
        result = []

        # TODO: Ensure that result is passed properly, refresh mutable
        #       arguments copy or pointer ...? Tests are passing ...
        def append_to_result(result, klass, attr_info):
            result.append(klass(
                          name=attr_info.name,
                          device=self.name,
                          writable=attr_info.writable,
                          datatype=PyTango.CmdArgType.values[
                                   attr_info.data_type],
                          dataformat=attr_info.data_format,
                          label=attr_info.label,
                          unit=attr_info.unit,
                          description=attr_info.description)
                          )

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

    def resolve_commands(self, info, pattern="*"):
        """This method fetch all the commands of a device.

        :param pattern: Pattern for filtering of the result.
                        Returns only commands that match the pattern.
        :type pattern: str

        :return: List of commands of the device.
        :rtype: List of DeviceCommand
        """

        proxy = proxies.get(self.name)
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

    def resolve_server(self, info):
        """ This method fetch the server infomation of a device.

        :return: List server info of a device.
        :rtype: List of DeviceInfo
        """

        proxy = proxies.get(self.name)
        dev_info = proxy.info()

        return [DeviceInfo(id=dev_info.server_id,
                           host=dev_info.server_host)]

    def resolve_exported(self, info):
        """ This method fetch the infomation about the device if it is exported or not.

        :return: True if exported, False otherwise.
        :rtype: bool
        """

        return self.info.exported

    def resolve_pid(self, info):
        return self.info.pid

    def resolve_started_date(self, info):
        return self.info.started_date

    def resolve_stopped_date(self, info):
        return self.info.stopped_date

    @property
    def info(self):
        """This method fetch all the information of a device."""

        if not hasattr(self, "_info"):
            self._info = db.get_device_info(self.name)
        return self._info


class Member(Device):
    """This class represent a member."""

    domain = String()
    family = String()

    @property
    def info(self):
        """This method fetch a member of the device using the name of the
        domain and family.
        """

        if not hasattr(self, "_info"):
            # NOTE: If we want to keep it compatible with python versions lower 
            #       than python 3.6, then use format ... buuuuuutttt,
            #       let's have some fun with the new f-strings
            devicename = f"{self.domain}/{self.family}/{self.name}"
            self._info = db.get_device_info(devicename)
        return self._info


class Family(TangoNodeType, Interface):
    """This class represent a family."""

    name = String()
    domain = String()
    members = List(Member, pattern=String())

    def resolve_members(self, info, pattern="*"):
        """This method fetch members using the name of the domain and pattern.

        :param pattern: Pattern for filtering of the result.
                        Returns only members that match the pattern.
        :type pattern: str

        :return: List of members.
        :rtype: List of Member
        """

        members = db.get_device_member(f"{self.domain}/{self.name}/{pattern}")
        return [Member(domain=self.domain, family=self.name, name=member)
                for member in members]


class Domain(TangoNodeType, Interface):
    """This class represent a domain."""

    name = String()
    families = List(Family, pattern=String())

    def resolve_families(self, info, pattern="*"):
        """This method fetch a list of families using pattern.

        :param pattern: Pattern for filtering of the result.
                        Returns only families that match the pattern.
        :type pattern: str

        :return:
            families([Family]):List of families.
        """

        families = db.get_device_family(f"{self.name}/{pattern}/*")
        return [Family(name=family, domain=self.name) for family in families]


class DeviceClass(TangoNodeType, Interface):

    name = String()
    server = String()
    instance = String()
    devices = List(Device)


# TODO: Missing documentation
class ServerInstance(TangoNodeType, Interface):
    """Not documented yet."""

    name = String()
    server = String()
    classes = List(DeviceClass, pattern=String())

    def resolve_classes(self, info, pattern="*"):
        devs_clss = db.get_device_class_list(f"{self.server}/{self.name}")
        mapping = defaultdict(list)
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)

        for device, clss in zip(devs_clss[::2], devs_clss[1::2]):
            mapping[clss].append(Device(name=device))

        return [DeviceClass(name=clss, server=self.server,
                            instance=self.name, devices=devices)
                for clss, devices in mapping.items()
                if rule.match(clss)]


class Server(TangoNodeType, Interface):
    """This class represents a query for server."""

    name = String()
    instances = List(ServerInstance, pattern=String())

    def resolve_instances(self, info, pattern="*"):
        """ This method fetches all the intances using pattern.

        :param pattern: Pattern for filtering the result.
                        Returns only properties that matches the pattern.
        :type pattern: str

        :return: List of intances.
        :rtype: List of ServerIntance
        """

        instances = db.get_instance_name_list(self.name)
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [ServerInstance(name=inst, server=self.name)
                for inst in instances if rule.match(inst)]


class Query(ObjectType):
    """This class contains all the queries."""

    devices = List(Device, pattern=String())
    domains = List(Domain, pattern=String())
    families = List(Family, domain=String(), pattern=String())
    members = List(Member, domain=String(), family=String(), pattern=String())

    servers = List(Server, pattern=String())
    instances = List(ServerInstance, server=String(), pattern=String())
    classes = List(DeviceClass, pattern=String())

    def resolve_devices(self, info, pattern="*"):
        """ This method fetches all the devices using the pattern.

        :param pattern: Pattern for filtering the result.
                        Returns only properties that matches the pattern.
        :type pattern: str

        :return: List of devices.
        :rtype: List of Device    
        """
        devices = db.get_device_exported(pattern)
        return [Device(name=d) for d in sorted(devices)]

    def resolve_domains(self, info, pattern="*"):
        """This method fetches all the domains using the pattern.

        :param pattern: Pattern for filtering the result.
                        Returns only properties that matches the pattern.
        :type pattern: str

        :return: List of domains.
        :rtype: List of Domain
        """
        domains = db.get_device_domain("%s/*" % pattern)
        return [Domain(name=d) for d in sorted(domains)]

    def resolve_families(self, info, domain="*", pattern="*"):
        """This method fetches all the families using the pattern.

        :param domain: Domain for filtering the result.
        :type domain: str

        :param pattern: Pattern for filtering the result.
                        Returns only properties that matches the pattern.
        :type pattern: str

        :return: List of families.
        :rtype: List of Family
        """

        families = db.get_device_family(f"{domain}/{pattern}/*")
        return [Family(domain=domain, name=d) for d in sorted(families)]

    def resolve_members(self, info, domain="*", family="*", pattern="*"):
        """This method fetches all the members using the pattern.

        :param domain: Domain for filtering the result.
        :type domain: str

        :param family: Family for filtering the result.
        :type family: str

        :param pattern: Pattern for filtering the result.
                        Returns only properties that matches the pattern.
        :type pattern: str

        :return: List of members.
        :rtype: List of Domain
        """

        members = db.get_device_member(f"{domain}/{family}/{pattern}")
        return [Member(domain=domain, family=family, name=member)
                for member in sorted(members)]

    def resolve_servers(self, info, pattern="*"):
        """ This method fetches all the servers using the pattern.

        :param pattern: Pattern for filtering the result.
                        Returns only properties that matches the pattern.
        :type pattern: str

        :return: List of servers.
        :rtype: List of Server.
        """

        servers = db.get_server_name_list()
        # The db service does not allow wildcard here, but it can still
        # useful to limit the number of children. Let's fake it!
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [Server(name=srv) for srv in sorted(servers) if rule.match(srv)]


class DatabaseMutations(ObjectType):
    """This class contains all the mutations."""

    put_device_property = PutDeviceProperty.Field()
    delete_device_property = DeleteDeviceProperty.Field()
    setAttributeValue = SetAttributeValue.Field()
    execute_command = ExecuteDeviceCommand.Field()


class ChangeData(ObjectType):
    value = ScalarTypes()
    w_value = ScalarTypes()
    quality = String()
    time = Float()


class ConfigData(ObjectType):
    description = String()
    label = String()
    unit = String()
    format = String()
    data_format = String()
    data_type = String()


class Event(Interface):
    event_type = String()
    device = String()
    name = String()


class ChangeEvent(ObjectType, interfaces=[Event]):
    data = Field(ChangeData)


class ConfigEvent(ObjectType, interfaces=[Event]):
    data = Field(ConfigData)


# NOTE: Maybe we should agree on having the constants in capitals
# Contains subscribed attributes
change_listeners = {}
config_listeners = {}


class Subscription(ObjectType):
    change_event = List(ChangeEvent, models=List(String))
    config_event = List(ConfigEvent, models=List(String))
    unsub_config_event = String(models=List(String))
    unsub_change_event = String(models=List(String))

    # TODO: documentation missing
    async def resolve_change_event(self, info, models=[]):

        keeper = EventKeeper()
        for attr in models:
            taurus_attr = TaurusWebAttribute(attr, keeper)
            change_listeners[attr] = taurus_attr

        while change_listeners:
            evt_list = []
            events = keeper.get()
            for event_type, data in events.items():
                for attr_name, value in data.items():
                    device, attr = attr_name.rsplit('/', 1)
                    if event_type == "CHANGE":
                        data = ChangeData(value=value['value'],
                                          w_value=value['w_value'],
                                          quality=value['quality'],
                                          time=value['time'])
                        event = ChangeEvent(event_type=event_type, 
                                            device=device,
                                            name=attr,
                                            data=data)
                        evt_list.append(event)
            if evt_list:
                yield evt_list
            await asyncio.sleep(1.0)

    async def resolve_config_event(self, info, models=[]):
        keeper = EventKeeper()
        for attr in models:
            taurus_attr = TaurusWebAttribute(attr, keeper)
            config_listeners[attr] = taurus_attr

        while config_listeners:
            evt_list = []
            events = keeper.get()
            for event_type, data in events.items():
                for attr_name, value in data.items():
                    device, attr = attr_name.rsplit('/', 1)
                    if event_type == "CONFIG":
                        data = ConfigData(description=value['description'],
                                          label=value['label'],
                                          unit=value['unit'],
                                          format=value['format'],
                                          data_format=value['data_format'],
                                          data_type=value['data_type']    
                                    )
                        event = ConfigEvent(event_type=event_type,
                                            device=device,
                                            name=attr,
                                            data=data)
                        evt_list.append(event)
            if evt_list:
                yield evt_list
            await asyncio.sleep(1.0)

    # TODO: documentation missing
    async def resolve_unsub_change_event(self, info, models=[]):
        result = []
        if change_listeners:
            for attr in models:
                listener = change_listeners[attr]
                if listener:
                    listener.clear()
                    del change_listeners[attr]
                    result.append(attr)
            yield f"Unsubscribed: {result}"
        else:
            yield "No attribute to unsubscribe"

    async def resolve_unsub_config_event(self, info, models=[]):
        result = []
        if config_listeners:
            for attr in models:
                listener = config_listeners[attr]
                if listener:
                    listener.clear()
                    del config_listeners[attr]
                    result.append(attr)
            yield f"Unsubscribed: {result}"
        else:
            yield "No attribute to unsubscribe"


# Help class
class EventKeeper:
    """A simple wrapper that keeps the latest event values for
    each attribute."""

    def __init__(self):
        self._events = defaultdict(dict)
        self._timestamps = defaultdict(dict)
        self._latest = defaultdict(dict)

    def put(self, model, action, value):
        """Update a model"""
        self._events[action][model] = value
        self._timestamps[action][model] = time.time()

    def get(self):
        """Returns the latest accumulated events"""
        tmp, self._events = self._events, defaultdict(dict)
        for event_type, events in tmp.items():
            self._latest[event_type].update(events)
        return tmp


tangoschema = graphene.Schema(query=Query, mutation=DatabaseMutations,
                              subscription=Subscription,
                              types=[ScalarDeviceAttribute,
                                     ImageDeviceAttribute,
                                     SpectrumDeviceAttribute]
                              )
