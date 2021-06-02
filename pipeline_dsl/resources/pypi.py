from typing import Optional, Dict
from pipeline_dsl.resources.resource import AbstractResource, ConcourseResource


class PyPi(AbstractResource):
    def __init__(self, name: str, username: str, password: str):
        self.name = name
        self.username = username
        self.password = password

    def resource_type(self) -> Optional[Dict]:
        return {
            "name": "pypi",
            "type": "docker-image",
            "source": {
                "repository": "cfplatformeng/concourse-pypi-resource",
                "tag": "latest",
            },
        }

    def get(self, name: str) -> "PyPi":
        return self

    def concourse(self, name: str) -> ConcourseResource:
        result = ConcourseResource(
            name=name,
            type="pypi",
            icon="language-python",
            source={
                "name": self.name,
                "repository": {
                    "username": self.username,
                    "password": self.password,
                },
            },
        )
        return result
