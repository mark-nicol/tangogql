"""Module containing the Subscription implementation."""

import time
import asyncio
from collections import defaultdict

from graphene import ObjectType, String, Float, Interface, Field, List, Int

from tangogql.schema.types import ScalarTypes
from tangogql.listener import TaurusWebAttribute


class ChangeData(ObjectType):
    value = ScalarTypes()
    w_value = ScalarTypes()
    quality = String()
    time = Float()


class ConfigData(ObjectType):
    description = String()
    label = String()
    unit = String()
    format = String()
    data_format = String()
    data_type = String()


class Event(Interface):
    event_type = String()
    device = String()
    name = String()


class ChangeEvent(ObjectType, interfaces=[Event]):
    data = Field(ChangeData)


class ConfigEvent(ObjectType, interfaces=[Event]):
    data = Field(ConfigData)


# NOTE: Maybe we should agree on having the constants in capitals
# Contains subscribed attributes
change_listeners = {}
config_listeners = {}
clients = []

class Subscription(ObjectType):
    change_event = List(ChangeEvent, models=List(String))
    config_event = List(ConfigEvent, models=List(String))
    unsub_config_event = String(models=List(String))
    unsub_change_event = String(client_id=Int())

    # TODO: documentation missing
    async def resolve_change_event(self, info, models=[]):
        clients.append(True)
        id = len(clients)-1

        keeper = EventKeeper()
        for attr in models:
            listener = change_listeners.get(attr)
            if not listener:
                l = TaurusWebAttribute(attr, keeper)
                change_listeners[attr] = l
            else:
                change_listeners[attr].addKeeper(keeper)

        while clients[id]:
            evt_list = []
            events = keeper.get()
            for event_type, data in events.items():
                for attr_name, value in data.items():
                    device, attr = attr_name.rsplit('/', 1)
                    if event_type == "CHANGE":
                        data = ChangeData(value=value['value'],
                                          w_value=value['w_value'],
                                          quality=value['quality'],
                                          time=value['time'])
                        event = ChangeEvent(event_type=event_type,
                                            device=device,
                                            name=attr,
                                            data=data)
                        evt_list.append(event)
            if evt_list:
                yield evt_list
            await asyncio.sleep(1.0)

        # unsubscribed
        for attr in models:
            l = change_listeners[attr]
            l.removeKeeper(keeper)
        if len(l.keepers) == 0:
            l.clear
            del change_listenere
            del clients[id]


    async def resolve_config_event(self, info, models=[]):
        keeper = EventKeeper()
        for attr in models:
            taurus_attr = TaurusWebAttribute(attr, keeper)
            config_listeners[attr] = taurus_attr

        while config_listeners:
            evt_list = []
            events = keeper.get()
            for event_type, data in events.items():
                for attr_name, value in data.items():
                    device, attr = attr_name.rsplit('/', 1)
                    if event_type == "CONFIG":
                        data = ConfigData(description=value['description'],
                                          label=value['label'],
                                          unit=value['unit'],
                                          format=value['format'],
                                          data_format=value['data_format'],
                                          data_type=value['data_type']
                                    )
                        event = ConfigEvent(event_type=event_type,
                                            device=device,
                                            name=attr,
                                            data=data)
                        evt_list.append(event)
            if evt_list:
                yield evt_list
            await asyncio.sleep(1.0)

    # TODO: documentation missing
    async def resolve_unsub_change_event(self, info, client_id = -1):
        if client_id in range(0,len(clients)):
            if clients[client_id]:
                clients[client_id]= False
            yield "Unsubscribed"
        else:
            yield "This clients_id is not registed"

    async def resolve_unsub_config_event(self, info, models=[]):
        result = []
        if config_listeners:
            for attr in models:
                listener = config_listeners[attr]
                if listener:
                    listener.clear()
                    del config_listeners[attr]
                    result.append(attr)
            yield f"Unsubscribed: {result}"
        else:
            yield "No attribute to unsubscribe"


# Help class
class EventKeeper:
    """A simple wrapper that keeps the latest event values for
    each attribute."""

    def __init__(self):
        self._events = defaultdict(dict)
        self._timestamps = defaultdict(dict)
        self._latest = defaultdict(dict)

    def put(self, model, action, value):
        """Update a model"""
        self._events[action][model] = value
        self._timestamps[action][model] = time.time()

    def get(self):
        """Returns the latest accumulated events"""
        tmp, self._events = self._events, defaultdict(dict)
        for event_type, events in tmp.items():
            self._latest[event_type].update(events)
        return tmp
