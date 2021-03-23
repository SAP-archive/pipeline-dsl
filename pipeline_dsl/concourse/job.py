import os
import shutil
from collections import OrderedDict

from .__shared import concourse_context
from .task import InitTask, Task


class Job:
    def __init__(self, name, script, init_dirs, image_resource, resource_chains, secret_manager, serial, serial_groups, old_name, groups):
        self.name = name
        self.groups = groups
        self.old_name = old_name
        self.plan = [InitTask(init_dirs, image_resource)]
        self.image_resource = image_resource
        self.resource_chains = resource_chains
        self.script = script
        self.inputs = []
        self.tasks = OrderedDict()
        self.serial = serial
        self.serial_groups = serial_groups
        self.on_success = None
        self.on_failure = None
        self.on_abort = None
        self.ensure = None
        self.secret_manager = secret_manager

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        return None

    def get(self, name, trigger=False, passed="auto", params=None, version=None):
        resource_chain = self.resource_chains.get(name, None)
        if not resource_chain:
            raise Exception("Resource " + name + " not configured for pipeline")
        if passed == "auto":
            passed = resource_chain.passed.copy()
        self.plan.append(GetStep(name, trigger, passed, params, version))
        resource_chain.passed.append(self.name)
        self.inputs.append(name)
        return resource_chain.resource.get(name)

    def put(self, name, params=None):
        resource_chain = self.resource_chains.get(name, None)
        if not resource_chain:
            raise Exception("Resource " + name + " not configured for pipeline")
        self.plan.append(PutStep(name, params))
        resource_chain.passed.append(self.name)
        self.inputs.append(name)
        return resource_chain.resource.get(name)

    def task(self, image_resource=None, **kwargs):
        if not image_resource:
            image_resource = self.image_resource

        def decorate(fun):
            task = Task(fun=fun, jobname=self.name, secret_manager=self.secret_manager, image_resource=image_resource, script=self.script, inputs=self.inputs, **kwargs)

            self.plan.append(task)
            self.tasks[task.name] = task
            return task.fn_cached

        return decorate

    def in_parallel(self, fail_fast=False):
        parallel_task = ParallelStep(self, fail_fast, self.secret_manager)
        self.plan.append(parallel_task)
        return parallel_task

    def concourse(self):
        obj = {
            "name": self.name.replace("_", "-"),
            "plan": list(map(lambda x: x.concourse(), self.plan)),
            "serial": self.serial,
            "serial_groups": self.serial_groups,
        }
        if self.on_success:
            obj["on_success"] = self.on_success.concourse()
        if self.on_failure:
            obj["on_failure"] = self.on_failure.concourse()
        if self.on_abort:
            obj["on_abort"] = self.on_abort.concourse()
        if self.ensure:
            obj["ensure"] = self.ensure.concourse()
        if self.old_name:
            obj["old_name"] = self.old_name
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
        task = self.tasks.get(name, None)
        if not task:
            task = self.tasks.get(name.replace("_", "-"), None)
        if not task:
            raise Exception(f"Task {name} not configured inside job {self.name}")
        return task.fn_cached()


class GetStep:
    def __init__(self, name, trigger, passed, params, version):
        self.name = name
        self.trigger = trigger
        self.passed = passed
        self.params = params
        self.version = version

    def concourse(self):
        result = {
            "get": self.name,
            "trigger": self.trigger,
            "passed": self.passed,
        }
        if self.params is not None:
            result["params"] = self.params
        if self.version is not None:
            result["version"] = self.version
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
            "try": self.task.concourse(),
        }


class DoStep:
    def __init__(self, tasks):
        self.tasks = tasks

    def concourse(self):
        return {
            "do": [task.concourse() for task in self.tasks],
        }


class ParallelStep:
    def __init__(self, job, fail_fast, secret_manager=None):
        self.job = job
        self.tasks = []
        self.fail_fast = fail_fast
        self.secret_manager = secret_manager

    def task(self, image_resource=None, **kwargs):
        if not image_resource:
            image_resource = self.job.image_resource

        def decorate(fun):
            task = Task(fun=fun, jobname=self.job.name, secret_manager=self.secret_manager, image_resource=image_resource, script=self.job.script, inputs=self.job.inputs, **kwargs)
            self.tasks.append(task)
            self.job.tasks[task.name] = task
            return task.fn_cached

        return decorate

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        return None

    def get(self, name, trigger=False, passed="auto", params=None, version=None):
        resource_chain = self.job.resource_chains.get(name, None)
        if not resource_chain:
            raise Exception("Resource " + name + " not configured for pipeline")
        if passed == "auto":
            passed = resource_chain.passed.copy()
        self.tasks.append(GetStep(name, trigger, passed, params, version))
        resource_chain.passed.append(self.job.name)
        self.job.inputs.append(name)
        return resource_chain.resource.get(name)

    def put(self, name, params=None):
        self.tasks.append(PutStep(name, params))

    def concourse(self):
        return {
            "in_parallel": {
                "fail_fast": self.fail_fast,
                "steps": [task.concourse() for task in self.tasks],
            },
        }
