import sys
import os
import json
import shutil
import subprocess
import platform
import base64
import argparse
import glob
import inspect
from collections import OrderedDict

from .__shared import CACHE_DIR
from .job import Job

class Pipeline():
    def __init__(self, name, image_resource={"type": "registry-image", "source": {"repository": "python", "tag": "3.8-buster"}}, script_dirs=[], team="main"):
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        self.script = module.__file__
        self.py_dirs = [os.path.dirname(self.script), os.path.dirname(os.path.dirname(os.path.dirname(__file__)))]
        self.script_dirs = []
        for script in script_dirs:
            self.script_dirs.append(os.path.realpath(script))
        self.jobs = []
        self.jobs_by_name = {}
        self.resource_chains = {}
        self.resource_types = {}
        self.name = name
        self.image_resource = image_resource
        self.team = team

    def path_append(self, dir):
        self.py_dirs.append(dir)
        sys.path.append(dir)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.main()

    def run(self):
        shutil.rmtree(CACHE_DIR, ignore_errors=True)
        for job in self.jobs:
            job.run()

    def run_task(self, job, task):
        if job in self.jobs_by_name:
            self.jobs_by_name[job].run_task(task)
        else:
            raise Exception("Job " + job + " not found. List of available jobs: " +
                            " ".join(list(self.jobs_by_name.keys())))

    def job(self, name, serial=False):
        result = Job(name, self.script, self.script_dirs, self.py_dirs, self.image_resource,
                     self.resource_chains, serial=serial)
        self.jobs.append(result)
        self.jobs_by_name[name] = result
        return result

    def resource(self, name, resource):
        self.resource_chains[name] = ResourceChain(resource)
        self.resource_types[resource.__class__.__name__] = resource

    def concourse(self):
        return {
            "pipeline_metadata": {
                "name": self.name,
                "team": self.team,
            },
            "resource_types": list(filter(lambda x: x, map(lambda kv: kv[1].resource_type(), self.resource_types.items()))),
            "resources": list(map(lambda kv: kv[1].resource.concourse(kv[0]), self.resource_chains.items())),
            "jobs": list(map(lambda x: x.concourse(), self.jobs)),
        }

    def main(self):
        parser = argparse.ArgumentParser(
            description='Python concourse interface')
        parser.add_argument('--job', help='name of the job to run')
        parser.add_argument('--task', help='name of the task to run')
        parser.add_argument('--target', help='upload concourse yaml to the given target')
        parser.add_argument('--dump', dest='dump',
                            action='store_true', help='dump concourse yaml')

        args = parser.parse_args()

        if args.dump:
            import yaml
            yaml.dump(self.concourse(), sys.stdout, allow_unicode=True)
            # fly -t concourse-sapcloud-garden set-pipeline -c  test.yaml -p "create-cluster"
        elif args.target:
            import yaml
            config_file = f"/tmp/{self.name}.yaml"
            with open(config_file,"w") as f:
                yaml.dump(self.concourse(), f, allow_unicode=True)
            subprocess.run(["fly", "-t", args.target, "set-pipeline", "-c", config_file, "-p", self.name, "-n"], check=True)
        elif args.job:
            print(self.run_task(args.job, args.task))
        else:
            print(self.run())

class ResourceChain:
    def __init__(self, resource):
        self.resource = resource
        self.passed = []
