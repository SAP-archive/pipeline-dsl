import os
from pipeline_dsl.concourse import concourse_context, subprocess


class GitRepoResource:
    def __init__(self, name, uri, config):
        self.name = name
        self.config = config
        self.uri = uri
        if concourse_context():
            self.path = os.path.abspath(self.name)
        else:
            self.path = os.getenv("HOME") + "/workspace/" + os.path.splitext(os.path.basename(uri))[0]

    def __str__(self):
        return self.path

    def directory(self):
        return self.path

    # Always returns the newest tag for the current version
    def tag(self):
        return subprocess.check_output(["git", "describe", "--tags"], cwd=self.path, stderr=subprocess.DEVNULL).decode("utf-8").strip()

    # Returns one tag for the current version
    def ref(self):
        if concourse_context():
            with open(os.path.join(self.path, ".git/ref")) as f:
                return f.read().strip()
        try:
            return self.tag()
        except Exception:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.path).decode("utf-8").strip()

    def short_ref(self):
        if concourse_context():
            with open(os.path.join(self.path, ".git/short_ref")) as f:
                return f.read().strip()
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=self.path).decode("utf-8").strip()


class GitRepo:
    def __init__(self, uri, username=None, password=None, branch=None, paths=None, ignore_paths=None, tag_filter=None, git_config={}, private_key=None):
        self.uri = uri
        self.username = username
        self.password = password
        self.branch = branch
        self.paths = paths
        self.ignore_paths = ignore_paths
        self.tag_filter = tag_filter
        self.git_config = git_config
        self.private_key = private_key

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "git",
            "icon": "git",
            "source": {
                "uri": self.uri,
                "branch": self.branch,
                "username": self.username,
                "password": self.password,
                "paths": self.paths,
                "ignore_paths": self.ignore_paths,
                "tag_filter": self.tag_filter,
                "git_config": list(map(lambda kv: {"name": kv[0], "value": kv[1]}, self.git_config.items())),
                "private_key": self.private_key,
            },
        }
        result["source"] = dict(filter(lambda x: x[1] is not None, result["source"].items()))
        return result

    def get(self, name):
        return GitRepoResource(name, self.uri, self.git_config)
