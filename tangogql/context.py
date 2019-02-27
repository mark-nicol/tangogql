import jwt


__all__ = ["build_context"]


class ClientInfo:
    def __init__(self, user, groups):
        if user is not None and type(user) is not str:
            raise TypeError("user must be a string or None")

        if not type(groups) is list:
            raise TypeError("groups must be a list")

        self.user = user
        self.groups = groups


def build_context(request, config):
    try:
        token = request.cookies.get("webjive_jwt", "")
        claims = jwt.decode(token, config.secret)
    except jwt.InvalidTokenError:
        claims = {}

    user = claims.get("username")
    groups = claims.get("groups", [])

    return {
        "client": ClientInfo(user, groups),
        "config": config
    }
