import json

class Config:
	def __init__(self, f):
		data = json.load(f)

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
