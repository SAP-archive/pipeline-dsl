from pypeline import Pipeline, GitRepo, shell

with Pipeline("pypeline") as pipeline:
    pipeline.resource("pypeline", GitRepo("https://github.tools.sap/cki/pypeline",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"]))

    pipeline.resource("pypeline-latest", GitRepo("https://github.tools.sap/cki/pypeline",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"], branch="latest"))

    with pipeline.job("test") as job:
        job.get("pypeline", trigger=True)

        @job.task()
        def install_and_test():
            shell(["make", "install"], cwd="pypeline")
            shell(["make", "test"], cwd="pypeline")

        job.put("pypeline-latest", params={"repository": "pypeline"})
