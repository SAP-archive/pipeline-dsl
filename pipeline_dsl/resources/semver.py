from pipeline_dsl.resources.resource import AbstractResource, ConcourseResource
from pipeline_dsl.concourse import concourse_context
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import os


class SemVerResource:
    def __init__(self, name: str) -> None:
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self) -> str:
        return self.name

    def version(self) -> str:
        if concourse_context():
            with open(os.path.join(self.path, "version")) as f:
                return f.read().strip()
        return "0.0.1"


class SemVer(AbstractResource[SemVerResource]):
    def __init__(self, driver: "SemVerDriver", initial_version: str = None):
        self.driver = driver
        self.initial_version = initial_version

    def resource_type(self) -> Optional[dict]:
        return None

    def concourse(self, name: str) -> ConcourseResource:
        result = ConcourseResource(
            name=name,
            type="semver",
            icon="creation",
            source=self.driver.concourse(),
        )
        if self.initial_version is not None:
            result.source["initial_version"] = self.initial_version
        return result

    def get(self, name: str) -> SemVerResource:
        return SemVerResource(name)


class SemVerDriver(ABC):
    @abstractmethod
    def concourse(self) -> Dict[str, Any]:
        pass


class SemVerGitDriver(SemVerDriver):
    def __init__(
        self,
        uri: str,
        branch: str,
        file: str,
        private_key: str = None,
        username: str = None,
        password: str = None,
        git_user: str = None,
        depth: str = None,
        skip_ssl_verification: bool = None,
        commit_message: str = None,
    ):
        self.uri = uri
        self.branch = branch
        self.file = file
        self.private_key = private_key
        self.username = username
        self.password = password
        self.git_user = git_user
        self.depth = depth
        self.skip_ssl_verification = skip_ssl_verification
        self.commit_message = commit_message

    def concourse(self) -> Dict[str, Any]:
        result = {
            "driver": "git",
            "uri": self.uri,
            "branch": self.branch,
            "file": self.file,
            "private_key": self.private_key,
            "username": self.username,
            "password": self.password,
            "git_user": self.git_user,
            "depth": self.depth,
            "skip_ssl_verification": self.skip_ssl_verification,
            "commit_message": self.commit_message,
        }

        return dict(
            filter(lambda x: x[1] is not None, result.items()),
        )
