from conpype import *

with Pipeline("kubernetes") as pipeline:
    pipeline.resource("kubernetes", GitRepo("https://github.com/kubernetes/kubernetes"))
   
    with pipeline.job("kube-job") as job:
        kubernetes = job.get("kubernetes")

        @job.task()
        def kube_task():
            print(f"Kubernetes workspace path {kubernetes.path}")
            print(f"Kubernetes is on version {kubernetes.ref()}")
