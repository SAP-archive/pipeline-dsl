---
marp: true
theme: undercover
---

# conpype: a Concourse pipeline DSL

---

## History

### 1. Plain concourse configuration

* Huge configuration files
* Violates "Don't repeat yourself" principle
* Requires "commit before test" in case of modularisation
* No reuse of code accross tasks and jobs
* Linting not possible

<pre style="font-size: 30%; color: green">
task: install
privileged: false
timeout: 5m
config:
  caches: []
  image_resource: ...
  inputs: ...
  outputs: ...
  params:
    REQUESTS_CA_BUNDLE: /etc/ssl/certs/ca-certificates.crt
  platform: linux
  run:
    args:
    - /bin/bash
    - ceu
    - |
      kubectl ...
</pre>

---

### 2. Use ytt

* Huge configuration files
* ~~Violates "Don't repeat yourself" principle~~
* Requires "commit before test" in case of modularisation
* No reuse of code accross tasks and jobs
* Linting not possible
* No local testing

<pre style="font-size: 30%; color: green">
#@ def images_resource()
source:
  repository: python
  tag: 3.8-buster
#@ end
task: install
privileged: false
timeout: 5m
config:
  caches: []
  image_resource: #@ image_resource()
  inputs: ...
  outputs: ...
  params:
    REQUESTS_CA_BUNDLE: /etc/ssl/certs/ca-certificates.crt
  platform: linux
  run:
    args:
    - /bin/bash
    - ceu
    - |
      kubectl ...
</pre>

---

### 3. Package scripts

* Huge configuration files
* ~~Violates "Don't repeat yourself" principle~~
* ~~Requires "commit before test" in case of modularisation~~
* No reuse of code accross tasks and jobs
* Linting not possible
* No local testing

<pre style="font-size: 30%; color: green">
#@ def images_resource()
source:
  repository: python
  tag: 3.8-buster
#@ end
task: install
privileged: false
timeout: 5m
config:
  caches: []
  image_resource: #@ image_resource()
  inputs: ...
  outputs: ...
  params:
    REQUESTS_CA_BUNDLE: /etc/ssl/certs/ca-certificates.crt
    SCRIPTS: |
      QlpoOTFBWSZTWUWSFTsAVFB
  platform: linux
  run:
    args:
    - /bin/bash
    - ceu
    - |
      echo ((SCRIPTS)) | base64 -d | tar -C bin -xvjf -
      bin/install.sh
</pre>

---

### First try to introduce conpype

* First prototype of a python based concourse DSL
* Complex syntax due to missing python decorators
* To much focus on local testing
* Was not considered to ease pipeline development

---

### 4. Move all scripts into separate files

* Huge configuration files
* ~~Violates "Don't repeat yourself" principle~~
* ~~Requires "commit before test" in case of modularisation~~
* **No reuse of code accross tasks and jobs**
* ~~Linting not possible~~
* **No local testing**

<pre style="font-size: 30%; color: green">
#@ def images_resource()
source:
  repository: python
  tag: 3.8-buster
#@ end
task: install
privileged: false
timeout: 5m
config:
  caches: []
  image_resource: #@ image_resource()
  inputs: ...
  outputs: ...
  params:
    REQUESTS_CA_BUNDLE: /etc/ssl/certs/ca-certificates.crt
    SCRIPTS: |
      QlpoOTFBWSZTWUWSFTsAVFB
  platform: linux
  run:
    args:
    - /bin/bash
    - ceu
    - |
      echo ((SCRIPTS)) | base64 -d | tar -C bin -xvjf -
      bin/install.sh
</pre>

---

### 5. Move all scripts back to YAML and run shellcheck

* Huge configuration files
* ~~Violates "Don't repeat yourself" principle~~
* ~~Requires "commit before test" in case of modularisation~~
* No reuse of code accross tasks and jobs
* ~~Linting not possible~~
* No local testing

<pre style="font-size: 30%; color: green">
#@ def images_resource()
source:
  repository: python
  tag: 3.8-buster
#@ end
task: install
privileged: false
timeout: 5m
config:
  caches: []
  image_resource: #@ image_resource()
  inputs: ...
  outputs: ...
  params:
    REQUESTS_CA_BUNDLE: /etc/ssl/certs/ca-certificates.crt
  platform: linux
  run:
    args:
    - /bin/bash
    - ceu
    - |
      kubectl ...
</pre>

---

### 6. Use conpype

* ~~Huge configuration files~~
* ~~Violates "Don't repeat yourself" principle~~
* ~~Requires "commit before test" in case of modularisation~~
* ~~No reuse of code accross tasks and jobs~~
* ~~Linting not possible~~
* ~~No local testing~~

```python
from conpype import *

with Pipeline("cf-for-k8s") as pipeline:
    with pipeline.job("install") as job:
        @job.task()
        def install():
            shell(["kubectl",...])
```

---

# Demo

Install cf-for-k8s

---

## Get repository


```python
from conpype import *

with Pipeline("cf-for-k8s") as pipeline:
    pipeline.resource("cf-for-k8s-scp", GithubToolsRepo("https://github.tools.sap/cki/cf-for-k8s-scp", 
                      branch="release",
                      username="istio-serviceuser",
                      password="((GITHUB_TOOLS_SAP_TOKEN))",
                      git_config={"user.name": "istio-serviceuser", "user.email": "istio@sap.com"}))

    with pipeline.job("install") as job:
        cf_for_k8s = job.get("cf-for-k8s-scp")
```

* Concourse secrets can be used in strings
* Dump concourse pipeline with `./cf-for-k8s.py --dump`
* Upload concourse pipeline with  `./cf-for-k8s.py --target demo`


---

## Reuse: Define class for `github.tools.sap` repository

```python
from conpype import *

class GithubToolsRepo(GitRepo):
    def __init__(self, path, branch="master"):
        super().__init__("https://github.tools.sap" + path,
                         branch= branch,
                         username="istio-serviceuser",
                         password="((GITHUB_TOOLS_SAP_TOKEN))",
                         git_config={"user.name": "istio-serviceuser", "user.email": "istio@sap.com"})

```

---

## Implement a task to install cf-for-k8s

```python
@job.task(secrets={"kubeconfig_content": "DEMO_KUBECONFIG_CONTENT"})
def install(kubeconfig_content):
    kubeconfig = "/tmp/kube.config"
    with open(kubeconfig,"w") as f:
        f.write(kubeconfig_content)
    os.environ["KUBECONFIG"] = kubeconfig
    shell(["shalm", "apply", cf_for_k8s.path])
```

* `job.task` is a python decorator which registers the function `install` as task in the job
* `shell` is a helper function which prints out the command and executes it
* To get the path where a resource is located use `resource.path`
* Secrets are passed as parameters
* Tasks are started in the same sequence as they appear in the source

---

## Complete pipeline definition

```python
from conpype import *


from conpype import *

class GithubToolsRepo(GitRepo):
    def __init__(self, path, branch="master"):
        super().__init__("https://github.tools.sap/" + path,
                         branch= branch,
                         username="istio-serviceuser",
                         password="((GITHUB_TOOLS_SAP_TOKEN))",
                         git_config={"user.name": "istio-serviceuser", "user.email": "istio@sap.com"})

IMAGE_RESOURCE= {"type": "docker-image", "source": 
     {"repository": "gcr.io/sap-se-gcp-istio-dev/ci-image","tag": 
     "latest", "username": "_json_key", "password": "((CONCOURSE_GCR_RO))"}}

with Pipeline("cf-for-k8s", image_resource = IMAGE_RESOURCE) as pipeline:
    pipeline.resource("cf-for-k8s-scp", GithubToolsRepo("cki/cf-for-k8s-scp", branch="0.7"))
    with pipeline.job("install") as job:

      cf_for_k8s = job.get("cf-for-k8s-scp")

      @job.task(secrets={"kubeconfig_content": "DEMO_KUBECONFIG_CONTENT"})
      def install(kubeconfig_content):
        kubeconfig = "/tmp/kube.config"
        with open(kubeconfig,"w") as f:
            f.write(kubeconfig_content)
        os.environ["KUBECONFIG"] = kubeconfig
        shell(["shalm", "apply", cf_for_k8s.path])

```

---

## Local execution

* Resources are taken from `$HOME/workspace/<resource>`. They are not cloned from git
* Secrets are taken from environment variables
* `export DEMO_KUBECONFIG_CONTENT=$(cat /Users/d001323/Downloads/kubeconfig--istio--uli.yml)`
* Run `./cf-for-k8s.py --job install --task install`

---

# Supported features

See [user documentation](https://github.tools.sap/cki/conpype/blob/develop/doc/user.md)

---

## Jobs and Tasks

```python
with pipeline.job("hello-job", timeout="5m") as job:

    @job.task(timeout="90s")
    def hello():
        print("Hello, world!")
```

* All configuration values can be passed as named values (e.g. `timeout`)

---

## Secrets

```python
@job.task(secrets={ "my_secret_arg": "MY_SECRET_IN_SECRET_STORE" })
def hello(my_secret_arg):
  print(f"Secret is {my_secret_arg}") 
```

* Secrets are passed as arguments to the methods if specified in the decorator
* Local execution supports reading the secrets from environment variables or from vault (`--secret-manager vault`)

---

## Resources

```python
with Pipeline("kubernetes") as pipeline:
  pipeline.resource("kubernetes", GitRepo("https://github.com/kubernetes/kubernetes"))
  with pipeline.job("kube-job") as job:
    kubernetes = job.get("kubernetes")

    @job.task()
    def kube_task():
      print(f"Kubernetes workspace path {kubernetes.path}")
      print(f"Kubernetes is on version {kubernetes.ref()}")
```
* You can specify any kind of resources by using the related class
* use `resource = job.get` to clone it into you workspace
* use `resource.path` to get the location of the repository inside you workspace

---

## Custom resources

```python
class Cron:
    def __init__(self,definition):
        self.definition = definition

    def resource_type(self):
        return {
            "name": "cron",
            "type": "docker-image",
            "source": {
                "repository": "phil9909/concourse-cron-resource",
                "tag": "latest",
            }
        }
    def concourse(self, name):
        return {
            "name": name,
            "type": "cron",
            "icon": "clock-outline",
            "source": {
                "cron": self.definition,
                "location": "Europe/Berlin",
            }
        }
```
---

## Passed setting on resources


```python
with Pipeline("cf-for-k8s", image_resource = IMAGE_RESOURCE) as pipeline:
    
    pipeline.resource("cf-for-k8s-scp", GithubToolsRepo("cki/cf-for-k8s-scp", branch="0.7"))
    with pipeline.job("install") as job:
        cf_for_k8s = job.get("cf-for-k8s-scp")

    with pipeline.job("test") as job:
        cf_for_k8s = job.get("cf-for-k8s-scp")

```

* Concourse automatically fills the `passed` definition of resources if they are used in subsequent jobs

---

## Outputs

```python
@job.task(outputs=["out"])
def tag(out):
    with open(os.path.join(out,"tag"), "w") as file:
      file.write("stable-" + datetime.now().isoformat('T'))
```

* Outputs are passed as parameters
* Use the value of the parameter to get the path to the output directory
* In a local environment, this folder will be located in `/tmp/outputs/<job>/<output>`

---

### Put a resource

```python
with pipeline.job("bump-cf4k8s-templates", serial=True) as job:
    job.get("my-repo")

    @job.task(outputs=["publish"], timeout="45m")
    def do_sth_with_repo(publish):
        # Copy my-repo to publish/my-repo
        # Work on publish/my-repo
    
    job.put("my-repo", params={"repository": "publish/my-repo", "rebase": True})
```

---

# Other related projects

* [lss-py](https://github.tools.sap/cki/lss-py/blob/master/product.py)