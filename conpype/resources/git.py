import os
from conpype.concourse import concourse_context, subprocess

class GitRepoResource:
    def __init__(self, name):
        self.name = name
        if concourse_context():
            self.path = os.path.abspath(self.name)
        else:
            self.path = os.getenv("HOME") + "/workspace/" + self.name

    def __str__(self):
        return self.directory()

    def directory(self):
        return self.path

    def ref(self):
        if concourse_context():
            with open(os.path.join(self.directory(), ".git/ref")) as f:
                return f.read().strip()
        try:
            return subprocess.check_output(["git", "describe", "--tags"], cwd=self.directory()).decode("utf-8").strip()
        except:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.directory()).decode("utf-8").strip()

    def short_ref(self):
        if concourse_context():
            with open(os.path.join(self.directory(), ".git/short_ref")) as f:
                return f.read().strip()
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=self.directory()).decode("utf-8").strip()


class GitRepo:
    def __init__(self, uri, username=None, password=None, branch=None, ignore_paths=None, tag_filter=None, git_config={}):
        self.uri = uri
        self.username = username
        self.password = password
        self.branch = branch
        self.ignore_paths = ignore_paths
        self.tag_filter = tag_filter
        self.git_config = git_config

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
                "ignore_paths": self.ignore_paths,
                "tag_filter": self.tag_filter,
                "git_config" : list(map(lambda kv: { "name" : kv[0], "value": kv[1]}, self.git_config.items()))
            }
        }
        result["source"] = dict(filter(lambda x: x[1] is not None, result["source"].items()))
        return result

    def get(self, name):
        return GitRepoResource(name)