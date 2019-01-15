""" Module containing parser for different error """
import PyTango
from graphql import format_error

class ErrorParser:
    def remove_duplicated_errors(errors):
        result_set = []
        for e in errors:
            if e and e not in result_set:
                result_set.append(e)
        return result_set

    def parse(error):
        message = []
        result = {}
        if isinstance(error.original_error,PyTango.DevFailed):
            for e in error.original_error.args:
                # rethrow pytango exception might gives an empty DevError
                if e.reason =="":
                    pass
                elif e.reason == "API_CorbaException":
                    pass
                elif e.reason in ["API_CantConnectToDevice","API_DeviceTimedOut"]:       
                    message.append({
                                    "device"  : e.desc.split("\n")[0].split(" ")[-1],
                                    "desc"    : e.desc.split("\n")[0],
                                    "reason"  : e.reason.split("_")[-1]
                                    })
                elif e.reason == "API_AttributeFailed":
                    [device,attribute] =  e.desc.split(",")      
                    result["device"] = device.split(" ")[-1]
                    result["attribute"] = attribute.split(" ")[-1]

                elif e.reason == "API_AttrValueNotSet":
                    result["reason"] = e.reason.split("_")[-1]
                    result["field"] = e.desc.split(" ")[1]

                else:
                    message.append(str(e))
            if result:
                message.append(result)
        else:
            # skip all the python build-in exceptions
            pass
        return message

