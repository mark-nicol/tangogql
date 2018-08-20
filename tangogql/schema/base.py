"""Module containing the Base classes for the Tango Schema."""


from tangogql.tangodb import CachedDatabase, DeviceProxyCache


db = CachedDatabase(ttl=10)
proxies = DeviceProxyCache()
