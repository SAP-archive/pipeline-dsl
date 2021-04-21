from pipeline_dsl.resources.pool import Pool
from pipeline_dsl.resources.gcs import GoogleCloudStorage
from pipeline_dsl.resources.git import GitRepo
from pipeline_dsl.resources.github import GithubRelease
from pipeline_dsl.resources.docker import DockerImage
from pipeline_dsl.resources.semver import SemVer, SemVerGitDriver
from pipeline_dsl.resources.cron import Cron
from pipeline_dsl.resources.registry_image import RegistryImage
from pipeline_dsl.resources.github_pr import GithubPR
from pipeline_dsl.resources.pypi import PyPi

ConcourseLockResource = Pool
GoogleCloudStorageResource = GoogleCloudStorage
