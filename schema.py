"""
A GraphQL schema for TANGO.
"""

import re
import fnmatch

import PyTango
import graphene
from tangodb import CachedDatabase, get_device_proxy


db = CachedDatabase(ttl=10)


class TangoSomething(graphene.Interface):

    nodetype = graphene.String()

    @graphene.resolve_only_args
    def resolve_nodetype(self):
        return type(self).__name__.lower()


class DeviceProperty(TangoSomething):

    name = graphene.String()
    device = graphene.String()
    value = graphene.List(graphene.String())

    def resolve_value(self, args, info):
        device = self.device
        name = self.name
        value = db.get_device_property(device, name)
        if value:
            return [line for line in value[name]]


class PutDeviceProperty(graphene.Mutation):

    ok = graphene.Boolean()

    class Input:
        device = graphene.String()
        name = graphene.String()
        value = graphene.List(graphene.String())
        # async = graphene.Boolean()

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


class DeleteDeviceProperty(graphene.Mutation):

    ok = graphene.Boolean()

    class Input:
        device = graphene.String()
        name = graphene.String()

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

    name = graphene.String()
    device = graphene.String()
    data_type = graphene.String()
    data_format = graphene.String()
    writable = graphene.String()
    label = graphene.String()
    unit = graphene.String()


class DeviceInfo(TangoSomething):

    name = graphene.String()
    device_class = graphene.String()
    server = graphene.String()
    # last_exported = graphene.Float()
    # last_unexported = graphene.Float()
    exported = graphene.Boolean()


class Device(TangoSomething):

    name = graphene.String()
    info = graphene.Field(DeviceInfo)
    properties = graphene.List(DeviceProperty, pattern=graphene.String())
    attributes = graphene.List(DeviceAttribute, pattern=graphene.String())

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
        proxy = get_device_proxy(self.name)
        device_info = proxy.info()
        import_info = proxy.import_info()
        return DeviceInfo(name=self.name,
                          device_class=device_info.dev_class,
                          server=device_info.server_id,
                          exported=import_info.exported)


class Member(TangoSomething):

    domain = graphene.String()
    family = graphene.String()
    name = graphene.String()

    properties = graphene.List(DeviceProperty, pattern=graphene.String())

    @graphene.resolve_only_args
    def resolve_properties(self, pattern="*"):
        device = "%s/%s/%s" % (self.domain, self.family, self.name)
        props = db.get_device_property_list(device, pattern)
        return [DeviceProperty(name=p, device=device) for p in props]


class Family(TangoSomething):

    name = graphene.String()
    domain = graphene.String()
    members = graphene.List(Member, pattern=graphene.String())

    @graphene.resolve_only_args
    def resolve_members(self, pattern="*"):
        members = db.get_device_member(
            "%s/%s/%s" % (self.domain, self.name, pattern))
        return [
            Member(domain=self.domain, family=self.name, name=m)
            for m in members
        ]


class Domain(TangoSomething):

    name = graphene.String()
    families = graphene.List(Family, pattern=graphene.String())

    @graphene.resolve_only_args
    def resolve_families(self, pattern="*"):
        families = db.get_device_family("%s/%s/*" % (self.name, pattern))
        return [Family(name=f, domain=self.name) for f in families]


class Query(graphene.ObjectType):

    devices = graphene.List(Device, pattern=graphene.String())
    domains = graphene.List(Domain, pattern=graphene.String())
    families = graphene.List(Family, domain=graphene.String(),
                             pattern=graphene.String())
    members = graphene.List(Member, domain=graphene.String(),
                            family=graphene.String(),
                            pattern=graphene.String())

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


class DatabaseMutations(graphene.ObjectType):
    put_device_property = graphene.Field(PutDeviceProperty)
    delete_device_property = graphene.Field(DeleteDeviceProperty)


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
