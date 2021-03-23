import os
from pipeline_dsl.concourse import concourse_context


class DockerImageResource:
    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self):
        return self.name

    def digest(self):
        if concourse_context():
            with open(os.path.join(self.path, "digest")) as f:
                return f.read().strip()
        return "latest"


class DockerImage:
    def __init__(self, repository, username=None, password=None, tag="latest"):
        self.repository = repository
        self.username = username
        self.password = password
        self.tag = tag

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "docker-image",
            "icon": "docker",
            "source": {
                "repository": self.repository,
                "username": self.username,
                "password": self.password,
                "tag": self.tag,
            },
        }
        result["source"] = dict(filter(lambda x: x[1] is not None, result["source"].items()))
        return result

    def get(self, name):
        return DockerImageResource(name)
