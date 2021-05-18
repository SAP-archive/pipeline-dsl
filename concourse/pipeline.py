from pipeline_dsl import Pipeline, GitRepo, shell, SemVer, SemVerGitDriver, PyPi
from pipeline_dsl.utils import modify_git_repo
import re
import urllib.request
import os
import stat
import subprocess
import json
import sys

COVERAGE_THRESHOLD = 75
DEFAULT_IMAGE = {
    "type": "docker-image",
    "source": {
        "repository": "gcr.io/sap-se-gcp-istio-dev/ci-image",
        "tag": "latest",
        "username": "_json_key",
        "password": "((IMAGE_PULL_SECRETS))",
    },
}

def update_version(new_version, source, target):
    with modify_git_repo(source, target, "Bump version " + new_version):
      shell(["sed", "-i", 's/version=.*/version="'+new_version+'",/', 'setup.py'])


with Pipeline("pipeline-dsl", team="garden", image_resource=DEFAULT_IMAGE) as pipeline:
    repo_url = "git@github.com:SAP/pipeline-dsl.git"
    pipeline.resource(
        "pipeline-dsl",
        GitRepo(repo_url, private_key="((GITHUB_COM_DEPLOY_KEY))", ignore_paths=["concourse/*", "doc/*"], branch="main", git_config={"user.name": "pipeline-dsl bot", "user.email": "istio@sap.com"}),
    )

    pipeline.resource(
        "pipeline-dsl-stable",
        GitRepo(repo_url, private_key="((GITHUB_COM_DEPLOY_KEY))", ignore_paths=["concourse/*"], branch="stable"),
    )

    pipeline.resource(
        "version",
        SemVer(source=SemVerGitDriver(repo_url, private_key="((GITHUB_COM_DEPLOY_KEY))", branch="version", file="version"), initial_version="0.1.0")
    )

    pipeline.resource(
        "pypi",
        PyPi(name="pipeline-dsl", username="((PYPI_USER.username))", password="((PYPI_USER.password))")
    )

    with pipeline.job("test") as job:
        job.get("pipeline-dsl", trigger=True)

        @job.task()
        def install_and_test():
            shell(["python3", "-m", "pip", "install", "-r", "requirements.txt"], cwd="pipeline-dsl")
            shell(["make", "install"], cwd="pipeline-dsl")
            urllib.request.urlretrieve("https://cki-concourse.istio.sapcloud.io/api/v1/cli?arch=amd64&platform=linux", "/usr/bin/fly")
            os.chmod("/usr/bin/fly", stat.S_IEXEC | stat.S_IREAD)
            shell(["make", "test"], cwd="pipeline-dsl")

    with pipeline.job("coverage") as job:
        job.get("pipeline-dsl", trigger=True)

        @job.task()
        def ensure_coverage():
            shell(["python3", "-m", "pip", "install", "-r", "requirements.txt"], cwd="pipeline-dsl")
            shell(["make", "coverage"], cwd="pipeline-dsl")
            repjson = subprocess.check_output(["coverage", "json", "-o", "-"], cwd="pipeline-dsl")
            report = json.loads(repjson)
            percentage = report["totals"]["percent_covered"]

            print(f"Current coverage: {percentage}")
            if float(percentage) < COVERAGE_THRESHOLD:
                print(f"Coverage below {COVERAGE_THRESHOLD}%! Failing job.")
                sys.exit(1)
            print(f"Coverage over {COVERAGE_THRESHOLD}%! Coverage check passed.")

        job.put("pipeline-dsl-stable", params={"repository": "pipeline-dsl"})

    with pipeline.job("auto-bump-patch") as job:
        with job.in_parallel() as inputs:
            version = inputs.get("version", trigger=True, params={"bump": "patch", "pre": "rc"}, passed=["release"])
            repo = inputs.get("pipeline-dsl", passed=[])

        @job.task(outputs=["repo_out"])
        def set_dev_version(repo_out):
          update_version(re.sub("-rc.*", "-dev", version.version()), repo, repo_out + "/git")

        with job.in_parallel() as outputs:
          outputs.put("version", params={"file": "version/version"})
          outputs.put("pipeline-dsl", params={"repository": "repo_out/git"})

    with pipeline.job("bump-minor") as job:
        with job.in_parallel() as inputs:
            version = inputs.get("version", params={"bump": "minor", "pre": "rc"}, passed=[])
            repo = inputs.get("pipeline-dsl", passed=[])

        @job.task(outputs=["repo_out"])
        def set_dev_version(repo_out):
          update_version(re.sub("-rc.*", "-dev", version.version()), repo, repo_out + "/git")

        with job.in_parallel() as outputs:
          outputs.put("version", params={"file": "version/version"})
          outputs.put("pipeline-dsl", params={"repository": "repo_out/git"})

    with pipeline.job("bump-major") as job:
        with job.in_parallel() as inputs:
            version = inputs.get("version", params={"bump": "major", "pre": "rc"}, passed=[])
            repo = inputs.get("pipeline-dsl", passed=[])

        @job.task(outputs=["repo_out"])
        def set_dev_version(repo_out):
          update_version(re.sub("-rc.*", "-dev", version.version()), repo, repo_out + "/git")

        with job.in_parallel() as outputs:
          outputs.put("version", params={"file": "version/version"})
          outputs.put("pipeline-dsl", params={"repository": "repo_out/git"})

    with pipeline.job("rc") as job:
        with job.in_parallel() as inputs:
            inputs.get("pipeline-dsl", trigger=True, passed=["coverage"])
            inputs.get("version", params={"pre": "rc"}, passed=[])

        job.put("version", params={"file": "version/version"})

    with pipeline.job("release") as job:
        with job.in_parallel() as inputs:
            version = inputs.get("version", params={"bump": "final"}, passed=["rc"])
            repo = inputs.get("pipeline-dsl", passed=["rc"])

        @job.task(outputs=["repo_out"])
        def prepare_repo(repo_out):
          update_version(version.version(), repo, repo_out + "/git")
          shell(["make", "dist"], cwd=repo_out + "/git")

        with job.in_parallel() as outputs:
          outputs.put("pipeline-dsl", params={"repository": "repo_out/git", "tag": "version/version", "tag_prefix": "v"})
          outputs.put("version", params={"file": "version/version"})

        job.put("pypi", params={"glob": "repo_out/git/dist/*.tar.gz"})

        @job.task()
        def verify_publish():
          shell(["pip3", "install", "pipeline-dsl==" + version.version()])

