from conpype import Pipeline, GitRepo, shell
import urllib.request
import os
import stat
import subprocess
import json 
import sys

COVERAGE_THRESHOLD = 75 

with Pipeline("conpype", team="garden") as pipeline:
    pipeline.resource("conpype", GitRepo("https://github.tools.sap/cki/conpype",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"], branch="develop"))

    pipeline.resource("conpype-main", GitRepo("https://github.tools.sap/cki/conpype",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"], branch="main"))

    with pipeline.job("test") as job:
        job.get("conpype", trigger=True)

        @job.task()
        def install_and_test():
            shell(["make", "install"], cwd="conpype")
            urllib.request.urlretrieve("https://cki-concourse.istio.sapcloud.io/api/v1/cli?arch=amd64&platform=linux", "/usr/bin/fly")
            os.chmod("/usr/bin/fly", stat.S_IEXEC | stat.S_IREAD)
            shell(["make", "test"], cwd="conpype")
    

    with pipeline.job("coverage") as job:
        job.get("conpype", trigger=True)
        @job.task()
        def ensure_coverage():
            shell(["pip", "install", "coverage"], cwd="conpype")
            shell(["make", "coverage"], cwd="conpype")
            repjson = subprocess.check_output(["coverage", "json", "-o", "-"], cwd="conpype")
            report = json.loads(repjson)
            percentage = report["totals"]["percent_covered"]

            print(f"Current coverage: {percentage}")
            if float(percentage) < COVERAGE_THRESHOLD:
                print(f"Coverage below {COVERAGE_THRESHOLD}%! Failing job.")
                sys.exit(1)
            print(f"Coverage over {COVERAGE_THRESHOLD}%! Coverage check passed.")

        job.put("conpype-main", params={"repository": "conpype"})
