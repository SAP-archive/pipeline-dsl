#!/usr/bin/env python3

from concourse import Pipeline, GitRepo

pipeline = Pipeline("c21s", __file__)
pipeline.resource("shalm", GitRepo("https://github.com/kramerul/shalm"))
job = pipeline.job("create-cluster")
shalm_dir = job.get("shalm")
cluster_name = "xxx"


@job.task()
def create_shoot():
    print("Create cluster {}".format(cluster_name))
    return cluster_name


@job.task(secrets={"home": "HOME"})
def install_shalm(home=None):
    print("HOME=" + home)
    print("Installing shalm {} into {}".format(shalm_dir, create_shoot()))
    return "Hello"


job = pipeline.job("test-cluster")
shalm_dir = job.get("shalm")

print(pipeline.main())
