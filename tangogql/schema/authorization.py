import os
from graphql import GraphQLError


<<<<<<< HEAD
class AuthorizationMiddleware(object):
    def resolve(next,root,info,**args):
        operation = info.operation.operation
        if operation == 'query':
            return next(root,info,**args)

        elif operation == 'subscription':
            return next(root,info,**args)

        elif operation == 'mutation':
            if info.context == None:
                raise UserUnauthorizedException("User Unathorized")
            if "user" not in info.context:
                raise UserUnauthorizedException("User Unathorized")
            if info.context["user"] == None:
                raise UserUnauthorizedException("User Unathorized")
            return next(root,info,**args)
        

class PermissionMiddleware(object):
    def resolve(next,root,info,**args):
        operation = info.operation.operation
        if operation == 'query':
            return next(root,info,**args)

        elif operation == 'subscription':
            return next(root,info,**args)

        elif operation == 'mutation':
            permissions = []
            permissions.append('KITS')
            required_group = os.environ.get("REQUIREDGROUP", "")
            if required_group and required_group != '':
                permissions.append(required_group)
            memberships = info.context["groups"]
            if memberships == None:
                raise PermissionDeniedException("Permission Denied")
            else:
                for membership in memberships:
                    if membership in permissions:
                        return next(root,info,**args)
            raise PermissionDeniedException("Permission Denied")
=======
def is_authorized(info):
    if info.context["client_data"] == None:
        return False

    if "user" not in info.context["client_data"]:
        return False

    if info.context["client_data"]["user"] == None:
        return False
    return True

def is_permited(info):
    required_groups = info.context["config_data"]["required_groups"]
    memberships = info.context["client_data"]["groups"]
    if not memberships:
        return False
    else:
        for membership in memberships:
            if membership in required_groups:
                return True
    return False
>>>>>>> 85ba3e223855844b8f6c45a9ba0f1c97fe4da4b9

class UserUnauthorizedException(GraphQLError):
    pass
    
class PermissionDeniedException(GraphQLError):
    pass