""" Module containing parser for different error """
import PyTango
from graphql import format_error

class ErrorParser:
    def filter_error(errors):
        seen = set()
        result_set = []
        for message in errors:
            duplicated = False
            for e in message:
                t = tuple(e.items())
                print(t)
                print(t not in seen)
                if t not in seen:
                    seen.add(t)
                    result_set.append(message)
        return result_set


    def parse(error):
        if isinstance(error.original_error,(PyTango.ConnectionFailed,PyTango.CommunicationFailed, PyTango.DevFailed)):
            message =[]
            for e in error.original_error.args:
                if not e.reason == "API_CorbaException":       
                    message.append({
                                    "device"  : e.desc.split("\n")[0].split(" ")[-1],
                                    "desc"    : e.desc.split("\n")[0],
                                    "reason"  : e.reason.split("_")[-1]
                                    })
            return message
        else:
            return str(error)

