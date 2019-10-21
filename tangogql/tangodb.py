#!/usr/bin/env python3

"""
A simple caching layer on top of a TANGO database.
"""

from collections import OrderedDict

from tango import Database, DeviceProxy, GreenMode

from tangogql.ttldict import TTLDict


class CachedMethod(object):
    """A cached wrapper for a DB method."""

    def __init__(self, method, ttl=10):
        self.cache = TTLDict(default_ttl=ttl)
        self.method = method

    def __call__(self, *args):
        if args in self.cache:
            return self.cache[args]
        value = self.method(*args)
        self.cache[args] = value
        return value


class CachedDatabase(object):
    """A TANGO database wrapper that caches 'get' methods."""

    _db = Database()
    _methods = {}

    def __init__(self, ttl):
        self._ttl = ttl

    def __getattr__(self, method):
        if not method.startswith("get_"):
            # caching 'set' methods doesn't make any sense anyway
            # TODO: check that this really catches the right methods
            return getattr(self._db, method)
        if method not in self._methods:
            self._methods[method] = CachedMethod(getattr(self._db, method),
                                                 ttl=self._ttl)
        return self._methods[method]


class DeviceProxyCache(object):
    """Keep a limited cache of device proxies that are reused."""
    # TODO: does this actually work? Are the proxies really cleaned up
    # by PyTango after they are deleted?

    def __init__(self, max_proxies=100):
        self.max_proxies = max_proxies
        self._device_proxies = OrderedDict()

    def get(self, devname):
        if devname in self._device_proxies:
            # Proxy to this device already exists
            proxy = self._device_proxies.pop(devname)
            self._device_proxies[devname] = proxy  # putting it first
            return proxy
        # Unknown device; let's create a new proxy
        proxy = DeviceProxy(devname, green_mode=GreenMode.Asyncio)
        if len(self._device_proxies) == self.max_proxies:
            # delete the oldest proxy last = False means FIFO
            self._device_proxies.popitem(last=False)
        self._device_proxies[devname] = proxy
        return proxy
