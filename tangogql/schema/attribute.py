"""Module defining the attributes."""

import PyTango
from graphene import Interface, String, Int

from tangogql.schema.base import proxies
from tangogql.schema.types import TangoNodeType
from tangogql.schema.types import ScalarTypes


class DeviceAttribute(Interface):
    """This class represents an attribute of a device."""

    name = String()
    device = String()
    datatype = String()
    dataformat = String()
    writable = String()
    label = String()
    unit = String()
    description = String()
    value = ScalarTypes()
    writevalue = ScalarTypes()
    quality = String()
    timestamp = Int()
    displevel= String()
    minvalue = ScalarTypes()
    maxvalue = ScalarTypes()
    minalarm = ScalarTypes()
    maxalarm = ScalarTypes()

    def resolve_writevalue(self, *args, **kwargs):
        """This method fetch the coresponding w_value of an attribute bases on its name.

        :return: W Value of the attribute.
        :rtype: Any
        """

        w_value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            if att_data.data_format != 0:  # SPECTRUM and IMAGE
                temp_val = att_data.w_value
                if isinstance(temp_val, tuple):
                    w_value = list(temp_val)
                else:
                    w_value = att_data.w_value.tolist()
            else:  # SCALAR
                w_value = att_data.w_value
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return [e.desc, e.reason]
        except Exception as e:
            return str(e)
        return w_value

    def resolve_value(self, *args, **kwargs):
        """This method fetch the coresponding value of an attribute bases on its name.

        :return: Value of the attribute.
        :rtype: Any
        """

        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            if att_data.data_format != 0:  # SPECTRUM and IMAGE
                temp_val = att_data.value
                if isinstance(temp_val, tuple):
                    value = list(temp_val)
                else:
                    value = att_data.value.tolist()
            else:  # SCALAR
                value = att_data.value
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return [e.desc, e.reason]
        except Exception as e:
            return str(e)
        return value

    def resolve_quality(self, *args, **kwargs):
        """This method fetch the coresponding quality of an attribute bases on its name.

        :return: The quality of the attribute.
        :rtype: str
        """

        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            value = att_data.quality.name
        # TODO: Check this part, don't do anything on an exception?
        # NOTE: Better to propagate SystemExit and KeyboardInterrupt,
        # otherwise Ctrl+C may not work.
        except Exception as e:
            pass
        return value

    def resolve_timestamp(self, *args, **kwargs):
        """This method fetch the timestamp value of an attribute bases on its name.

        :return: The timestamp value
        :rtype: float
        """

        value = None
        try:
            proxy = proxies.get(self.device)
            att_data = proxy.read_attribute(self.name)
            value = att_data.time.tv_sec
        except Exception as e:
            pass
        return value


class ScalarDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass


class ImageDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass


class SpectrumDeviceAttribute(TangoNodeType, interfaces=[DeviceAttribute]):
    pass
