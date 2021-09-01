from pipeline_dsl.resources.resource import AbstractResource, ConcourseResource
from pipeline_dsl.concourse import concourse_context, subprocess
from typing import Optional, Dict
import os


class GitRepoResource:
    def __init__(self, name: str, uri: str, config: dict) -> None:
        self.name = name
        self.config = config
        self.uri = uri
        if concourse_context():
            self.path = os.path.abspath(self.name)
        else:
            self.path = os.getenv("HOME", "") + "/workspace/" + os.path.splitext(os.path.basename(uri))[0]

    def __str__(self) -> str:
        return self.path

    def directory(self) -> str:
        return self.path

    # Always returns the newest tag for the current version
    def tag(self) -> str:
        return subprocess.check_output(["git", "describe", "--tags"], cwd=self.path, stderr=subprocess.DEVNULL).decode("utf-8").strip()

    # Returns one tag for the current version
    def ref(self) -> str:
        if concourse_context():
            with open(os.path.join(self.path, ".git/ref")) as f:
                return f.read().strip()
        try:
            return self.tag()
        except Exception:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.path).decode("utf-8").strip()

    def short_ref(self) -> str:
        if concourse_context():
            with open(os.path.join(self.path, ".git/short_ref")) as f:
                return f.read().strip()
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=self.path).decode("utf-8").strip()


class GitRepo(AbstractResource[GitRepoResource]):
    def __init__(
        self,
        uri: str,
        username: str = None,
        password: str = None,
        branch: str = None,
        paths: list = None,
        ignore_paths: list = None,
        tag_filter: str = None,
        git_config: dict = {},
        private_key: str = None,
        fetch_tags: bool = None,
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self.branch = branch
        self.paths = paths
        self.ignore_paths = ignore_paths
        self.tag_filter = tag_filter
        self.git_config = git_config
        self.private_key = private_key
        self.fetch_tags = fetch_tags

    def resource_type(self) -> Optional[Dict]:
        return None

    def concourse(self, name: str) -> ConcourseResource:
        result = ConcourseResource(
            name=name,
            type="git",
            icon="git",
            source={
                "uri": self.uri,
                "branch": self.branch,
                "username": self.username,
                "password": self.password,
                "paths": self.paths,
                "ignore_paths": self.ignore_paths,
                "tag_filter": self.tag_filter,
                "git_config": list(map(lambda kv: {"name": kv[0], "value": kv[1]}, self.git_config.items())),
                "private_key": self.private_key,
                "fetch_tags": self.fetch_tags,
            },
        )
        result.source = dict(
            filter(lambda x: x[1] is not None, result.source.items()),
        )
        return result

    def get(self, name: str) -> GitRepoResource:
        return GitRepoResource(name, self.uri, self.git_config)
