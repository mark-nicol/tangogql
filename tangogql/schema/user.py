from graphene import String, Int, List, Boolean, Field, ObjectType
from tangogql.schema.types import ScalarTypes
import re
import fnmatch
class ActivityLog:
    def __init__(self):
        self._log_container = []

    def put(self,time,user, command, device, parameters, old_state, new_state):
        log = {
                "time": time, 
                "command": command,
                "device": device,
                "parameters": {k :v for k, v in parameters.items()},
                "before_state": old_state,
                "after_state": new_state
            }
        self._log_container.append(log)
    # def _sort_by_time(self,e):
    #     return e["time"]
    def get_logs(self, pattern = "*"):
        if pattern == "*":
            return self._log_container.sort(key = attrgetter("time"))
        else:
            result = []
            rule = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
            for log in self._log_container: 
                if rule.match(log["device"], pattern):
                    result.append(log)
            return result.sort(key = attrgetter("time"))
    

activity_log = ActivityLog()

# class UserLog(ObjectType):
#     user = String(user= String())
#     logs = ScalarTypes()
#     def resolve_logs(self, info):
#         return activity_log.get(self.user)

class LogMiddleware (object):
    def resolve(next, root, info, **args):
        if info.operation.operation == "mutation":
            print("called log")
            for att in dir(info):
                print (att, getattr(info,att))
            print (args)
            result = next(root,info,**args)
            
            activity_log.put(datetime.now(),info.context["client_data"]["user"],"ExecuteDeviceCommand",device, {"command" : command, "argin": argin}, before_state, after_state)
        else:
            result = next(root,info,**args)
        return result




# OperationDefinition(
# operation='mutation', 
# name=None, 
# variable_definitions=[], 
# directives=[], 
# selection_set=SelectionSet(selections=[Field(alias=None, name=Name(value='putDeviceProperty'),
# arguments=[Argument(name=Name(value='device'),
# value=StringValue(value='sys/tg_test/1')), Argument(name=Name(value='name'), 
# value=StringValue(value='state')),
# Argument(name=Name(value='value'),
# value=StringValue(value='Hej'))], 
# directives=[], 
# selection_set=SelectionSet(selections=[Field(alias=None, name=Name(value='ok'), 
# arguments=[], directives=[], selection_set=None), 
# Field(alias=None, name=Name(value='message'), arguments=[], directives=[], selection_set=None)]))]
# )