import os
from graphql import GraphQLError


def is_authorized(info):
    if info.context == None:
        return False

    if "user" not in info.context:
        return False

    if info.context["user"] == None:
        return False
    return True

def is_permited(info):
    permissions = []
    permissions.append('KITS')
    required_group = os.environ.get("REQUIREDGROUP", "")
    if required_group and required_group != '':
        permissions.append(required_group)
    memberships = info.context["groups"]
    if memberships == None:
        return False
    else:
        for membership in memberships:
            if membership in permissions:
                return True
    return False

class UserUnauthorizedException(GraphQLError):
    pass
    
class PermissionDeniedException(GraphQLError):
    pass