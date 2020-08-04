# Pypeline

Python DSL for [concourse](https://concourse-ci.org/)


## Installation

```bash
pip install git+https://github.tools.sap/cki/pypeline.git@latest
```

## Example

```python
from pypeline import Pipeline, GitRepo

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

