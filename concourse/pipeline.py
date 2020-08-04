from pypeline import Pipeline, GitRepo, shell

with Pipeline("pypeline") as pipeline:
    pipeline.resource("pypeline", GitRepo("https://github.tools.sap/cki/pypeline",
        username="istio-serviceuser", password="((GITHUB_TOOLS_SAP_TOKEN))", ignore_paths=["concourse/*"]))

    with pipeline.job("test") as job:
        job.get("pypeline", trigger=True)

        @job.task()
        def make_test():
            shell(["make", "test"], cwd="pypeline")
