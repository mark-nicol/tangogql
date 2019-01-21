import os
from graphql import GraphQLError


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

class UserUnauthorizedException(GraphQLError):
    pass
    
class PermissionDeniedException(GraphQLError):
    pass