"""A GraphQL schema for TANGO."""

import fnmatch
import re
from collections import defaultdict
from operator import attrgetter
import json
import PyTango
import graphene
from graphene import (Boolean, Field, Float, Int, Interface, List, Mutation,
                      ObjectType, String, Union,Scalar,Dynamic)
from tangodb import CachedDatabase, DeviceProxyCache
from graphene.types import Scalar
from graphql.language import ast
import asyncio
from collections import OrderedDict
from collections import defaultdict
import time
from listener import TaurusWebAttribute
#from directives import GraphQLUnlessDirective

db = CachedDatabase(ttl=10)
proxies = DeviceProxyCache()



class TangoSomething(ObjectType):
    """ This class represents type of a node in Tango. """

    nodetype = String()

    def resolve_nodetype(self, info):
        """ This method gets the type of the node in Tango. 
        
        Returns:
            name(str): Name of the type.
        
        """

        return type(self).__name__.lower()

class DeviceProperty(TangoSomething, Interface):
    """ This class represents property of a device.  """

    name = String()
    device = String()
    value = List(String)

    def resolve_value(self, info):
        """ This method fetch the value of the property by its name.
            
        Returns:
            values[str]: A list of string contains the values corespond to the name of the property. 
        
        """

        device = self.device
        name = self.name
        value = db.get_device_property(device, name)
        if value:
            return [line for line in value[name]]

# This class make it possible to have input and out of multiples different types
class ScalarTypes(Scalar):
    """ The ScalarTypes represents a geneneric scalar value that could be:
    Int, String, Boolean, Float, List. """
    
    @staticmethod
    def coerce_type(value):
        """ This method just return the input value.
        
        Args:
            value(any)
        
        returns:
            value(any)  
        
        """
        
        #value of type DevState should return as string 
        if type(value).__name__ == "DevState":
            return str(value)
        return value
    @staticmethod
    def serialize(value):
        return ScalarTypes.coerce_type(value)
    @staticmethod
    def parse_value(value):
        """ This method is called when an assigment is made.
        
        Args:
            value(any)
        
        Returns:
            value(any) 
        
        """
        
        return ScalarTypes.coerce_type(value)
    #Called for the input
    @staticmethod
    def parse_literal(node):
        """ This method is called when the value of type *ScalarTypes* is used as input.
        
        Args:
            value(any)
        
        Returns:
            value(bool or str or int or float or Exception): Return exception when it is not possible to parse the value 
            to one of the scalar types. 
        
        """
        
        try:
            if isinstance(node, ast.IntValue):
                return int(node.value)
            elif isinstance(node,ast.FloatValue):
                return float(node.value)
            elif isinstance(node, ast.BooleanValue):
                return node.value
            elif isinstance(node, ast.ListValue):
                return [ScalarTypes.parse_literal(value) for value in node.values]
            elif isinstance(node,ast.StringValue):
                return str(node.value)
            else:
                raise ValueError('The input value is not of acceptable types')
        except Exception as e:
            return e

class ExecuteDeviceCommand(Mutation):
    """ This class represent a mutation for executing a command. """

    class Arguments:
        device = String(required = True)
        command = String(required = True)
        argin = ScalarTypes()

    ok = Boolean()
    message = List(String)
    output = ScalarTypes()

    def mutate(self, info, device, command,argin):
        """ This method executes a command.
        
        Args:
            device(str): Name of the device that the command will be executed.
            
            command(str): Name of the command.
            
            argin(str or int or bool or float): The input argument for the command.
        
        Returns:
            value(ExecuteDeviceCommand): Return ok = True and message = Success 
            if the command executes successfully,
            False otherwise. When an input is not one of the scalar types 
            or an exception has been raised while executing the command, it 
            returns message = error_message.
        
        """

    def mutate(self, info, device, command,argin = None):
        if type(argin) is ValueError:
            return ExecuteDeviceCommand(ok= False, message = [str(argin)])
        try:
            proxy = proxies.get(device)
            result = proxy.command_inout(command,argin)
            return ExecuteDeviceCommand(ok = True, message = ["Success"], output = result)
        except PyTango.DevFailed or PyTango.ConnectionFailed or PyTango.CommunicationFailed or PyTango.DeviceUnlocked as error:
            e = error.args[0]
            return ExecuteDeviceCommand(ok = False, message = [e.desc,e.reason])
        except Exception as e:
            return ExecuteDeviceCommand(ok = False, message = [str(e)]) 

class SetAttributeValue(Mutation):
    """ This class reprensents the mutation for setting value to an attribute. """
    
    class Arguments:
        device = String(required = True)
        name = String (required = True)
        value = ScalarTypes(required = True)

    ok = Boolean()
    message = List(String)

    def mutate(self, info, device, name,value):
        """ This method sets value to an attribute.
        
        Args:
            device(str): Name of the device.
            name(str): Name of the attribute.
            value(int or str or bool or float): The value to set.
        
        Returns:
            value(SetAttributeValue): return ok = True and message = Success if successful, 
            False otherwise.When an input is not one the scalar types 
            or an exception has been raised while setting the value 
            returns message = error_message.
        
        """

        if type(value) is ValueError:
            return SetAttributeValue(ok= False, message = [str(value)])
        try:
            proxy = proxies.get(device)
            proxy.write_attribute(name,value)
            return SetAttributeValue(ok=True, message = ["Success"])
        except PyTango.DevFailed or PyTango.ConnectionFailed or PyTango.CommunicationFailed or PyTango.DeviceUnlocked as error:
            e = error.args[0]
            return SetAttributeValue(ok = False,message = [e.desc,e.reason])
        except Exception as e:
            return SetAttributeValue(ok= False, message = [str(e)])
          
class PutDeviceProperty(Mutation):
    """ This class represents mutation for putting a device property. """

    class Arguments:
        device = String(required=True)
        name = String(required=True)
        value = List(String)
        # async = Boolean()

    ok = Boolean()
    message = List(String)
    def mutate(self,info, device,name,value =""):
        """ This method adds property to a device.
        
        Args:
            device(str): Name of a device.
            name(str):  Name of the property.
            value([str]): Value of the property.
        
        Returns:
            value(PutDeviceProperty):Returns ok = True and message = Success if successful, False otherwise.
            If an exception has been raised returns message = error_message.   
        
        """

        # wait = not args.get("async")
        try:
            db.put_device_property(device, {name: value})
            return PutDeviceProperty( ok = True, message = ["Success"])
        except PyTango.DevFailed or PyTango.ConnectionFailed or PyTango.CommunicationFailed or PyTango.DeviceUnlocked as error:
            e = error.args[0]
            return SetAttributeValue(ok = False,message = [e.desc,e.reason])
        except Exception as e:
            return SetAttributeValue(ok= False, message = [str(e)])

class DeleteDeviceProperty(Mutation):
    """This class represents mutation for deleting property of a device."""

    class Arguments:
        device = String(required=True)
        name = String(required=True)
    ok = Boolean()
    message = List(String)
    def mutate(self,info,device,name):
        """This method delete a property of a device.

        Args: 
            device(str): name of the device.
            name(str): name of the property.
        Returns:
            value(DeleteDeviceProperty):Returns ok = True and message = Success if successful,
            ok = False otherwise.If exception has been raised returns message = error_message.

        """

        try:
                db.delete_device_property(device, name)
                return DeleteDeviceProperty( ok = True, message = ["Success"])
        except PyTango.DevFailed or PyTango.ConnectionFailed or PyTango.CommunicationFailed or PyTango.DeviceUnlocked as error:
            e = error.args[0]
            return DeleteDeviceProperty(ok = False,message = [e.desc,e.reason])
        except Exception as e:
            return DeleteDeviceProperty(ok= False, message = [str(e)])

class DeviceAttribute(Interface):

    """ This class represents an attribute of a device.  """

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

        """ This method fetch the coresponding value of an attribute bases on its name.

        Returns:
            value(any): Value of the attribute.

        """

        #value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            if att_data.data_format != 0: # SPECTRUM and IMAGE
                temp_val = att_data.value
                if isinstance(temp_val, tuple):
                    value = list(temp_val)
                else:
                    value = att_data.value.tolist()
            else: # SCALAR
                    value = att_data.value 
        except PyTango.DevFailed or PyTango.ConnectionFailed or PyTango.CommunicationFailed or PyTango.DeviceUnlocked as error:
            e = error.args[0]
            return [e.desc,e.reason]
        except Exception as e:
            return str(e)
        return value

    def resolve_quality(self, *args, **kwargs):

        """ This method fetch the coresponding quality of an attribute bases on its name.
            
        Returns
            value(str): The quality of the attribute.

        """

        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            value = att_data.quality.name
        except:
            pass
        return value

    def resolve_timestamp(self, *args, **kwargs):

        """This method fetch the timestamp value of an attribute bases on its name.
        
        Returns:
            value(float): The timestamp value.
        
        """

        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            value = att_data.time.tv_sec
        except:
            pass
        return value

class ScalarDeviceAttribute(TangoSomething,ObjectType):
    class Meta:
        interfaces = (DeviceAttribute,)

class ImageDeviceAttribute(TangoSomething,ObjectType):
    class Meta:
        interfaces = (DeviceAttribute,)

class SpectrumDeviceAttribute(TangoSomething,ObjectType):
    class Meta: 
        interfaces = (DeviceAttribute,)

class DeviceCommand(TangoSomething, Interface):
    """ This class represents an command and its properties. """

    name = String()
    tag = Int()
    displevel = String()
    intype = String()
    intypedesc = String()
    outtype = String()
    outtypedesc = String()

class DeviceInfo(TangoSomething, Interface):
    """ This class represents info of a device.  """

    id = String()       #server id
    host = String()     #server host

class Device(TangoSomething, Interface):
    """ This class represent a device. """

    name = String()
    state = String()
    properties = List(DeviceProperty, pattern=String())
    attributes = List(DeviceAttribute, pattern=String())
    commands = List(DeviceCommand, pattern=String())
    server = List(DeviceInfo)

    #device_class = String()
    #server = String()
    pid = Int()
    started_date = String()
    stopped_date = String()
    exported = Boolean()

    def resolve_state(self,info):
        """ This method fetch the state of the device.
        
        Return:
            state(str): State of the device.
        
        """
        try:
            proxy = proxies.get(self.name)
            return proxy.state()
        except PyTango.DevFailed or PyTango.ConnectionFailed or PyTango.CommunicationFailed or PyTango.DeviceUnlocked:
            return "UNKNOWN"
        except Exception as e:
            return str(e)

    def resolve_properties(self, info, pattern="*"):

        """ This method fetch the properties of the device.
        
        Args:
            pattern(str): Pattern for filtering the result. Returns only properties that matches the pattern.
        
        Returns:
            properties([DeviceProperty]): List of properties for the device.
        
        """

        props = db.get_device_property_list(self.name, pattern)
        return [DeviceProperty(name=p, device=self.name) for p in props]

    def resolve_attributes(self, info, pattern="*"):

        """ This method fetch all the attributes and its' properties of a device.
        
        Args:
            pattern(str):  Pattern for filtering the result. Returns only properties that match the pattern.
        
        Returns:
            attributes([DeviceAttribute]): List of attributes of the device.
        
        """

        proxy = proxies.get(self.name)
        attr_infos = proxy.attribute_list_query()
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        sorted_info = sorted(attr_infos,key=attrgetter("name"))
        result = []
        for a in sorted_info:
            if rule.match(a.name):
                if str(a.data_format) =="SCALAR":
                    result.append(ScalarAttribute(
                        name=a.name,
                        device=self.name,
                        writable=a.writable,
                        datatype=PyTango.CmdArgType.values[a.data_type],
                        dataformat=a.data_format,
                        label=a.label,
                        unit=a.unit,
                        description=a.description))
                if str(a.data_format) =="SPECTRUM":
                    result.append(SpectrumAttribute(
                        name=a.name,
                        device=self.name,
                        writable=a.writable,
                        datatype=PyTango.CmdArgType.values[a.data_type],
                        dataformat=a.data_format,
                        label=a.label,
                        unit=a.unit,
                        description=a.description))
                if str(a.data_format) =="IMAGE":
                    result.append(ImageAttribute(
                        name=a.name,
                        device=self.name,
                        writable=a.writable,
                        datatype=PyTango.CmdArgType.values[a.data_type],
                        dataformat=a.data_format,
                        label=a.label,
                        unit=a.unit,
                        description=a.description))
        return result

    def resolve_commands(self, info, pattern="*"):
        """ This method fetch all the commands of a device.
        
        Args:
            pattern(str):  Pattern for filtering of the result. Returns only commands that match the pattern.
        
        Returns:
            commands([DeviceCommand]): List of commands of the device.
        
        """

        proxy = proxies.get(self.name)
        cmd_infos = proxy.command_list_query()
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)

        return [DeviceCommand(
            name=a.cmd_name,
            tag=a.cmd_tag,
            displevel=a.disp_level,
            intype=a.in_type,
            intypedesc=a.in_type_desc,
            outtype=a.out_type,
            outtypedesc=a.out_type_desc)
                for a in sorted(cmd_infos, key=attrgetter("cmd_name"))
                                if rule.match(a.cmd_name)]

    def resolve_server(self, info):
        """ This method fetch the server infomation of a device.
         
        Returns:
            server([DeviceInfo]): List server info of a device.
        
        """

        proxy = proxies.get(self.name)
        dev_info = proxy.info()

        return [DeviceInfo(
            id=dev_info.server_id,
            host=dev_info.server_host)]

    def resolve_exported(self, info):
        """ This method fetch the infomation about the device if it is exported or not.
        
        Returns:
            exported(bool): True if exported, False otherwise.
        
        """
        
        return self.info.exported
    def resolve_pid(self,info):
        return self.info.pid
    def resolve_started_date(self,info):
        return self.info.started_date
    def resolve_stopped_date(self,info):
        return self.info.stopped_date

    @property
    def info(self):

        """ This method fetch all the information of a device. """

        if not hasattr(self, "_info"):
            self._info = db.get_device_info(self.name)
        return self._info

class Member(Device):

    """ This class represent a member. """


    domain = String()
    family = String()

    @property
    def info(self):

        """ This method fetch a member of the device using the name of the domain and family. """

        if not hasattr(self, "_info"):
            devicename = "%s/%s/%s" % (self.domain, self.family, self.name)
            self._info = db.get_device_info(devicename)
        return self._info

class Family(TangoSomething, Interface):

    """ This class represent a family. """

    name = String()
    domain = String()
    members = List(Member, pattern=String())

    def resolve_members(self, info, pattern="*"):
        """ This method fetch members using the name of the domain and pattern.
            
        Args:
            pattern(str): Pattern for filtering of the result. Returns only members that match the pattern.
        
        Returns:
            members([Member]):List of members.
        
        """

        members = db.get_device_member(
            "%s/%s/%s" % (self.domain, self.name, pattern))
        return [
            Member(domain=self.domain, family=self.name, name=m)
            for m in members
        ]

class Domain(TangoSomething, Interface):

    """ This class represent a domain. """

    name = String()
    families = List(Family, pattern=String())

    def resolve_families(self, info, pattern="*"):
        """ This method fetch a list of families using pattern.
            
        Args:
            pattern(str): Pattern for filtering of the result. Returns only families that match the pattern.
        
        Returns:
            families([Family]):List of families.
        
        """

        families = db.get_device_family("%s/%s/*" % (self.name, pattern))
        return [Family(name=f, domain=self.name) for f in families]

class DeviceClass(TangoSomething, Interface):

    name = String()
    server = String()
    instance = String()
    devices = List(Device)

class ServerInstance(TangoSomething, Interface):
    """ Not documented yet. """

    name = String()
    server = String()
    classes = List(DeviceClass, pattern=String())

    def resolve_classes(self,info , pattern="*"):
        devs_clss = db.get_device_class_list("%s/%s" % (self.server, self.name))
        mapping = defaultdict(list)
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        for device, clss in zip(devs_clss[::2], devs_clss[1::2]):
            mapping[clss].append(Device(name=device))
        return [DeviceClass(name=clss, server=self.server, instance=self.name,
                            devices=devices)
                for clss, devices in mapping.items()
                if rule.match(clss)]

class Server(TangoSomething, Interface):
    """ This class represents a query for server. """

    name = String()
    instances = List(ServerInstance, pattern=String())

    def resolve_instances(self, info, pattern="*"):
        """ This method fetches all the intances using pattern.
            
            Args:
                pattern(str): Pattern for filtering the result. Returns only properties that matches the pattern.

            Returns:
                intances[ServerIntance]: List of intances.

        """
        instances = db.get_instance_name_list(self.name)
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [ServerInstance(name=inst, server=self.name)
                for inst in instances if rule.match(inst)]

class Query(ObjectType):
    """ This class contains all the queries. """
    devices = List(Device, pattern=String())
    domains = List(Domain, pattern=String())
    families = List(Family, domain=String(), pattern=String())
    members = List(Member, domain=String(), family=String(), pattern=String())

    servers = List(Server, pattern=String())
    instances = List(ServerInstance, server=String(), pattern=String())
    classes = List(DeviceClass, pattern=String())

    def resolve_devices(self, info, pattern="*"):
        """ This method fetches all the devices using the pattern.
        
        Args: 
            pattern(str): Pattern for filtering the result. Returns only properties that matches the pattern.
        
        Returns:
            devices([Device]): List of devices.
    
        """
        devices = db.get_device_exported(pattern)
        return [Device(name=d) for d in sorted(devices)]

    def resolve_domains(self, info, pattern="*"):
        """ This method fetches all the domains using the pattern.
        
        Args: 
            pattern(str): Pattern for filtering the result. Returns only properties that matches the pattern.
        
        Returns:
            domains([Domain]): List of domains.
    
        """
        domains = db.get_device_domain("%s/*" % pattern)
        return [Domain(name=d) for d in sorted(domains)]

    def resolve_families(self, info, domain="*", pattern="*"):
        """ This method fetches all the families using the pattern.
        
        Args: 
            pattern(str): Pattern for filtering the result. Returns only properties that matches the pattern.
        
        Returns:
            families([Family]): List of families.
    
        """
        
        families = db.get_device_family("%s/%s/*" % (domain, pattern))
        return [Family(domain=domain, name=d) for d in sorted(families)]

    def resolve_members(self, info, domain="*", family="*", pattern="*"):
        """ This method fetches all the members using the pattern.
        
        Args: 
            pattern(str): Pattern for filtering the result. Returns only properties that matches the pattern.
        
        Returns:
            members([Domain]): List of members.
    
        """
        members = db.get_device_member("%s/%s/%s" % (domain, family, pattern))
        return [Member(domain=domain, family=family, name=m)
                for m in sorted(members)]

    def resolve_servers(self, info, pattern="*"):
        """ This method fetches all the servers using the pattern.
        
        Args: 
            pattern(str): Pattern for filtering the result. Returns only properties that matches the pattern.
        
        Returns:
            servers([Domain]): List of servers.
    
        """

        servers = db.get_server_name_list()
        # The db service does not allow wildcard here, but it can still
        # useful to limit the number of children. Let's fake it!
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [Server(name=srv) for srv in sorted(servers) if rule.match(srv)]

class DatabaseMutations(ObjectType):
    """ This class contains all the mutations. """

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
    attribute = Field(DeviceAttribute)

class ChangeEvent(ObjectType):
    class Meta:
        interfaces = (Event,)
    data = Field(ChangeData)

class ConfigEvent(ObjectType):
    class Meta:
        interfaces = (Event,)
    data = Field(ConfigData)

# Contains subscribed attributes
change_listeners = {}
config_listeners ={}

class Subscription(ObjectType):
    sub_change_event = Field(List(ChangeEvent),sub_list = List(String))
    unsub_config_event = String(unsub_list = List(String))
    unsub_change_event = String(unsub_list = List(String))
    sub_config_event = Field(List(ConfigEvent),sub_list = List(String))
    
    async def resolve_sub_change_event(self,info,sub_list = []):
        keeper = EventKeeper()
        for attr in sub_list:
            l = TaurusWebAttribute(attr, keeper)
            change_listeners[attr] = l
        i = 0
        while change_listeners:
            evt_list = []
            events = keeper.get()
            for event_type,data in events.items():
                for attr_name, value in data.items():
                    device,attr = attr_name.rsplit('/',1)
                    if event_type == "CHANGE":
                        data = ChangeData(value = value['value'],
                                        w_value = value['w_value'],
                                        quality = value['quality'],
                                        time = value['time'])  
                        event = ChangeEvent(event_type = event_type, 
                                            attribute = DeviceAttribute(device = device,name = attr),
                                            data = data)
                        evt_list.append(event)  
            if evt_list:
                yield evt_list
            await asyncio.sleep(1.0)

    async def resolve_sub_config_event(self, info, sub_list = []):
        keeper = EventKeeper()
        for attr in sub_list:
            l = TaurusWebAttribute(attr, keeper)
            config_listeners[attr] = l
        i = 0
        while config_listeners:
            evt_list = []
            events = keeper.get()
            for event_type,data in events.items():
                for attr_name, value in data.items():
                    device,attr = attr_name.rsplit('/',1)
                    if event_type == "CONFIG":
                        data = ConfigData(description = value['description'],
                                        label = value['label'],
                                        unit = value['unit'],
                                        format = value['format'],
                                        data_format = value['data_format'],
                                        data_type = value['data_type']    
                                    )
                        event = ConfigEvent(event_type = event_type,
                                            attribute = DeviceAttribute(device = device,name = attr),
                                            data = data)
                        evt_list.append(event)  
            if evt_list:
                yield evt_list
            await asyncio.sleep(1.0)
    async def resolve_unsub_change_event(self, info,unsub_list = []):
        result = []
        if change_listeners:
            for attr in unsub_list:
                listener = change_listeners[attr]
                if listener:
                    listener.clear()
                    del change_listeners[attr]
                    result.append(attr)
            yield "Unsubscribed: " + ','.join(result)
        else:
            yield "No attribute to unsubscribe"
        

    async def resolve_unsub_config_event(self, info,unsub_list = []):
        result = []
        if config_listeners:
            for attr in unsub_list:
                listener = config_listeners[attr]
                if listener:
                    listener.clear()
                    del config_listeners[attr]
                    result.append(attr)
            yield "Unsubscribed: " + ','.join(result)
        else:
            yield "No attribute to unsubscribe"

# Help class
class EventKeeper:

    """A simple wrapper that keeps the latest event values for
    each attribute"""

    def __init__(self):
        self._events = defaultdict(dict)
        self._timestamps = defaultdict(dict)
        self._latest = defaultdict(dict)

    def put(self, model, action, value):
        "Update a model"
        self._events[action][model] = value
        self._timestamps[action][model] = time.time()

    def get(self):
        "Returns the latest accumulated events"
        tmp, self._events = self._events, defaultdict(dict)
        for event_type, events in tmp.items():
            self._latest[event_type].update(events)
        return tmp

tangoschema = graphene.Schema(query=Query, mutation=DatabaseMutations, subscription = Subscription, 
                            types = [ScalarDeviceAttribute,
                                    ImageDeviceAttribute,
                                    SpectrumDeviceAttribute,
                                    DeviceAttribute])
if __name__ == "__main__":

    # test/example

    q = """
    query Hejsan {
        a: devices(pattern: "sys/tg_test/1") {

            name
            exported
            properties {
              name
              value
            }
            attributes(pattern: "*scalar*") {
              name
              label
              unit
              datatype
              dataformat
              value
              timestamp
              quality
            }
        }
        # b: devices(pattern: "sys/database/*") {
        #     name
        #     info {
        #       exported
        #     }

        #     attributes(pattern: "state") {
        #       name
        #       label
        #     }
        # },

        # domains(pattern: "*") {
        #     name
        #     families(pattern: "*") {
        #         name
        #     }
        # }
    }
    """

    result = tangoschema.execute(q)
    if result.errors:
        traceback.print_tb(result.errors[0].stack, limit=10, file=sys.stdout)
    import json
    print(json.dumps(result.data, indent=4))
