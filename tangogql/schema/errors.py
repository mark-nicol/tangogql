""" Module containing parser for different error """
import PyTango
from graphql import format_error

class ErrorParser:
    def remove_duplicated_errors(errors):
        seen = set()
        result_set = []
        for message in errors:
                if isinstance(message,dict):
                    t = tuple(message.items())
                else:
                    t = str(e)
                if t not in seen:
                    seen.add(t)
                    result_set.append(message)
        return result_set

    def parse(error):
        message = {}
        if isinstance(error.original_error,(PyTango.ConnectionFailed,PyTango.CommunicationFailed,PyTango.DevFailed)):
            for e in error.original_error.args:
                print(e)
                # rethrow pytango exception might gives an empty DevError
                if e.reason =="":
                    pass
                elif e.reason == "API_CorbaException":
                    pass
                elif e.reason == "":
                    pass
                elif e.reason in ["API_CantConnectToDevice", "API_DeviceTimedOut"]:
                    message["device"] = e.desc.split("\n")[0].split(" ")[-1]
                    message["desc" ] = e.desc.split("\n")[0]
                    message["reason"] = e.reason.split("_")[-1]
                elif e.reason == "API_AttributeFailed":
                    [device,attribute] =  e.desc.split(",")      
                    message["device"] = device.split(" ")[-1]
                    message["attribute"] = attribute.split(" ")[-1]
                elif e.reason == "API_AttrValueNotSet":
                    message["reason"] = e.reason.split("_")[-1]
                    message["field"] = e.desc.split(" ")[1]
                else:
                    message["reason"] = e.reason
                    message["desc"] = e.desc
        else:
            message["reason"] = str(error)
        return message

