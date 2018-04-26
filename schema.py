"""
A GraphQL schema for TANGO.
"""

import fnmatch
import re
from collections import defaultdict
from operator import attrgetter

import PyTango
import graphene
from graphene import (Boolean, Field, Float, Int, Interface, List, Mutation,
                      ObjectType, String)
from tangodb import CachedDatabase, DeviceProxyCache


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


class PutDeviceProperty(Mutation):

    ok = Boolean()

    class Arguments:
        device = String()
        name = String()
        value = List(String)
        # async = Boolean()

    @classmethod
    def mutate(cls, instance, args, info):
        device = args["device"]
        name = args["name"]
        value = args.get("value")
        # wait = not args.get("async")
        try:
            db.put_device_property(device, {name: value})
            print(db.get_device_property(device, name))
            print(device, name, value)
        except PyTango.DevFailed:
            return PutDeviceProperty(ok=False)
        return PutDeviceProperty(ok=True)


class DeleteDeviceProperty(Mutation):

    ok = Boolean()

    class Arguments:
        device = String()
        name = String()

    @classmethod
    def mutate(cls, instance, args, info):
        device = args["device"]
        name = args["name"]
        try:
            db.delete_device_property(device, name)
        except PyTango.DevFailed:
            return DeleteDeviceProperty(ok=False)
        return DeleteDeviceProperty(ok=True)


class DeviceAttribute(TangoSomething, Interface):

    name = String()
    device = String()
    datatype = String()
    dataformat = String()
    writable = String()
    label = String()
    unit = String()
    description = String()

    # @graphene.resolve_only_args
    # def resolve_data_type(self):
    #     proxy = proxies.get(self.device)
    #     info = proxy.get_attribute_config(self.name)
    #     return str(info.data_type)

    # @graphene.resolve_only_args
    # def resolve_data_format(self):
    #     print("resolve_data_format", self.device, self.name)
    #     proxy = proxies.get(self.device)
    #     info = proxy.get_attribute_config(self.name)
    #     return str(info.data_format)


class Device(TangoSomething, Interface):

    name = String()
    properties = List(DeviceProperty, pattern=String())
    attributes = List(DeviceAttribute, pattern=String())

    device_class = String()
    server = String()
    pid = Int()
    started_date = Float()
    stopped_date = Float()
    exported = Boolean()

    def resolve_properties(self, info, pattern="*"):
        props = db.get_device_property_list(self.name, pattern)
        return [DeviceProperty(name=p, device=self.name) for p in props]

    def resolve_attributes(self, info, pattern="*"):
        print("resolving_attributes ", self.name, pattern)
        proxy = proxies.get(self.name)
        attr_infos = proxy.attribute_list_query()
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [DeviceAttribute(
            name=a.name, device=self.name, writable=a.writable,
            datatype=PyTango.CmdArgType.values[a.data_type],
            dataformat=a.data_format,
            label=a.label, unit=a.unit, description=a.description)
                for a in sorted(attr_infos, key=attrgetter("name"))
                                if rule.match(a.name)]

    def resolve_exported(self, info):
        return self.info.exported

    @property
    def info(self):
        if not hasattr(self, "_info"):
            print("info", self.name)
            self._info = db.get_device_info(self.name)
            print(self._info)
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
    put_device_property = Field(PutDeviceProperty)
    delete_device_property = Field(DeleteDeviceProperty)


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
            attributes {
              name
              label
              unit
              datatype
              dataformat
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
