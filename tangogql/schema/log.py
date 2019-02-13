from graphene import String, Int, List, Boolean, Field, ObjectType
from tangogql.schema.types import ScalarTypes
from functools import wraps
import re
import fnmatch
import operator
class ActivityLog:
    def __init__(self):
        self._log_container = []

    def put_log(self,time,user, command, device, parameters, before_state = None, after_state = None):
        log = {
                "time": time, 
                "user": user,
                "command": command,
                "device": device,
                "parameters": {k :v for k, v in parameters.items()},
                "before_state": before_state,
                "after_state": after_state
            }
        self._log_container.append(log)

    def get_logs(self, device = "*"):
       
        result = []
        rule = re.compile(fnmatch.translate(device), re.IGNORECASE)
        for log in self._log_container: 
            if rule.match(log["device"]):
                result.append(log)
        result.sort(key = operator.itemgetter('time'), reverse=True)
        return result
    
activity_log = ActivityLog()



