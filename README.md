![](https://img.shields.io/badge/STATUS-NOT%20CURRENTLY%20MAINTAINED-red.svg?longCache=true&style=flat)

# Important Notice
This public repository is read-only and no longer maintained.

# Pipeline DSL for [Concourse](https://concourse-ci.org/) 

[![downloads](https://static.pepy.tech/badge/pipeline-dsl/month)](https://pypi.org/project/pipeline-dsl/)
[![python](https://img.shields.io/badge/python-3.7-blue.svg)](https://pypi.org/project/pipeline-dsl/)
[![pypi](https://img.shields.io/pypi/v/pipeline-dsl.svg)](https://pypi.org/project/pipeline-dsl/)
[![license](https://img.shields.io/pypi/l/pipeline-dsl.svg)](https://pypi.org/project/pipeline-dsl/)

## Features

* Develop complete Concourse pipelines in plain Python
* Test Pipelines inside Concourse without pushing them to github 
* Test Pipelines locally


## Installation

Installation from [PyPI](https://pypi.org/project/pipeline-dsl/)
```bash
pip3 install pipeline-dsl
```

Installation from GitHub
```bash
pip3 install --upgrade git+https://github.com/sap/pipeline-dsl.git@main
```

## Example

```python
from pipeline_dsl import Pipeline, GitRepo

with Pipeline("c21s") as pipeline:
    pipeline.resource("shalm", GitRepo("https://github.com/wonderix/shalm"))
    with pipeline.job("create-cluster") as job:
        shalm = job.get("shalm")
        cluster_name = "test"

        @job.task()
        def create_shoot():
            print(f"Create cluster {cluster_name}")
            return cluster_name

        @job.task(secrets={"home": "HOME"})
        def install_shalm(home=None):
            print("HOME=" + home)
            print(f"Installing shalm {shalm.path} into {create_shoot()}")
            return "Hello"
```


## Documentation

* [Users guide](/doc/user.md)
* [Reference guide](/doc/reference.md)
* [Contribution guidelines](/doc/contributing.md)
* [Examples](examples)

