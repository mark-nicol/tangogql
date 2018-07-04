"""
A GraphQL schema for TANGO.
"""
from graphene.types.scalars import MIN_INT, MAX_INT
import six
import fnmatch
import re
from collections import defaultdict
from operator import attrgetter
import json
import PyTango
import graphene
from graphene import (Boolean, Field, Float, Int, Interface, List, Mutation,
                      ObjectType, String, Union,Scalar)
from tangodb import CachedDatabase, DeviceProxyCache
from graphene.types import Scalar
from graphql.language import ast
db = CachedDatabase(ttl=10)
proxies = DeviceProxyCache()


class TangoSomething(ObjectType):

    nodetype = String()

    def resolve_nodetype(self, info):
        return type(self).__name__.lower()

class DeviceProperty(TangoSomething, Interface):

    name = String()
    device = String()
    value = List(String)

    def resolve_value(self, info):
        device = self.device
        name = self.name
        value = db.get_device_property(device, name)
        if value:
            return [line for line in value[name]]

class ScalarTypes(Scalar):
    '''The ScalarTypes represents a geneneric scalar value that could be:
    Int, String, Boolean, Float, List'''
    @staticmethod
    def coerce_type(value):
        #value of type DevState should return as string 
        if type(value).__name__ == "DevState":
            return str(value)
        return value
    @staticmethod
    def serialize(value):
        return ScalarTypes.coerce_type(value)
    @staticmethod
    def parse_value(value):
        return ScalarTypes.coerce_type(value)
    #Called for the input
    @staticmethod
    def parse_literal(node):
        try:
            if isinstance(node, ast.IntValue):
                return int(node.value)
            elif isinstance(node,ast.FloatValue):
                return float(node.value)
            elif isinstance(node, ast.BooleanValue):
                return node.value
            elif isinstance(node, ast.ListValue):
                return [ScalarTypes.parse_literal(value) for value in node.values]
            else:
                raise ValueError('The input value is not of acceptable types')
        except Exception as e:
            return e

class SetAttributeValue(Mutation):
    
    class Arguments:
        device = String(required = True)
        name = String (required = True)
        value = ScalarTypes(required = True)
    ok = Boolean()
    message = List(String)
    def mutate(self, info, device, name,value):
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
    class Arguments:
        device = String(required=True)
        name = String(required=True)
        value = List(String)
        # async = Boolean()

    ok = Boolean()

    def mutate(self,info, device,name,value =""):
        # wait = not args.get("async")
        try:
            db.put_device_property(device, {name: value})
            return PutDeviceProperty( ok = True)
        except PyTango.DevFailed:
            return PutDeviceProperty(ok = False)


class DeleteDeviceProperty(Mutation):

    ok = Boolean()

    class Arguments:
        device = String(required=True)
        name = String(required=True)

    def mutate(self,info,device,name):

        try:
            db.delete_device_property(device, name)
            return DeleteDeviceProperty(ok=True)

        except PyTango.DevFailed:
            return DeleteDeviceProperty(ok=False)

class DeviceAttribute(TangoSomething, Interface):

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
        value = None
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
        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            value = att_data.quality.name
        except:
            pass
        return value

    def resolve_timestamp(self, *args, **kwargs):
        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            value = att_data.time.tv_sec
        except:
            pass
        return value

class DeviceCommand(TangoSomething, Interface):
    name = String()
    tag = Int()
    displevel = String()
    intype = String()
    intypedesc = String()
    outtype = String()
    outtypedesc = String()

class DeviceInfo(TangoSomething, Interface):
    id = String()       #server id
    host = String()     #server host


class Device(TangoSomething, Interface):
    name = String()
    state = String()
    properties = List(DeviceProperty, pattern=String())
    attributes = List(DeviceAttribute, pattern=String())
    commands = List(DeviceCommand, pattern=String())
    server = List(DeviceInfo)

    device_class = String()
    #server = String()
    pid = Int()
    started_date = Float()
    stopped_date = Float()
    exported = Boolean()
    def resolve_state(self,info):
        proxy = proxies.get(self.name)
        return proxy.state()
    def resolve_properties(self, info, pattern="*"):
        props = db.get_device_property_list(self.name, pattern)
        return [DeviceProperty(name=p, device=self.name) for p in props]

    def resolve_attributes(self, info, pattern="*"):
        proxy = proxies.get(self.name)
        attr_infos = proxy.attribute_list_query()
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [DeviceAttribute(
            name=a.name,
            device=self.name,
            writable=a.writable,
            datatype=PyTango.CmdArgType.values[a.data_type],
            dataformat=a.data_format,
            label=a.label,
            unit=a.unit,
            description=a.description)
                for a in sorted(attr_infos, key=attrgetter("name"))
                                if rule.match(a.name)]

    def resolve_commands(self, info, pattern="*"):
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
        proxy = proxies.get(self.name)
        dev_info = proxy.info()

        return [DeviceInfo(
            id=dev_info.server_id,
            host=dev_info.server_host)]

    def resolve_exported(self, info):
        return self.info.exported

    @property
    def info(self):
        if not hasattr(self, "_info"):
            self._info = db.get_device_info(self.name)
        return self._info


class Member(Device):

    domain = String()
    family = String()

    @property
    def info(self):
        if not hasattr(self, "_info"):
            devicename = "%s/%s/%s" % (self.domain, self.family, self.name)
            self._info = db.get_device_info(devicename)
        return self._info


class Family(TangoSomething, Interface):

    name = String()
    domain = String()
    members = List(Member, pattern=String())

    def resolve_members(self, info, pattern="*"):
        members = db.get_device_member(
            "%s/%s/%s" % (self.domain, self.name, pattern))
        return [
            Member(domain=self.domain, family=self.name, name=m)
            for m in members
        ]


class Domain(TangoSomething, Interface):

    name = String()
    families = List(Family, pattern=String())

    def resolve_families(self, info, pattern="*"):
        families = db.get_device_family("%s/%s/*" % (self.name, pattern))
        return [Family(name=f, domain=self.name) for f in families]


class DeviceClass(TangoSomething, Interface):

    name = String()
    server = String()
    instance = String()
    devices = List(Device)


class ServerInstance(TangoSomething, Interface):

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

    name = String()
    instances = List(ServerInstance, pattern=String())

    def resolve_instances(self, info, pattern="*"):
        instances = db.get_instance_name_list(self.name)
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [ServerInstance(name=inst, server=self.name)
                for inst in instances if rule.match(inst)]


class Query(ObjectType):

    devices = List(Device, pattern=String())
    domains = List(Domain, pattern=String())
    families = List(Family, domain=String(), pattern=String())
    members = List(Member, domain=String(), family=String(), pattern=String())

    servers = List(Server, pattern=String())
    instances = List(ServerInstance, server=String(), pattern=String())
    classes = List(DeviceClass, pattern=String())

    def resolve_devices(self, info, pattern="*"):
        devices = db.get_device_exported(pattern)
        return [Device(name=d) for d in sorted(devices)]

    def resolve_domains(self, info, pattern="*"):
        domains = db.get_device_domain("%s/*" % pattern)
        return [Domain(name=d) for d in sorted(domains)]

    def resolve_families(self, info, domain="*", pattern="*"):
        families = db.get_device_family("%s/%s/*" % (domain, pattern))
        return [Family(domain=domain, name=d) for d in sorted(families)]

    def resolve_members(self, info, domain="*", family="*", pattern="*"):
        members = db.get_device_member("%s/%s/%s" % (domain, family, pattern))
        return [Member(domain=domain, family=family, name=m)
                for m in sorted(members)]

    def resolve_servers(self, info, pattern="*"):
        servers = db.get_server_name_list()
        # The db service does not allow wildcard here, but it can still
        # useful to limit the number of children. Let's fake it!
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [Server(name=srv) for srv in sorted(servers) if rule.match(srv)]


class DatabaseMutations(ObjectType):
    put_device_property = PutDeviceProperty.Field()
    delete_device_property = DeleteDeviceProperty.Field()
    SetAttributeValue = SetAttributeValue.Field()

tangoschema = graphene.Schema(query=Query, mutation=DatabaseMutations)


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
    import json
    print(json.dumps(result.data, indent=4))