#!/usr/bin/env python3


import yaml
import sys
import os
import json
import shutil

CACHE_DIR = 'tasks'
class Task:
  def __init__(self, name, jobname, timeout, image_resource,script,inputs):
      self.name = name
      self.timeout = timeout
      self.config =  {
        "platform" : "linux",
        "image_resource": image_resource,
        "outputs": [ { "name" : CACHE_DIR} ],
        "inputs": list(map(lambda x: {"name": x}, inputs)) ,
        "run" : {
          "path": "/usr/bin/python3",
          "args" : [ script, jobname , name ],
        }
      }
  def concourse(self):
    return {
      "task" : self.name,
      "timeout" : self.timeout, 
      "config" : self.config,
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
  def dir(self,name):
    return "~/workspace/" + name


class GetTask:
  def __init__(self, name,trigger,resource):
    self.name = name
    self.trigger = trigger
    self.resource = resource
  def concourse(self):
    return {
      "get": self.name,
      "trigger": self.trigger,
    }


class Job:
  def __init__(self, name, script,image_resource,resources):
    self.name = name
    self.plan =  []
    self.last_task = None
    self.image_resource = image_resource
    self.script = script
    self.resources = resources
    self.inputs = []

  def get(self,name,trigger=False):
    resource = self.resources[name]
    self.plan.append(GetTask(name,trigger,resource))
    self.inputs.append(name)
    return resource.dir(name)

  def task(self,name,fun,timeout="5m",image_resource=None,resources=[]):
    if  not image_resource:
      image_resource = self.image_resource
    inputs = self.inputs
    if self.last_task:
      inputs = inputs + [CACHE_DIR]
    self.plan.append(Task(name,self.name,timeout,image_resource,self.script,inputs))
    cache_file = os.path.join(CACHE_DIR, self.name, name + ".json")
    def fn():
      print("Running: {}".format(name))
      os.makedirs(os.path.dirname(cache_file), exist_ok=True)
      try:
        with open(cache_file,'r') as fd:
          return json.load(fd)
      except FileNotFoundError:
        result = fun()
        with open(cache_file,'w') as fd:
          json.dump(result,fd)
        return result
    self.last_task = fn
    return self.last_task

  def concourse(self):
    return {
      "name" : self.name,
      "plan" : list(map(lambda x: x.concourse(), self.plan))
    }
  
  def run(self):
    return self.last_task()



class Pipeline():
  def __init__(self,name,script):
    self.jobs = []
    self.resources = {}
    self.name = name
    self.image_resource = "ci-image"
    self.script = script

  def run(self):
    shutil.rmtree(CACHE_DIR)
    for job in self.jobs:
      job.run()
  
  def job(self,name):
    result = Job(name,self.script,self.image_resource,self.resources)
    self.jobs.append(result)
    return result

  def resource(self,name,resource):
    self.resources[name] = resource

  def concourse(self):
    return {
      "resources" : list(map(lambda kv: kv[1].concourse(kv[0]), self.resources.items())),
      "jobs" : list(map(lambda x: x.concourse(), self.jobs)),
    }


def create_shoot(cluster_name):
  print("Create cluster {}".format(cluster_name))
  return cluster_name

def install_shalm(shalm_dir,create_cluster):
  cluster_name = create_cluster()
  print("Installing shalm {} into {}".format(shalm_dir,cluster_name))
  return "Hello"

def pipeline():
  p = Pipeline("c21s",os.path.basename(__file__))
  p.resource("c21s",GitRepo("https://github.tools.sap/cki/c21s"))
  job = p.job("create-cluster")
  c21s_dir = job.get("c21s")
  task_create_cluster = job.task("create-shoot",lambda : create_shoot("xxx"))
  job.task("install-shalm",lambda : install_shalm(c21s_dir,task_create_cluster))
  return p

p = pipeline()

print(p.run())
yaml.dump(p.concourse(), sys.stdout, allow_unicode=True)
