#!/usr/bin/env python3


import yaml
import sys
import os

class Task(yaml.YAMLObject):
    yaml_tag = u'!Task'
    def __init__(self, name, timeout, image_resource,script):
        self.task = name
        self.timeout = timeout
        self.config =  {
          "platform" : "linux",
          "image_resource": image_resource,
          "run" : {
            "path": "/usr/bin/python3",
            "args" : script,
          }
        }

def noop(self, *args, **kw):
    pass




class Pipeline():
  def __init__(self,name,script):
    self.steps = []
    self.name = name
    self.last_task = None
    self.image_resource = "ci-image"
    self.script = script


  def task(self,name,fun,timeout="5m",image_resource=None,resources=[]):
    if  not image_resource:
      image_resource = self.image_resource
    self.steps.append(Task(name,timeout,image_resource,self.script))
    def fn():
      print("Running: {}".format(name))
      return fun()
    self.last_task = fn
    return self.last_task

  def run(self):
    return self.last_task()

  def concourse(self):
    yaml.emitter.Emitter.process_tag = noop
    yaml.dump({"plan": self.steps}, sys.stdout, allow_unicode=True)


def create_cluster(cluster_name):
  print("Create cluster {}".format(cluster_name))
  return cluster_name

def install_shalm(shalm_dir,create_cluster):
  cluster_name = create_cluster()
  print("Installing shalm {} into {}".format(shalm_dir,cluster_name))
  return "Hello"

def pipeline(shalm_dir):
  p = Pipeline("create-cluster",os.path.basename(__file__))
  task_create_cluster = p.task("create-cluster",lambda : create_cluster("xxx"))
  p.task("install-shalm",lambda : install_shalm(shalm_dir,task_create_cluster))
  return p

p = pipeline("shalm_dir")

print(p.run())
p.concourse()