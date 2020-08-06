
import sys
import os
import json
import shutil
import subprocess
import platform
import base64
import glob
import inspect
from collections import OrderedDict

from .__shared import concourse_context
from .task import InitTask, Task


class Job:
    def __init__(self, name, script, init_dirs, image_resource, resource_chains, serial):
        self.name = name
        self.plan = [InitTask(init_dirs, image_resource)]
        self.image_resource = image_resource
        self.resource_chains = resource_chains
        self.script = script
        self.inputs = []
        self.tasks = OrderedDict()
        self.serial = serial
        self.on_failure = None
        self.on_abort = None
        self.ensure = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        return None

    def get(self, name, trigger=False, passed="auto", params=None):
        resource_chain = self.resource_chains.get(name,None)
        if not resource_chain:
            raise Exception("Resource " + name + " not configured for pipeline")
        if passed == "auto":
            passed = resource_chain.passed.copy()
        self.plan.append(GetStep(name, trigger, passed, params))
        resource_chain.passed.append(self.name)
        self.inputs.append(name)
        return resource_chain.resource.get(name)

    def put(self, name, params=None):
        resource_chain = self.resource_chains.get(name,None)
        if not resource_chain:
            raise Exception("Resource " + name + " not configured for pipeline")
        self.plan.append(PutStep(name, params))
        resource_chain.passed.append(self.name)
        self.inputs.append(name)
        return resource_chain.resource.get(name)

    def task(self, timeout="5m", privileged=False, image_resource=None, resources=[], secrets={}, outputs=[], attempts=1, caches=[], name=None):
        if not image_resource:
            image_resource = self.image_resource

        def decorate(fun):
            task = Task(fun, self.name, timeout, privileged, image_resource, self.script, self.inputs, outputs, secrets, attempts, caches, name)
            self.plan.append(task)
            self.tasks[task.name] = task
            return task.fn_cached
        return decorate

    def in_parallel(self, fail_fast=False):
        parallel_task = ParallelStep(self, fail_fast)
        self.plan.append(parallel_task)
        return parallel_task

    def concourse(self):
        obj = {
            "name": self.name,
            "plan": list(map(lambda x: x.concourse(), self.plan)),
            "serial": self.serial
        }
        if self.on_failure:
            obj['on_failure'] = self.on_failure.concourse()
        if self.on_abort:
            obj['on_abort'] = self.on_abort.concourse()
        if self.ensure:
            obj['ensure'] = self.ensure.concourse()
        return obj

    def __cleanup_outputs(self):
        if not concourse_context():
            try:
                shutil.rmtree(os.path.join("/tmp", "outputs", self.name))
            except FileNotFoundError:
                pass

    def run(self):
        self.__cleanup_outputs()
        for _, v in self.tasks.items():
            v.fn_cached()

    def run_task(self, name):
        self.__cleanup_outputs()
        return self.tasks[name].fn_cached()

class GetStep:
    def __init__(self, name, trigger, passed, params):
        self.name = name
        self.trigger = trigger
        self.passed = passed
        self.params = params

    def concourse(self):
        result = {
            "get": self.name,
            "trigger": self.trigger,
            "passed": self.passed,
        }
        if self.params != None:
            result["params"] = self.params
        return result


class PutStep:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def concourse(self):
        return {
            "put": self.name,
            "params": self.params,
        }

class TryStep:
    def __init__(self, task):
        self.task = task

    def concourse(self):
        return {
            "try": self.task.concourse()
        }

class ParallelStep:
    def __init__(self, job, fail_fast):
        self.job = job
        self.tasks = []
        self.fail_fast = fail_fast

    def task(self, timeout="5m", privileged=False, image_resource=None, resources=[], secrets={}, outputs=[], attempts=1, caches=[]):
        if not image_resource:
            image_resource = self.job.image_resource

        def decorate(fun):
            task = Task(fun, self.job.name, timeout, privileged, image_resource, self.job.script, self.job.inputs, outputs, secrets, attempts, caches)
            self.tasks.append(task)
            self.job.tasks[task.name] = task
            return task.fn_cached
        return decorate

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        return None

    def put(self, name, params=None):
        self.tasks.append(PutStep(name, params))

    def concourse(self):
        return {
            "in_parallel": {
                "fail_fast": self.fail_fast,
                "steps": [task.concourse() for task in self.tasks]
            }
        }