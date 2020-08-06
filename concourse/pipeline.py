from conpype import Pipeline, GitRepo, shell
import urllib.request
import os
import stat

with Pipeline("conpype", team="garden") as pipeline:
    pipeline.resource("conpype", GitRepo("https://github.tools.sap/cki/conpype",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"], branch="develop"))

    pipeline.resource("conpype-latest", GitRepo("https://github.tools.sap/cki/conpype",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"], branch="latest"))

    with pipeline.job("test") as job:
        job.get("conpype", trigger=True)

        @job.task()
        def install_and_test():
            shell(["make", "install"], cwd="conpype")
            urllib.request.urlretrieve("https://cki-concourse.istio.sapcloud.io/api/v1/cli?arch=amd64&platform=linux", "/usr/bin/fly")
            os.chmod("/usr/bin/fly", stat.S_IEXEC | stat.S_IREAD)
            shell(["make", "test"], cwd="conpype")

        job.put("conpype-latest", params={"repository": "conpype"})
