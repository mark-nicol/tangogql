"""Module containing Queries."""

import re
import fnmatch
import PyTango
import copy
from collections import defaultdict
from graphene import ObjectType, String, List, Field, Int
from tangogql.schema.types import ScalarTypes
from tangogql.schema.base import db, proxies
from tangogql.schema.device import Device, DeviceCommand
from tangogql.schema.attribute import DeviceAttribute
from tangogql.schema.log import user_actions, UserAction


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


class Family(ObjectType):
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


class Domain(ObjectType):
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


class DeviceClass(ObjectType):

    name = String()
    server = String()
    instance = String()
    devices = List(Device)


# TODO: Missing documentation
class ServerInstance(ObjectType):
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


class Server(ObjectType):
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

    info = String()
    devices = List(Device, pattern=String())
    device = Field(Device, name=String(required=True))
    domains = List(Domain, pattern=String())
    families = List(Family, domain=String(), pattern=String())
    members = List(Member, domain=String(), family=String(), pattern=String())
    user_actions = List(UserAction, pattern=String(),skip=Int(),first=Int())
    servers = List(Server, pattern=String())
    instances = List(ServerInstance, server=String(), pattern=String())
    classes = List(DeviceClass, pattern=String())

    attributes = List(DeviceAttribute, full_names=List(String, required=True))
    commands = List(DeviceCommand, full_names=List(String, required=True))

    async def resolve_info(self, info):
        db = PyTango.Database()
        return db.get_info()

    async def resolve_device(self, info, name=None):
        """ This method fetches the device using the name.

        :param name: Name of the device.
        :type name: str

        :return:  Device.
        :rtype: Device    
        """
        device_names = db.get_device_exported(name)
        if len(device_names) == 1:
            return Device(name=device_names[0])
        else:
            return None

    async def resolve_devices(self, info, pattern="*"):
        """ This method fetches all the devices using the pattern.

        :param pattern: Pattern for filtering the result.
                        Returns only properties that matches the pattern.
        :type pattern: str

        :return: List of devices.
        :rtype: List of Device    
        """
        device_names = db.get_device_exported(pattern)
        return [Device(name=name) for name in device_names]

    async def resolve_attributes(self, info, full_names):
        result = []
        attr_list = defaultdict(list)

        for name in full_names:
            *parts, attribute = name.split('/')
            device = '/'.join(parts)
            attr_list[device].append(attribute)
                
        for device, attrs in attr_list.items():
            proxy = proxies.get(device)
            attr_infos = proxy.attribute_list_query()

            for attr_info in attr_infos:
                if attr_info.name in attrs:
                    result.append(DeviceAttribute(
                        name=attr_info.name,
                        device=device,
                    ))

        return result

    async def resolve_commands(self, info, full_names):
        result = []
        cmd_list = defaultdict(list)

        for name in full_names:
            *parts, command_name = name.split('/')
            device_name = '/'.join(parts)
            cmd_list[device_name].append(command_name)

        for device_name, command_names in cmd_list.items():
            proxy = proxies.get(device_name)
            cmd_infos = proxy.command_list_query()

            for cmd_info in cmd_infos:
                if cmd_info.cmd_name in command_names:
                    result.append(DeviceCommand(name=cmd_info.cmd_name,
                        tag=cmd_info.cmd_tag,
                        displevel=cmd_info.disp_level,
                        intype=cmd_info.in_type,
                        intypedesc=cmd_info.in_type_desc,
                        outtype=cmd_info.out_type,
                        outtypedesc=cmd_info.out_type_desc,
                        device=device_name
                    ))

        return result

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

    def resolve_user_actions(self, info, pattern="*", first = None, skip = None):
        """ This method fetches the user actions.

        :param name: Name of the user.
        :type name: str

        :return:  Log.
        :rtype: Log    
        """
        result = user_actions.get(pattern)
        if skip:
            result = result[skip:]

        if first:
            result = result[:first]
        
        return result
