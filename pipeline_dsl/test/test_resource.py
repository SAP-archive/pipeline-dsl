import unittest
import os
from pipeline_dsl.resources import GitRepo, Cron, DockerImage, GoogleCloudStorage, Pool, GithubRelease, SemVer, SemVerGitDriver, RegistryImage, GithubPR
from pipeline_dsl.concourse.__shared import concourse_ctx


class TestGitResource(unittest.TestCase):
    def test_basic(self):
        repo = GitRepo("https://example.com/repo.git", git_config={"user.name": "unknown", "user.email": "unknown@example.com"})

        obj = repo.concourse(name="test")
        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "git",
                "icon": "git",
                "source": {
                    "uri": "https://example.com/repo.git",
                    "git_config": [
                        {
                            "name": "user.name",
                            "value": "unknown",
                        },
                        {
                            "name": "user.email",
                            "value": "unknown@example.com",
                        },
                    ],
                },
            },
        )

    def test_path(self):
        with concourse_ctx(False):
            repo = GitRepo("https://example.com/repo.git", git_config={"user.name": "unknown", "user.email": "unknown@example.com"})
            self.assertEqual(repo.get("xxx").path, os.path.join(os.environ["HOME"], "workspace", "repo"))


class TestCronResource(unittest.TestCase):
    def test_basic(self):
        repo = Cron("definition")

        obj = repo.concourse("test")
        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "cron",
                "icon": "clock-outline",
                "source": {
                    "cron": "definition",
                    "location": "Europe/Berlin",
                },
            },
        )

        obj = repo.resource_type()
        self.assertDictEqual(
            obj,
            {
                "name": "cron",
                "type": "docker-image",
                "source": {
                    "repository": "phil9909/concourse-cron-resource",
                    "tag": "latest",
                },
            },
        )


class TestDockerImageResource(unittest.TestCase):
    def test_basic(self):
        resource = DockerImage("repo", "username", "password", "tag")

        obj = resource.concourse("test")
        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "docker-image",
                "icon": "docker",
                "source": {
                    "repository": "repo",
                    "username": "username",
                    "password": "password",
                    "tag": "tag",
                },
            },
        )

        location = resource.get("test")
        self.assertEqual(location.digest(), "latest")


class TestGoogleCloudStorageResource(unittest.TestCase):
    def test_basic(self):
        resource = GoogleCloudStorage("bucket", "regexp", "credentials")

        obj = resource.concourse("test")
        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "gcs",
                "icon": "file-cloud",
                "source": {
                    "bucket": "bucket",
                    "regexp": "regexp",
                    "json_key": "credentials",
                },
            },
        )

        self.assertDictEqual(
            resource.resource_type(),
            {
                "name": "gcs",
                "type": "docker-image",
                "source": {
                    "repository": "frodenas/gcs-resource",
                    "tag": "latest",
                },
            },
        )


class TestPoolResource(unittest.TestCase):
    def test_basic(self):
        resource = Pool("uri", "branch", "pool", "username", "password")

        obj = resource.concourse("test")
        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "pool-stable",
                "icon": "lock",
                "source": {
                    "uri": "uri",
                    "branch": "branch",
                    "pool": "pool",
                    "username": "username",
                    "password": "password",
                },
            },
        )

        self.assertDictEqual(
            resource.resource_type(),
            {
                "name": "pool-stable",
                "type": "docker-image",
                "source": {
                    "repository": "concourse/pool-resource",
                    "tag": "1.1.1",
                },
            },
        )


class TestGithubResource(unittest.TestCase):
    def test_basic(self):
        resource = GithubRelease("owner", "repo", "access_token", pre_release=True, release=False, github_api_url="github_api_url/v3", github_uploads_url="github_uploads_url")

        obj = resource.concourse("test")
        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "github-release",
                "icon": "github",
                "source": {
                    "owner": "owner",
                    "repository": "repo",
                    "access_token": "access_token",
                    "pre_release": True,
                    "release": False,
                    "github_api_url": "github_api_url/v3",
                    "github_v4_api_url": "github_api_url/graphql",
                    "github_uploads_url": "github_uploads_url",
                },
            },
        )


class TestSemVerResource(unittest.TestCase):
    def test_private_key(self):
        resource = SemVer(
            SemVerGitDriver(
                "git@github.com:concourse/concourse.git",
                "version",
                "version-file",
                private_key="testkey",
                username="user",
                git_user="git_user",
                depth=1,
                skip_ssl_verification=True,
                commit_message="Commit Message",
            )
        )
        obj = resource.concourse("test")

        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "semver",
                "icon": "creation",
                "source": {
                    "driver": "git",
                    "uri": "git@github.com:concourse/concourse.git",
                    "branch": "version",
                    "file": "version-file",
                    "private_key": "testkey",
                    "username": "user",
                    "depth": 1,
                    "git_user": "git_user",
                    "skip_ssl_verification": True,
                    "commit_message": "Commit Message",
                },
            },
        )

    def test_password(self):
        resource = SemVer(
            SemVerGitDriver(
                "git@github.com:concourse/concourse.git",
                "version",
                "version-file",
                password="pw",
                username="user",
                git_user="git_user",
                depth=1,
                skip_ssl_verification=True,
                commit_message="Commit Message",
            )
        )
        obj = resource.concourse("test")

        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "semver",
                "icon": "creation",
                "source": {
                    "driver": "git",
                    "uri": "git@github.com:concourse/concourse.git",
                    "branch": "version",
                    "file": "version-file",
                    "password": "pw",
                    "username": "user",
                    "depth": 1,
                    "git_user": "git_user",
                    "skip_ssl_verification": True,
                    "commit_message": "Commit Message",
                },
            },
        )


class TestRegistryImageResource(unittest.TestCase):
    def test_basic(self):
        resource = RegistryImage("repo", "user", "password", "tag", "variant")

        obj = resource.concourse("test")

        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "registry-image",
                "source": {
                    "repository": "repo",
                    "username": "user",
                    "password": "password",
                    "tag": "tag",
                    "variant": "variant",
                },
            },
        )


class TestGithubPRResource(unittest.TestCase):
    def test_basic(self):
        resource = GithubPR("torvalds/linux", "((GITHUB_TOKEN))", skip_ssl_verification=True, v3_endpoint="https://api.example.com")

        obj = resource.concourse("test")

        self.assertDictEqual(
            obj,
            {
                "name": "test",
                "type": "github-pr",
                "icon": "source-pull",
                "source": {
                    "repository": "torvalds/linux",
                    "access_token": "((GITHUB_TOKEN))",
                    "skip_ssl_verification": True,
                    "v3_endpoint": "https://api.example.com",
                },
            },
        )


if __name__ == "__main__":
    unittest.main()

# run > python3 -munittest in main pipeline-dsl dir to execute
