from typing import Optional, Dict, Collection
from pipeline_dsl.resources.resource import AbstractResource, ConcourseResource


class Pool(AbstractResource):
    def __init__(self, uri: str, branch: str, pool: str, username: str, password: str):
        self.uri = uri
        self.branch = branch
        self.pool = pool
        self.username = username
        self.password = password

    def resource_type(self) -> Optional[Dict]:
        return {
            "name": "pool-stable",
            "type": "docker-image",
            "source": {
                "repository": "concourse/pool-resource",
                "tag": "1.1.1",
            },
        }

    def get(self, name: str) -> "Pool":
        return self

    def concourse(self, name: str) -> ConcourseResource:
        result = ConcourseResource(
            name=name,
            type="pool-stable",
            icon="lock",
            source={
                "uri": self.uri,
                "branch": self.branch,
                "pool": self.pool,
                "username": self.username,
                "password": self.password,
            },
        )
        return result
