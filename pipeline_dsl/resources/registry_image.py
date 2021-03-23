import os
from pipeline_dsl.concourse import concourse_context


class RegistryImageResource:
    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self):
        return self.name

    def tag(self, default=None):
        if concourse_context():
            with open(os.path.join(self.path, "tag")) as f:
                return f.read().strip()
        return default


class RegistryImage:
    def __init__(self, repo, username=None, password=None, tag=None, variant=None):
        self.repo = repo
        self.username = username
        self.password = password
        self.tag = tag
        self.variant = variant

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "registry-image",
            "source": {
                "repository": self.repo,
                "username": self.username,
                "password": self.password,
                "tag": self.tag,
                "variant": self.variant,
            },
        }
        result["source"] = dict(
            filter(lambda x: x[1] is not None, result["source"].items()),
        )
        return result

    def get(self, name):
        return RegistryImageResource(name)
