from taurus import Attribute, Manager
from taurus.core.taurusbasetypes import TaurusEventType
import PyTango

# Manager().changeDefaultPollingPeriod(1000)


def error_str(err):
    if isinstance(err, PyTango.DevFailed):
        err = err[0]
        return "[{0}] {1}".format(err.reason, err.desc)
    return str(err)


def format_value(value, attr_type):
    if attr_type is PyTango.ArgType.DevState:
        return str(value)
    return value


def format_value_event(evt):
    return {
        "value": format_value(evt.value, evt.type),
        "w_value": format_value(evt.w_value, evt.type),
        "quality": str(evt.quality),
        "time": evt.time.totime()
    }


def format_config_event(evt):
    return {
        'description': evt.description,
        'label': evt.label,
        'unit': evt.unit if evt.unit != "No unit" else "",
        'format': evt.format,
        # ...
    }


# Based on code from the taurus-web project
class TaurusWebAttribute(object):

    def __init__(self, name, callback):
        self.name = name
        self.callback = callback
        self._last_time = 0
        self.last_value_event = None
        self.last_config_event = None
        self.attribute.addListener(self)

    @property
    def attribute(self):
        return Attribute(self.name)

    def eventReceived(self, evt_src, evt_type, evt_value):

        """Transforms the event into a JSON encoded string and sends this
        string into the web socket."""

        action = "CHANGE"
        if evt_type == TaurusEventType.Error:
            action = "ERROR"
            value = error_str(evt_value)
        else:
            if evt_type == TaurusEventType.Config:
                action = "CONFIG"
                value = format_config_event(evt_src)
                self.last_config_event = value
            else:
                self._last_time = evt_value.time.tv_sec
                value = format_value_event(evt_value)
                self.last_value_event = value

        self.write_message({"type": action, "data": {self.name: value}})

    def write_message(self, message):
        print(message)
        self.callback(message)

    def clear(self):
        self.attribute.removeListener(self)

    def __del__(self):
        print("GC", self.name)


