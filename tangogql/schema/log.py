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

    def get(self, pattern = "*"):
        result = []
        rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        for log in self._log_container:
            if rule.match(log.device):
                result.append(log)
        result.sort(key = lambda e: e.timestamp, reverse=True)
        return result
    
user_actions = ActivityLog()

class UserAction(Interface):
    timestamp = DateTime() 
    user = String()
    device = String()

class ExcuteCommandUserAction(ObjectType,interfaces=[UserAction]):
    name = String()
    argin = ScalarTypes()

class SetAttributeValueUserAction(ObjectType,interfaces=[UserAction]):
    name = String()
    value = ScalarTypes()
    value_before = ScalarTypes()
    value_after = ScalarTypes()

class PutDevicePropertyUserAction(ObjectType,interfaces=[UserAction]):
    name = String()
    value = ScalarTypes()

class DeleteDevicePropertyUserAction(ObjectType,interfaces=[UserAction]):
    name = String()

