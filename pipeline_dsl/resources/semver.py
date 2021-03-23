import os
from pipeline_dsl.concourse import concourse_context


class SemVerResource:
    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self):
        return self.name

    def version(self):
        if concourse_context():
            with open(os.path.join(self.path, "version")) as f:
                return f.read().strip()
        return "0.0.1"


class SemVer:
    def __init__(self, source, initial_version=None):
        self.source = source
        self.initial_version = initial_version

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "semver",
            "icon": "creation",
            "source": self.source.concourse(),
        }
        if self.initial_version is not None:
            result["source"]["initial_version"] = self.initial_version
        return result

    def get(self, name):
        return SemVerResource(name)


class SemVerGitDriver:
    def __init__(self, uri, branch, file, private_key=None, username=None, password=None, git_user=None, depth=None, skip_ssl_verification=None, commit_message=None):
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

    def resource_type(self):
        return None

    def concourse(self):
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

        return dict(filter(lambda x: x[1] is not None, result.items()))

    def get(self, name):
        return None
