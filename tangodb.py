"""
A simple caching layer on top of a TANGO database
"""

from collections import OrderedDict

import PyTango

from ttldict import TTLDict


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

    """A TANGO database wrapper that caches 'get' methods"""

    _db = PyTango.Database()
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


# Keep a cache of device proxies
# TODO: does this actually work? Are the proxies really cleaned up
# after they are deleted?
MAX_PROXIES = 100
_device_proxies = OrderedDict()


def get_device_proxy(devname):
    """Keep a cache of the MAX_PROXIES last used proxies, and reuse
    proxies pointing to the same device"""
    if devname in _device_proxies:
        return _device_proxies[devname]
    proxy = PyTango.DeviceProxy(devname)
    if len(_device_proxies) == MAX_PROXIES:
        oldest = _device_proxies.keys()[0]
        del _device_proxies[oldest]
    _device_proxies[devname] = proxy
    return proxy


