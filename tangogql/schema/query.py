"""Module containing Queries."""

import re
import fnmatch
import PyTango
from collections import defaultdict
from graphene import Interface, ObjectType, String, List, Field

from tangogql.schema.base import db, proxies
from tangogql.schema.device import Device
from tangogql.schema.user import UserLog

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


class Family(ObjectType, Interface):
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


class Domain(ObjectType, Interface):
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


class DeviceClass(ObjectType, Interface):

    name = String()
    server = String()
    instance = String()
    devices = List(Device)


# TODO: Missing documentation
class ServerInstance(ObjectType, Interface):
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


class Server(ObjectType, Interface):
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
    device = Field(Device, name=String(required=True))
    domains = List(Domain, pattern=String())
    families = List(Family, domain=String(), pattern=String())
    members = List(Member, domain=String(), family=String(), pattern=String())
    
    servers = List(Server, pattern=String())
    instances = List(ServerInstance, server=String(), pattern=String())
    classes = List(DeviceClass, pattern=String())
    userlog = Field(UserLog, user = String(required=True))

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
    def resolve_userlog(self, info, user):
        """ This method fetches the activity log using the name.

        :param name: Name of the user.
        :type name: str

        :return:  UserLog.
        :rtype: UserLog    
        """
        
        return UserLog(user = user)