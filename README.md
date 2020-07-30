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


## Users Guide

### Local execution

It's possible to execute each task locally

```
python <pipeline> --job <job> --task <task>
```

In this case 
* all repositories are expected to be located in `$HOME/workspace/<resourcename>`
* all secrets are set as environment variable
* no get actions on resources are executed
* no put actions on resources are executed

### Handling of paths

#### Repositories

To get access to a repository, you need to do the following
* declare the repository as pipeline resource
* use `resource = job.get` to clone it into you workspace
* use `resource.path` to get the location of the repository inside you workspace

```
pipeline.resource("shalm", GitRepo("https://github.com/wonderix/shalm"))
with pipeline.job("create-cluster") as job:
    resource = job.get("resource")

    @job.task()
    def my_task():
        print(resource.path)
```

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

### Reusing code

#### Using libraries

#### Loading code from repositories

#### Using ci-cd image

### Passing resources

It resources are used by different jobs within the same pipeline, `pypeline` automatically adds the required `passed` setting on the resource. It's possible to override this behaviour by explicitly setting the `passed` attribute inside a call to `job.get(...,passed=[...])`

### Calling other tasks

This feature is currently not available