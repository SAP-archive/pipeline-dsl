from pipeline_dsl.resources.resource import AbstractResource, ConcourseResource
from pipeline_dsl.concourse import concourse_context
from typing import Optional, Dict
import os


class DockerImageResource:
    def __init__(self, name: str) -> None:
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self) -> str:
        return self.name

    def digest(self) -> str:
        if concourse_context():
            with open(os.path.join(self.path, "digest")) as f:
                return f.read().strip()
        return "latest"


class DockerImage(AbstractResource[DockerImageResource]):
    def __init__(self, repository: str, username: str = None, password: str = None, tag: str = "latest"):
        self.repository = repository
        self.username = username
        self.password = password
        self.tag = tag

    def resource_type(self) -> Optional[Dict]:
        return None

    def concourse(self, name: str) -> ConcourseResource:
        result = ConcourseResource(
            name=name,
            type="docker-image",
            icon="docker",
            source={
                "repository": self.repository,
                "username": self.username,
                "password": self.password,
                "tag": self.tag,
            },
        )
        result.source = dict(
            filter(lambda x: x[1] is not None, result.source.items()),
        )
        return result

    def get(self, name: str) -> DockerImageResource:
        return DockerImageResource(name)
