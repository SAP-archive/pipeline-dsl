#!/usr/bin/env python3

import sys
import os
import json
import shutil
import subprocess
import platform
import base64
import glob
import argparse

CACHE_DIR = 'tasks'
SCRIPT_DIR = 'scripts'
class Task:
  def __init__(self, name, jobname, timeout, image_resource,script,inputs,secrets):
      self.name = name
      self.timeout = timeout
      self.config =  {
        "platform" : "linux",
        "image_resource": image_resource,
        "outputs": [ { "name" : CACHE_DIR} ],
        "inputs": [ { "name" : CACHE_DIR},  { "name" : SCRIPT_DIR} ] + list(map(lambda x: {"name": x}, inputs)) ,
        "params": list(map(lambda kv: { kv[1] : '(({}))'.format(kv[1]) }, secrets.items())),
        "run" : {
          "path": "/usr/bin/python3",
          "args" : [ os.path.join(SCRIPT_DIR,os.path.basename(script)), "--job", jobname , "--task" , name ],
        }
      }
  def concourse(self):
    return {
      "task" : self.name,
      "timeout" : self.timeout, 
      "config" : self.config,
    }

class InitTask:
  def __init__(self,script,image_resource):
      self.script_dir = os.path.dirname(script)
      self.image_resource = image_resource
  def concourse(self):
    if platform.system() == "Darwin":
      tar = "gtar"
    else:
      tar = "tar"
    skip = len(self.script_dir)+1
    files = list(map(lambda x: x[skip:],glob.glob(os.path.join(self.script_dir,'*.py'), recursive=True)))
    cmd = '{tar} cj --sort=name --mtime="UTC 2019-01-01" --owner=root:0 --group=root:0 -b 1 -f - -C {script_dir} {files}'.format(tar=tar,script_dir=self.script_dir,files=" ".join(files))
    data = base64.b64encode(subprocess.check_output(cmd,shell=True)).decode("utf-8") 
    return {
      "task" : "init",
      "config" : {
        "platform" : "linux",
        "image_resource": self.image_resource,
        "outputs": [ { "name" : CACHE_DIR},  { "name" : SCRIPT_DIR} ],
        "run" : {
          "path": "/bin/bash",
          "args" : [ 
            '-ceu', 
            'echo "{data}" | base64 -d | tar -C {script_dir} -xjf -'.format(script_dir=SCRIPT_DIR,data=data),
          ],
        }
      }
    }

class GitRepo:
  def __init__(self, uri):
      self.uri = uri
  def concourse(self,name):
    return {
      "name": name,
      "type": "git",
      "source": {
          "uri" : self.uri,
          "branch": "master",
      }
    }
  def get(self,name):
    return "~/workspace/" + name


class GetTask:
  def __init__(self, name,trigger,passed):
    self.name = name
    self.trigger = trigger
    self.passed = passed
  def concourse(self):
    return {
      "get": self.name,
      "trigger": self.trigger,
      "passed": self.passed,
    }

class ResourceChain:
  def __init__(self,resource):
    self.resource = resource
    self.passed = []

class Job:
  def __init__(self, name, script,image_resource,resource_chains):
    self.name = name
    self.plan =  [ InitTask(script,image_resource)]
    self.last_task = None
    self.image_resource = image_resource
    self.script = script
    self.resource_chains = resource_chains
    self.inputs = []
    self.tasks = {}

  def get(self,name,trigger=True,passed=None):
    resource_chain = self.resource_chains[name]
    if not passed:
      passed = resource_chain.passed.copy()
    self.plan.append(GetTask(name,trigger,passed))
    resource_chain.passed.append(self.name)
    self.inputs.append(name)
    return resource_chain.resource.get(name)

  def task(self,name,timeout="5m",image_resource=None,resources=[],secrets={}):
    if  not image_resource:
      image_resource = self.image_resource
    def decorate(fun):
      self.plan.append(Task(name,self.name,timeout,image_resource,self.script,self.inputs,secrets))
      cache_file = os.path.join(CACHE_DIR, self.name, name + ".json")
      def fn():
        print("Running: {}".format(name))
        kwargs = {}
        for kv in secrets.items():
          kwargs[kv[0]] = os.getenv(kv[1])
          if not kwargs[kv[0]]:
            raise Exception('Secret not available as environment variable "{secret}"'.format(secret=kv[1]))
        result = fun(**kwargs)
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file,'w') as fd:
          json.dump(result,fd)
        return result

      def fn_cached():
        try:
          with open(cache_file,'r') as fd:
            return json.load(fd)
        except FileNotFoundError:
          try:
            return fn()
          except Exception as exc:
            raise exc from None

      
      self.tasks[name] = fn
      self.last_task = fn_cached
      return self.last_task
    return decorate

  def concourse(self):
    return {
      "name" : self.name,
      "plan" : list(map(lambda x: x.concourse(), self.plan))
    }
  
  def run(self):
    return self.last_task()

  def run_task(self,name):
    return self.tasks[name]()


class Pipeline():
  def __init__(self,name,script):
    self.jobs = []
    self.jobs_by_name = {}
    self.resource_chains = {}
    self.name = name
    self.image_resource = {
      "type": "registry-image",
      "source": {
        "repository": "python",
        "tag" : "3.8-buster"
      }
    }
    self.script = script

  def run(self):
    shutil.rmtree(CACHE_DIR,ignore_errors=True)
    for job in self.jobs:
      job.run()

  def run_task(self,job,task):
    self.jobs_by_name[job].run_task(task)

  def job(self,name):
    result = Job(name,self.script,self.image_resource,self.resource_chains)
    self.jobs.append(result)
    self.jobs_by_name[name] = result
    return result

  def resource(self,name,resource):
    self.resource_chains[name] = ResourceChain(resource)

  def concourse(self):
    return {
      "resources" : list(map(lambda kv: kv[1].resource.concourse(kv[0]), self.resource_chains.items())),
      "jobs" : list(map(lambda x: x.concourse(), self.jobs)),
    }
  
  def main(self):
    parser = argparse.ArgumentParser(description='Python concourse interface')
    parser.add_argument('--job',help='name of the job to run')
    parser.add_argument('--task',help='name of the task to run')
    parser.add_argument('--concourse', dest='concourse', action='store_true', help='dump concourse')

    args = parser.parse_args()

    if args.concourse:
      import yaml
      yaml.dump(self.concourse(), sys.stdout, allow_unicode=True)
      # fly -t concourse-sapcloud-garden set-pipeline -c  test.yaml -p "create-cluster"
    elif args.job: 
      print(self.run_task(args.job,args.task))
    else:
      print(self.run())


pipeline = Pipeline("c21s",__file__)
pipeline.resource("shalm",GitRepo("https://github.com/kramerul/shalm"))
job = pipeline.job("create-cluster")
shalm_dir = job.get("shalm")
cluster_name = "xxx"

@job.task("create_shoot")
def create_shoot():
  print("Create cluster {}".format(cluster_name))
  return cluster_name

@job.task("install_shalm",secrets={"home" : "HOME"})
def install_shalm(home=None):
  print(home)
  print("Installing shalm {} into {}".format(shalm_dir,create_shoot()))
  return "Hello"

job = pipeline.job("test-cluster")
shalm_dir = job.get("shalm")

pipeline.main()

