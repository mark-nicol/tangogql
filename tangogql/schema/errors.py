""" Module containing parser for different error """
import PyTango
from graphql import format_error

class ErrorParser:
    def remove_duplicated_errors(errors):
        seen = set()
        result_set = []
        for message in errors:
            
            for e in message:
                if isinstance(e,dict):
                    t = tuple(e.items())
                else:
                    t = tuple(e)
                if t not in seen:
                    seen.add(t)
                    result_set.append(message)
        return result_set

    def parse(error):
        message = []
        result = {}
        if isinstance(error.original_error,(PyTango.ConnectionFailed,PyTango.CommunicationFailed,PyTango.DevFailed)):
            for e in error.original_error.args:
                if e.reason == "API_CorbaException":
                    pass
                if e.reason == "API_CantConnectToDevice":       
                    message.append({
                                    "device"  : e.desc.split("\n")[0].split(" ")[-1],
                                    "desc"    : e.desc.split("\n")[0],
                                    "reason"  : e.reason.split("_")[-1]
                                    })

                if e.reason == "API_AttributeFailed":
                    [device,attribute] =  e.desc.split(",")      
                    result["device"] = device.split(" ")[-1]
                    result["attribute"] = attribute.split(" ")[-1]

                if e.reason == "API_AttrValueNotSet":
                    result["reason"] = e.reason.split("_")[-1]
                    result["field"] = e.desc.split(" ")[1]
            if result:
                message.append(result)
        else:
            message.append(str(error))
        return message

