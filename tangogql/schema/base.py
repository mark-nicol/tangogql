"""Module containing the Base classes for the Tango Schema."""


from tangogql.tangodb import CachedDatabase, DeviceProxyCache
from tangogql.aioattribute import SubscriptionManager

db = CachedDatabase(ttl=10)
proxies = DeviceProxyCache()
subscriptions = SubscriptionManager()
