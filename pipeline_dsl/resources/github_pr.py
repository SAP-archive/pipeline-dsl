import os
import json
from pipeline_dsl.concourse import concourse_context


class GithubPRResource:
    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self):
        return self.name

    def version(self, default=None):
        if concourse_context():
            return json.load(open(os.path.join(self.path, ".git", "resource", "version.json")))
        return default

    def metadata(self, default=None):
        if concourse_context():
            return json.load(open(os.path.join(self.path, ".git", "resource", "metadata.json")))
        return default

    def changed_files(self, default=None):
        if concourse_context():
            with open(os.path.join(self.path, ".git", "resource", "changed_files")) as f:
                lines = f.readlines()
                return [line.strip() for line in lines]
        return default


class GithubPR:
    def __init__(
        self,
        repository,
        access_token,
        v3_endpoint=None,
        v4_endpoint=None,
        paths=None,
        ignore_paths=None,
        disable_ci_skip=None,
        skip_ssl_verification=None,
        disable_forks=None,
        ignore_drafts=None,
        required_review_approvals=None,
        git_crypt_key=None,
        base_branch=None,
        labels=None,
        disable_git_lfs=None,
        states=None,
    ):
        self.repository = repository
        self.access_token = access_token
        self.v3_endpoint = v3_endpoint
        self.v4_endpoint = v4_endpoint
        self.paths = paths
        self.ignore_paths = ignore_paths
        self.disable_ci_skip = disable_ci_skip
        self.skip_ssl_verification = skip_ssl_verification
        self.disable_forks = disable_forks
        self.ignore_drafts = ignore_drafts
        self.required_review_approvals = required_review_approvals
        self.git_crypt_key = git_crypt_key
        self.base_branch = base_branch
        self.labels = labels
        self.disable_git_lfs = disable_git_lfs
        self.states = states

    def resource_type(self):
        return {
            "name": "github-pr",
            "type": "docker-image",
            "source": {
                "repository": "teliaoss/github-pr-resource",
                "tag": "latest",
            },
        }

    def concourse(self, name):
        result = {
            "name": name,
            "type": "github-pr",
            "icon": "source-pull",
            "source": {
                "repository": self.repository,
                "access_token": self.access_token,
                "v3_endpoint": self.v3_endpoint,
                "v4_endpoint": self.v4_endpoint,
                "paths": self.paths,
                "ignore_paths": self.ignore_paths,
                "disable_ci_skip": self.disable_ci_skip,
                "skip_ssl_verification": self.skip_ssl_verification,
                "disable_forks": self.disable_forks,
                "ignore_drafts": self.ignore_drafts,
                "required_review_approvals": self.required_review_approvals,
                "git_crypt_key": self.git_crypt_key,
                "base_branch": self.base_branch,
                "labels": self.labels,
                "disable_git_lfs": self.disable_git_lfs,
                "states": self.states,
            },
        }
        result["source"] = dict(
            filter(lambda x: x[1] is not None, result["source"].items()),
        )
        return result

    def get(self, name):
        return GithubPRResource(name)
