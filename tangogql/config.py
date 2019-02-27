import json


# TODO: required_groups should be renamed to authorized_groups,
# in order not to imply that the user needs to belong to *all*
# of the groups.


class Config:
	def __init__(self, file):
		data = json.load(file)

		try:
			secret = data["secret"]
		except KeyError:
			raise ConfigError("no secret provided")

		if not isinstance(secret, str):
			raise ConfigError("secret must be a string")

		required_groups = data.get("required_groups", [])
		if not all(isinstance(group, str) for group in required_groups):
			raise ConfigError("required_groups must consist of strings")

		self.secret = secret
		self.required_groups = required_groups


class ConfigError(Exception):
	def __init__(self, reason):
		super().__init__(f"Config error: {reason}")
