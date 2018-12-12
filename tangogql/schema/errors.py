""" Module containing parser for different error """
import PyTango
from graphql import format_error
class ErrorParser:
    def parse(error):
        if isinstance(error.original_error,(PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked)):            
            message =  {"message":[{
                                    "desc"    : e.desc.split("\n")[0],   # only the first row contains important info
                                    "reason"  : e.reason,
                                    "severity": e.severity,
                                    "origin"  : e.origin} 
                                    for e in error.original_error.args]
                           
                        }
            return message
        else:
            return format_error(error)