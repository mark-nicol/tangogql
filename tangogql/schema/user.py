from graphene import String, Int, List, Boolean, Field, ObjectType
from tangogql.schema.types import ScalarTypes


class ActivityLog:
    def __init__(self):
        self._log_container = {}

    def put(self,user, command, device, parameters):
        log = {
                "command": command,
                "device": device,
                "parameters": {k :v for k, v in parameters.items()}
            }
        if user in self._log_container:
            self._log_container[user].append(log)
        else:
            self._log_container [user] = []
            self._log_container[user].append(log)
    def get(self,user):
        if user not in self._log_container:
            return []
        else: 
            return self._log_container[user]

activity_log = ActivityLog()

class UserLog(ObjectType):
    user = String(user= String())
    log = ScalarTypes()
    def resolve_log(self, info):
        return activity_log.get(self.user)
