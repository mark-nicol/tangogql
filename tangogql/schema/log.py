from graphene import String, Int, List, Boolean, Field, ObjectType, Interface
from graphene.types.datetime import DateTime
from tangogql.schema.types import ScalarTypes
from functools import wraps
import re
import fnmatch
import operator

class ActivityLog:
    def __init__(self):
        self._log_container = []

    def put(self,log):
        self._log_container.append(log)

    def get_logs(self, device = "*"):
        result = []
        rule = re.compile(fnmatch.translate(device), re.IGNORECASE)
        for log in self._log_container:
            if rule.match(log.device):
                result.append(log)
        result.sort(key = lambda e: e.timestamp, reverse=True)
        return result
    
activity_log = ActivityLog()

class UserAction(Interface):
    timestamp = DateTime() 
    user = String()
    device = String()

class ExcuteCommandUserAction(ObjectType,interfaces=[UserAction]):
    command = String()
    argin = ScalarTypes()

class SetAttributeValueUserAction(ObjectType,interfaces=[UserAction]):
    name = String()
    value = ScalarTypes()
    before_value = ScalarTypes()
    after_value = ScalarTypes()

class PutDevicePropertyUserAction(ObjectType,interfaces=[UserAction]):
    name = String()
    property_value = List(String)

class DeleteDevicePropertyUserAction(ObjectType,interfaces=[UserAction]):
    name = String()

