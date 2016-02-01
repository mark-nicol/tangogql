"""
A GraphQL schema for TANGO.
"""

import re
import fnmatch

import PyTango
import graphene
from graphene import (String, Int, Float, Boolean, List, Field,
                      Interface, Mutation, ObjectType)
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


class DeviceInfo(TangoSomething):

    name = String()
    device_class = String()
    server = String()
    pid = Int()
    started_date = Float()
    stopped_date = Float()
    exported = Boolean()


class Device(TangoSomething):

    name = String()
    info = Field(DeviceInfo)
    properties = List(DeviceProperty, pattern=String())
    attributes = List(DeviceAttribute, pattern=String())

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
    def resolve_info(self):
        info = db.get_device_info(self.name)
        return DeviceInfo(name=self.name,
                          device_class=info.class_name,
                          server=info.ds_full_name,
                          exported=info.exported,
                          pid=info.pid,
                          started_date=info.started_date,
                          stopped_date=info.stopped_date)


class Member(TangoSomething):

    domain = String()
    family = String()
    name = String()

    properties = List(DeviceProperty, pattern=String())

    @graphene.resolve_only_args
    def resolve_properties(self, pattern="*"):
        device = "%s/%s/%s" % (self.domain, self.family, self.name)
        props = db.get_device_property_list(device, pattern)
        return [DeviceProperty(name=p, device=device) for p in props]


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


class Query(ObjectType):

    devices = List(Device, pattern=String())
    domains = List(Domain, pattern=String())
    families = List(Family, domain=String(), pattern=String())
    members = List(Member, domain=String(), family=String(), pattern=String())

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
