import os
from graphql import GraphQLError


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

class UserUnauthorizedException(GraphQLError):
    pass
    
class PermissionDeniedException(GraphQLError):
    pass