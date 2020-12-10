from conpype.resources.pool import Pool
from conpype.resources.gcs import GoogleCloudStorage
from conpype.resources.git import GitRepo
from conpype.resources.github import GithubRelease
from conpype.resources.docker import DockerImage
from conpype.resources.semver import SemVer, SemVerGitDriver
from conpype.resources.cron import Cron
from conpype.resources.registry_image import RegistryImage
from conpype.resources.github_pr import GithubPR

ConcourseLockResource = Pool
GoogleCloudStorageResource = GoogleCloudStorage
