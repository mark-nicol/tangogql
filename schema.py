"""
A GraphQL schema for TANGO.
"""

import fnmatch
import re
from collections import defaultdict

import PyTango
import graphene
from graphene import (Boolean, Field, Float, Int, Interface, List, Mutation,
    ObjectType, String)
from tangodb import CachedDatabase, get_device_proxy


db = CachedDatabase(ttl=10)


class TangoSomething(Interface):

    nodetype = String()

    @graphene.resolve_only_args
    def resolve_nodetype(self):
        return type(self).__name__.lower()


class DeviceProperty(TangoSomething):

    name = String()
    device = String()
    value = List(String())

    def resolve_value(self, args, info):
        device = self.device
        name = self.name
        value = db.get_device_property(device, name)
        if value:
            return [line for line in value[name]]


class PutDeviceProperty(Mutation):

    ok = Boolean()

    class Input:
        device = String()
        name = String()
        value = List(String())
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

    class Input:
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


class DeviceAttribute(TangoSomething):

    name = String()
    device = String()
    data_type = String()
    data_format = String()
    writable = String()
    label = String()
    unit = String()


class Device(TangoSomething):

    name = String()
    properties = List(DeviceProperty, pattern=String())
    attributes = List(DeviceAttribute, pattern=String())

    device_class = String()
    server = String()
    pid = Int()
    started_date = Float()
    stopped_date = Float()
    exported = Boolean()

    @graphene.resolve_only_args
    def resolve_properties(self, pattern="*"):
        props = db.get_device_property_list(self.name, pattern)
        return [DeviceProperty(name=p, device=self.name) for p in props]

    @graphene.resolve_only_args
    def resolve_attributes(self, pattern="*"):
        proxy = get_device_proxy(self.name)
        attr_infos = proxy.attribute_list_query()
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [DeviceAttribute(name=a.name, device=self.name,
                                data_type=str(a.data_type),
                                writable=str(a.writable),
                                data_format=str(a.data_format),
                                label=a.label, unit=a.unit)
                for a in attr_infos if rule.match(a.name)]

    @graphene.resolve_only_args
    def resolve_exported(self):
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


class Family(TangoSomething):

    name = String()
    domain = String()
    members = List(Member, pattern=String())

    @graphene.resolve_only_args
    def resolve_members(self, pattern="*"):
        members = db.get_device_member(
            "%s/%s/%s" % (self.domain, self.name, pattern))
        return [
            Member(domain=self.domain, family=self.name, name=m)
            for m in members
        ]


class Domain(TangoSomething):

    name = String()
    families = List(Family, pattern=String())

    @graphene.resolve_only_args
    def resolve_families(self, pattern="*"):
        families = db.get_device_family("%s/%s/*" % (self.name, pattern))
        return [Family(name=f, domain=self.name) for f in families]


class DeviceClass(TangoSomething):

    name = String()
    server = String()
    instance = String()
    devices = List(Device)


class ServerInstance(TangoSomething):

    name = String()
    server = String()
    classes = List(DeviceClass, pattern=String())

    @graphene.resolve_only_args
    def resolve_classes(self, pattern="*"):
        devs_clss = db.get_device_class_list("%s/%s" % (self.server, self.name))
        mapping = defaultdict(list)
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        for device, clss in zip(devs_clss[::2], devs_clss[1::2]):
            mapping[clss].append(Device(name=device))
        return [DeviceClass(name=clss, server=self.server, instance=self.name,
                            devices=devices)
                for clss, devices in mapping.items()
                if rule.match(clss)]


class Server(TangoSomething):

    name = String()
    instances = List(ServerInstance, pattern=String())

    @graphene.resolve_only_args
    def resolve_instances(self, pattern="*"):
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

    @graphene.resolve_only_args
    def resolve_devices(self, pattern="*"):
        devices = db.get_device_exported(pattern)
        return [Device(name=d) for d in devices]

    @graphene.resolve_only_args
    def resolve_domains(self, pattern="*"):
        domains = db.get_device_domain("%s/*" % pattern)
        return [Domain(name=d) for d in domains]

    @graphene.resolve_only_args
    def resolve_families(self, domain="*", pattern="*"):
        families = db.get_device_family("%s/%s/*" % (domain, pattern))
        return [Family(domain=domain, name=d) for d in families]

    @graphene.resolve_only_args
    def resolve_members(self, domain="*", family="*", pattern="*"):
        members = db.get_device_member("%s/%s/%s" % (domain, family, pattern))
        return [Member(domain=domain, family=family, name=m) for m in members]

    @graphene.resolve_only_args
    def resolve_servers(self, pattern="*"):
        servers = db.get_server_name_list()
        # The db service does not allow wildcard here, but it can still
        # useful to limit the number of children. Let's fake it!
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        return [Server(name=srv) for srv in servers if rule.match(srv)]


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
            info {
              exported
              server
            }
            properties {
              name
              value
            }
        },
        b: devices(pattern: "sys/database/*") {
            name
            info {
              exported
            }

            attributes(pattern: "state") {
              name
              label
            }
        },

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
