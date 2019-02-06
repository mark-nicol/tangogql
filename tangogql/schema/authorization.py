import os
from graphql import GraphQLError
import logging
logger = logging.getLogger('logger')

class AuthenticationMiddleware(object): 
    def resolve(next,root,info,**args):
        operation = info.operation.operation
        if operation == 'query':
            return next(root,info,**args)

        elif operation == 'subscription':
            return next(root,info,**args)

        elif operation == 'mutation':
            if info.context == None:
                raise UserUnauthorizedException("User Unathorized")
            if "user" not in info.context["client_data"]:
                raise UserUnauthorizedException("User Unathorized")
            if info.context["client_data"]["user"] in [None,""]:
                raise UserUnauthorizedException("User Unathorized")
            return next(root,info,**args)
        
class AuthorizationMiddleware(object):
    def resolve(next,root,info,**args):
        operation = info.operation.operation
        if operation == 'query':
            return next(root,info,**args)

        elif operation == 'subscription':
            return next(root,info,**args)

        elif operation == 'mutation':
            if "required_groups" not in info.context["config_data"]:
                logger.info("WARNING: required groups is not configured. No permisson check will be applied")
                return next(root,info,**args)
            elif not info.context["config_data"]["required_groups"]:
                logger.info("WARNING: required groups is not configured. No permisson check will be applied")
                return next(root,info,**args)
            else:
                required_group = info.context["config_data"]["required_groups"] 
                memberships = info.context["client_data"]["groups"]
                if memberships == None:
                    raise PermissionDeniedException("Permission Denied")
                else:
                    for membership in memberships:
                        if membership in required_group:
                            return next(root,info,**args)
                raise PermissionDeniedException("Permission Denied")

class UserUnauthorizedException(GraphQLError):
    pass
    
class PermissionDeniedException(GraphQLError):
    pass