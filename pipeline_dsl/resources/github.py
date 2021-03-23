import os
import re
from pipeline_dsl.concourse import concourse_context


class GithubReleaseResource:
    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self):
        return self.name

    def tag(self, default=None):
        if concourse_context():
            with open(os.path.join(self.path, "tag")) as f:
                return f.read().strip()
        return default


class GithubRelease:
    def __init__(self, owner, repo, access_token=None, pre_release=False, release=True, github_api_url=None, github_v4_api_url=None, github_uploads_url=None, tag_filter=None, order_by=None):
        self.owner = owner
        self.repo = repo
        self.access_token = access_token
        self.pre_release = pre_release
        self.release = release
        self.github_api_url = github_api_url
        self.github_v4_api_url = github_v4_api_url
        if github_api_url and not github_v4_api_url:
            self.github_v4_api_url = re.sub(r"/v[0-9]/*", "/graphql", github_api_url)
        self.github_uploads_url = github_uploads_url
        self.tag_filter = tag_filter
        self.order_by = order_by

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "github-release",
            "icon": "github",
            "source": {
                "owner": self.owner,
                "repository": self.repo,
                "access_token": self.access_token,
                "pre_release": self.pre_release,
                "release": self.release,
                "github_api_url": self.github_api_url,
                "github_v4_api_url": self.github_v4_api_url,
                "github_uploads_url": self.github_uploads_url,
                "tag_filter": self.tag_filter,
                "order_by": self.order_by,
            },
        }
        result["source"] = dict(filter(lambda x: x[1] is not None, result["source"].items()))
        return result

    def get(self, name):
        return GithubReleaseResource(name)
