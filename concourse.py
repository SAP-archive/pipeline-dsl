import sys
import os
import json
import shutil
import subprocess
import platform
import base64
import glob
import argparse
import inspect

CACHE_DIR = 'tasks'
SCRIPT_DIR = 'scripts'
CONCOURSE_CONTEXT = 'concourse'


class Task:
    def __init__(self, name, jobname, timeout, image_resource, script, inputs, secrets):
        self.name = name
        self.timeout = timeout
        self.config = {
            "platform": "linux",
            "image_resource": image_resource,
            "outputs": [{"name": CACHE_DIR}],
            "inputs": [{"name": CACHE_DIR},  {"name": SCRIPT_DIR}] + list(map(lambda x: {"name": x}, inputs)),
            "params": {**dict(map(lambda kv: (str(kv[1]), '(({}))'.format(str(kv[1]))), secrets.items())),
                        **{
                            "PYTHONPATH" : SCRIPT_DIR + "/0:" + SCRIPT_DIR + "/1:" + SCRIPT_DIR + "/2:" + SCRIPT_DIR + "/3:",
                            "CONTEXT": CONCOURSE_CONTEXT,
                            "REQUESTS_CA_BUNDLE" : '/etc/ssl/certs/ca-certificates.crt'
                          }},
            "run": {
                "path": "/usr/bin/python3",
                "args": [os.path.join(SCRIPT_DIR,"0", os.path.basename(script)), "--job", jobname, "--task", name],
            }
        }

    def concourse(self):
        return {
            "task": self.name,
            "timeout": self.timeout,
            "config": self.config,
        }


class InitTask:
    def __init__(self, script_dirs, image_resource):
        self.script_dirs = script_dirs
        self.image_resource = image_resource

    def concourse(self):
        if platform.system() == "Darwin":
            tar = "gtar"
        else:
            tar = "tar"
        files = []
        transform = []
        for dir in self.script_dirs:
            dir = os.path.abspath(dir)
            transform.append("--transform 's|{dir}|{i}|g'".format(dir=dir,i=len(transform)))
            files = files + list(glob.glob(os.path.join(dir, '*.py'), recursive=True))
        cmd = '{tar} cj --sort=name --mtime="UTC 2019-01-01" {transform} --owner=root:0 --group=root:0 -b 1 -P -f - {files}'.format(
            tar=tar, transform = " ".join(transform), files=" ".join(files))
        data = base64.b64encode(subprocess.check_output(
            cmd, shell=True)).decode("utf-8")
        return {
            "task": "init",
            "config": {
                "platform": "linux",
                "image_resource": self.image_resource,
                "outputs": [{"name": CACHE_DIR},  {"name": SCRIPT_DIR}],
                "run": {
                    "path": "/bin/bash",
                    "args": [
                        '-ceu',
                        'echo "{data}" | base64 -d | tar -C {script_dir} -xjf -'.format(
                            script_dir=SCRIPT_DIR, data=data),
                    ],
                }
            }
        }


class GitRepo:
    def __init__(self, uri, username=None,password=None, branch="master",ignore_paths=None):
        self.uri = uri
        self.username=username
        self.password=password
        self.branch=branch
        self.ignore_paths = ignore_paths

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "git",
            "source": {
                "uri": self.uri,
                "branch": self.branch,
                "username": self.username,
                "password": self.password,
                "ignore_paths": self.ignore_paths,
            }
        }
        return result

    def get(self, name):
        if os.getenv("CONTEXT") == CONCOURSE_CONTEXT:
            return name
        return os.getenv("HOME") + "/workspace/" + name


class GetTask:
    def __init__(self, name, trigger, passed):
        self.name = name
        self.trigger = trigger
        self.passed = passed

    def concourse(self):
        return {
            "get": self.name,
            "trigger": self.trigger,
            "passed": self.passed,
        }


class OptionalSecret:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class ResourceChain:
    def __init__(self, resource):
        self.resource = resource
        self.passed = []


class Job:
    def __init__(self, name, script, script_dirs, image_resource, resource_chains):
        self.name = name
        self.plan = [InitTask(script_dirs, image_resource)]
        self.last_task = None
        self.image_resource = image_resource
        self.resource_chains = resource_chains
        self.script = script
        self.inputs = []
        self.tasks = {}

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        return None

    def get(self, name, trigger=True, passed=None):
        resource_chain = self.resource_chains[name]
        if not passed:
            passed = resource_chain.passed.copy()
        self.plan.append(GetTask(name, trigger, passed))
        resource_chain.passed.append(self.name)
        self.inputs.append(name)
        return resource_chain.resource.get(name)

    def task(self, timeout="5m", image_resource=None, resources=[], secrets={}):
        if not image_resource:
            image_resource = self.image_resource

        def decorate(fun):
            name = fun.__name__
            self.plan.append(Task(name, self.name, timeout,
                                  image_resource, self.script, self.inputs, secrets))
            cache_file = os.path.join(CACHE_DIR, self.name, name + ".json")

            def fn():
                print("Running: {}".format(name))
                kwargs = {}
                for kv in secrets.items():
                    kwargs[kv[0]] = os.getenv(str(kv[1]))
                    if not kwargs[kv[0]] and not isinstance(kv[1], OptionalSecret):
                        raise Exception('Secret not available as environment variable "{secret}"'.format(secret=kv[1]))
                result = fun(**kwargs)
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'w') as fd:
                    json.dump(result, fd)
                return result

            def fn_cached():
                try:
                    with open(cache_file, 'r') as fd:
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
            "name": self.name,
            "plan": list(map(lambda x: x.concourse(), self.plan))
        }

    def run(self):
        if self.last_task:
            return self.last_task()
        else:
            return None

    def run_task(self, name):
        return self.tasks[name]()


class Pipeline():
    def __init__(self, name,image_resource = {"type": "registry-image","source": {"repository": "python","tag": "3.8-buster"}}):
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        self.script = module.__file__
        self.script_dirs = [os.path.dirname(self.script),os.path.dirname(__file__)]
        self.jobs = []
        self.jobs_by_name = {}
        self.resource_chains = {}
        self.resource_types = {}
        self.name = name
        self.image_resource = image_resource

    def path_append(self, dir):
        self.script_dirs.append(dir)
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
            raise Exception("Job " + job + " not found. List of available jobs: " + " ".join(list(self.jobs_by_name.keys())))

    def job(self, name):
        result = Job(name, self.script, self.script_dirs, self.image_resource,
                     self.resource_chains)
        self.jobs.append(result)
        self.jobs_by_name[name] = result
        return result

    def resource(self, name, resource):
        self.resource_chains[name] = ResourceChain(resource)
        self.resource_types[resource.__class__.__name__] = resource

    def concourse(self):
        return {
            "resource_types": list(filter(lambda x: x, map(lambda kv: kv[1].resource_type(), self.resource_types.items()))),
            "resources": list(map(lambda kv: kv[1].resource.concourse(kv[0]), self.resource_chains.items())),
            "jobs": list(map(lambda x: x.concourse(), self.jobs)),
        }

    def main(self):
        parser = argparse.ArgumentParser(
            description='Python concourse interface')
        parser.add_argument('--job', help='name of the job to run')
        parser.add_argument('--task', help='name of the task to run')
        parser.add_argument('--concourse', dest='concourse',
                            action='store_true', help='dump concourse')

        args = parser.parse_args()

        if args.concourse:
            import yaml
            yaml.dump(self.concourse(), sys.stdout, allow_unicode=True)
            # fly -t concourse-sapcloud-garden set-pipeline -c  test.yaml -p "create-cluster"
        elif args.job:
            print(self.run_task(args.job, args.task))
        else:
            print(self.run())

def shell(cmd,check=True,cwd=None):
    print(" ".join(cmd))
    return subprocess.run(cmd, check=check, cwd=cwd)