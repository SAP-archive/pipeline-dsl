from pipeline_dsl import Pipeline, GitRepo, shell
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

with Pipeline("pipeline-dsl", team="garden", image_resource=DEFAULT_IMAGE) as pipeline:
    repo_url = "git@github.com:SAP/pipeline-dsl.git"
    pipeline.resource(
        "pipeline-dsl",
        GitRepo(repo_url, private_key="((GITHUB_COM_DEPLOY_KEY))", ignore_paths=["concourse/*", "doc/*"], branch="main"),
    )

    pipeline.resource(
        "pipeline-dsl-stable",
        GitRepo(repo_url, private_key="((GITHUB_COM_DEPLOY_KEY))", ignore_paths=["concourse/*"], branch="stable"),
    )

    with pipeline.job("test") as job:
        job.get("pipeline-dsl", trigger=True)

        @job.task()
        def install_and_test():
            shell(["make", "install"], cwd="pipeline-dsl")
            urllib.request.urlretrieve("https://cki-concourse.istio.sapcloud.io/api/v1/cli?arch=amd64&platform=linux", "/usr/bin/fly")
            os.chmod("/usr/bin/fly", stat.S_IEXEC | stat.S_IREAD)
            shell(["make", "test"], cwd="pipeline-dsl")

    with pipeline.job("coverage") as job:
        job.get("pipeline-dsl", trigger=True)

        @job.task()
        def ensure_coverage():
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
