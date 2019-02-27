import os
from graphql import GraphQLError
import logging

logger = logging.getLogger('logger')

class AuthenticationMiddleware:
    def resolve(next, root, info, **args):
        if info.operation.operation == 'mutation':
            if info.context["client"].user is None:
                raise AuthenticationError("User is not authenticated")

        return next(root, info, **args)

class AuthorizationMiddleware:
    def resolve(next, root, info, **args):
        if info.operation.operation == 'mutation':
            config = info.context["config"]
            required_groups = config.required_groups

            client = info.context["client"]
            memberships = client.groups

            if required_groups and not set(required_groups) & set(memberships):
                raise AuthorizationError(f"User {client.user} is not in any of the required groups")

        return next(root, info, **args)

class AuthError(GraphQLError):
    pass

class AuthenticationError(AuthError):
    pass
    
class AuthorizationError(AuthError):
    pass
