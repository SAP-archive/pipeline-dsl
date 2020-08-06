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
    def __init__(self, uri, username=None, password=None, branch=None, ignore_paths=None, tag_filter=None):
        self.uri = uri
        self.username = username
        self.password = password
        self.branch = branch
        self.ignore_paths = ignore_paths
        self.tag_filter = tag_filter

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "git",
            "icon": "git",
            "source": {
                "uri": self.uri,
                **({"branch": self.branch} if self.branch is not None else {}),
                **({"username": self.username} if self.username is not None else {}),
                **({"password": self.password} if self.password is not None else {}),
                **({"ignore_paths": self.ignore_paths} if self.ignore_paths is not None else {}),
                **({"tag_filter": self.tag_filter} if self.ignore_paths is not None else {}),
            }
        }
        return result

    def get(self, name):
        return GitRepoResource(name)