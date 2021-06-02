from pipeline_dsl.resources.resource import AbstractResource, ConcourseResource
from pipeline_dsl.concourse import concourse_context
from typing import Optional
import os
import re


class GithubReleaseResource:
    def __init__(self, name: str) -> None:
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self) -> str:
        return self.name

    def tag(self, default: str = None) -> Optional[str]:
        if concourse_context():
            with open(os.path.join(self.path, "tag")) as f:
                return f.read().strip()
        return default


class GithubRelease(AbstractResource[GithubReleaseResource]):
    def __init__(
        self,
        owner: str,
        repo: str,
        access_token: str = None,
        pre_release: bool = False,
        release: bool = True,
        github_api_url: str = None,
        github_v4_api_url: str = None,
        github_uploads_url: str = None,
        tag_filter: str = None,
        order_by: str = None,
    ):
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

    def resource_type(self) -> Optional[dict]:
        return None

    def concourse(self, name: str) -> ConcourseResource:
        result = ConcourseResource(
            name=name,
            type="github-release",
            icon="github",
            source={
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
        )
        result.source = dict(
            filter(lambda x: x[1] is not None, result.source.items()),
        )
        return result

    def get(self, name: str) -> GithubReleaseResource:
        return GithubReleaseResource(name)
