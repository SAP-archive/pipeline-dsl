import sys
import os
import json
import shutil
import subprocess
import platform
import base64
import glob
import argparse
import inspect
from collections import OrderedDict
from pypeline.concourse import *

class ConcourseLockResource:
    def __init__(self, uri, branch, pool, username, password):
        self.uri = uri
        self.branch = branch
        self.pool = pool
        self.username = username
        self.password = password

    def resource_type(self):
        return {
            "name": "pool_stable",
            "type": "docker-image",
            "source": {
                "repository": "concourse/pool-resource",
                "tag": "1.1.1",
            }
        }

    def get(self, name):
        return self

    def concourse(self, name):
        result = {
            "name": name,
            "type": "pool_stable",
            "icon": "lock",
            "source": {
                "uri": self.uri,
                "branch": self.branch,
                "pool": self.pool,
                "username": self.username,
                "password": self.password,
            }
        }
        return result


class GoogleCloudStorageResource:
    def __init__(self, bucket, regexp, credentials):
        self.bucket = bucket
        self.regexp = regexp
        self.credentials = credentials

    def resource_type(self):
        return {
            "name": "gcs",
            "type": "docker-image",
            "source": {
                "repository": "frodenas/gcs-resource",
                "tag": "latest",
            }
        }

    def get(self, name):
        return self
    
    def concourse(self, name):
        result = {
            "name": name,
            "type": "gcs",
            "icon": "file-cloud",
            "source": {
                "bucket": self.bucket,
                "regexp": self.regexp,
                "json_key": self.credentials,
            }
        }
        return result

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


class GitRepo:
    def __init__(self, uri, username=None, password=None, branch="master", ignore_paths=None, tag_filter=None):
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
                "branch": self.branch,
                "username": self.username,
                "password": self.password,
                "ignore_paths": self.ignore_paths,
                "tag_filter": self.tag_filter,
            }
        }
        return result

    def get(self, name):
        return GitRepoResource(name)


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
    def __init__(self, owner, repo, access_token=None, pre_release=False, release=True):
        self.owner = owner
        self.repo = repo
        self.access_token = access_token
        self.pre_release = pre_release
        self.release = release

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
            }
        }
        return result

    def get(self, name):
        return GithubReleaseResource(name)


class DockerImageResource:
    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self):
        return self.name

    def digest(self):
        if concourse_context():
            with open(os.path.join(self.path, "digest")) as f:
                return f.read().strip()
        return "latest"

class DockerImage:
    def __init__(self, repository, username=None, password=None, tag="latest"):
        self.repository = repository
        self.username = username
        self.password = password
        self.tag = tag

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "docker-image",
            "icon": "docker",
            "source": {
                "repository": self.repository,
                "username": self.username,
                "password": self.password,
                "tag": self.tag
            }
        }
        return result

    def get(self, name):
        return DockerImageResource(name)
    

class Cron:
    def __init__(self,definition):
        self.definition = definition

    def resource_type(self):
        return {
            "name": "cron",
            "type": "docker-image",
            "source": {
                "repository": "phil9909/concourse-cron-resource",
                "tag": "latest",
            }
        }
    def concourse(self, name):
        return {
            "name": name,
            "type": "cron",
            "icon": "clock-outline",
            "source": {
                "cron": self.definition,
                "location": "Europe/Berlin",
            }
        }

    def get(self, name):
        return None
