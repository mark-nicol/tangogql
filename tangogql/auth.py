import os
from graphql import GraphQLError
import logging

logger = logging.getLogger('logger')

def authorization(f):
    def wrapper(self, info,*args, **kw):
        config = info.context["config"]
        required_groups = config.required_groups
        client = info.context["client"]
        memberships = client.groups
        if required_groups and not set(required_groups) & set(memberships):
            raise AuthorizationError(f"User {client.user} is not in any of the required groups")
        return f(self, info,*args, **kw)
    return wrapper

def authentication(f):
    def wrapper(self, info,*args, **kw):
        if info.context["client"].user is None:
            raise AuthenticationError("User is not authenticated")
        return f(self, info,*args, **kw)
    return wrapper

class AuthError(GraphQLError):
    pass

class AuthenticationError(AuthError):
    pass
    
class AuthorizationError(AuthError):
    pass
