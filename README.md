# Pypeline

Python DSL for [concourse](https://concourse-ci.org/)


## Installation

Currently, there is no pypi repository avaialable within SAP. Therefore, installation must be done manually

```bash
git clone https://github.tools.sap/cki/pypeline.git
cd pypeline
make install
```

## Example

```python
from pypeline import Pipeline, GitRepo

with Pipeline("c21s", __file__) as pipeline:
    pipeline.resource("shalm", GitRepo("https://github.com/wonderix/shalm"))
    with pipeline.job("create-cluster") as job:
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
```


## Users Guide

### Local execution

It's possible to execute each task locally

```
python <pipeline> --job <job> --task <task>
```

In this case 
* all repositories are expected to be located in `$HOME/workspace/<resourcename>`
* all secrets are set as environment variable
* no put actions are executed

### Handling of paths

#### Repositories

#### Outputs

You can use output folders for your tasks. Therefore, you can use the `outputs` parameter passed to the `task` decoration. For each declared output, a parameter is passed to your task function. You should use this parameter get the location of the output folder.

In a local environment, this folder will be located in `/tmp/outputs/<job>/<output>`. If running inside concourse, this path will be located inside your workspace.

```
@job.task(outputs=["out"])
def tag(out):
    with open(os.path.join(out,"tag"), "w") as file:
      file.write("stable-" + datetime.now().isoformat('T'))
```

### Using secret manager

You can use values provided by the concourse secret manager as input variable to you task function. Therefore, you can pass the `secrets` parameter to the `task` decorator. Inside the `secret` parameter you can pass the name of the passed parameter as key and the name of the secret as value.

In a local environment the secret values are taken from environment variables.

```
@job.task(secrets={"secret": "SECRET"})
def mytask(home=None):
    print("SECRET=" + secret)
```