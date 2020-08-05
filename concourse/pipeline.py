from pypeline import Pipeline, GitRepo, shell
import urllib.request
import os
import stat

with Pipeline("pypeline", team="garden") as pipeline:
    pipeline.resource("pypeline", GitRepo("https://github.tools.sap/cki/pypeline",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"]))

    pipeline.resource("pypeline-latest", GitRepo("https://github.tools.sap/cki/pypeline",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"], branch="latest"))

    with pipeline.job("test") as job:
        job.get("pypeline", trigger=True)

        @job.task()
        def install_and_test():
            shell(["make", "install"], cwd="pypeline")
            urllib.request.urlretrieve("https://cki-concourse.istio.sapcloud.io/api/v1/cli?arch=amd64&platform=linux", "/usr/bin/fly")
            os.chmod("/usr/bin/fly", stat.S_IEXEC | stat.S_IREAD)
            shell(["make", "test"], cwd="pypeline")

        job.put("pypeline-latest", params={"repository": "pypeline"})
