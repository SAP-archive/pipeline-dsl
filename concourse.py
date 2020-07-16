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
from collections import OrderedDict

CACHE_DIR = 'tasks'
SCRIPT_DIR = 'scripts'
CONCOURSE_CONTEXT = 'concourse'


def concourse_context():
    return os.getenv("CONTEXT") == CONCOURSE_CONTEXT


class Task:
    def __init__(self, fun, jobname, timeout, image_resource, script, inputs, outputs, secrets, attempts):
        name = fun.__name__
        self.name = name
        self.timeout = timeout
        self.attempts = attempts
        self.config = {
            "platform": "linux",
            "image_resource": image_resource,
            "outputs": [{"name": CACHE_DIR}] + list(map(lambda x: {"name": x}, outputs)),
            "inputs": [{"name": CACHE_DIR},  {"name": SCRIPT_DIR}] + list(map(lambda x: {"name": x}, inputs)),
            "params": {**dict(map(lambda kv: (str(kv[0]), '(({}))'.format(str(kv[1]))), secrets.items())),
                       **{
                "PYTHONPATH": SCRIPT_DIR + "/0:" + SCRIPT_DIR + "/1:" + SCRIPT_DIR + "/2:" + SCRIPT_DIR + "/3" + os.environ["PYTHONPATH"],
                "CONTEXT": CONCOURSE_CONTEXT,
                "REQUESTS_CA_BUNDLE": '/etc/ssl/certs/ca-certificates.crt'
            }},
            "run": {
                "path": "/usr/bin/python3",
                "args": [os.path.join(SCRIPT_DIR, "0", os.path.basename(script)), "--job", jobname, "--task", name],
            }
        }
        cache_file = os.path.join(CACHE_DIR, jobname, name + ".json")

        def fn():
            print(f"Running: {name}")
            kwargs = {}
            for kv in secrets.items():
                kwargs[kv[0]] = os.getenv(str(kv[1]))
                if not kwargs[kv[0]] and not isinstance(kv[1], OptionalSecret):
                    raise Exception(f'Secret not available as environment variable "{kv[1]}"')
            for out in outputs:
                dir = out
                if not concourse_context():
                    dir = os.path.join("/tmp", self.name, name, out)
                os.makedirs(dir, exist_ok=True)
                kwargs[out] = dir
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
        self.fn = fn
        self.fn_cached = fn_cached


    def concourse(self):
        return {
            "task": self.name,
            "timeout": self.timeout,
            "config": self.config,
            "attempts": self.attempts,
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
            transform.append(f"--transform 's|{dir}|{len(transform)}|g'")
            files = files + \
                list(glob.glob(os.path.join(dir, '*.py'), recursive=True))
        cmd = f'{tar} cj --sort=name --mtime="UTC 2019-01-01" {" ".join(transform)} --owner=root:0 --group=root:0 -b 1 -P -f - {" ".join(files)}'
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
                        f'echo "{data}" | base64 -d | tar -C {SCRIPT_DIR} -xjf -',
                    ],
                }
            }
        }


class GitRepoResource:
    def __init__(self, name):
        self.name = name
        if concourse_context():
            self.path = os.path.abspath(self.name)
        else:
            self.path = os.getenv("HOME") + "/workspace/" + self.name

    def __str__(self):
        return self.directory()

    def directory(self):
        return self.path

    def ref(self):
        if concourse_context():
            with open(os.path.join(self.directory(), ".git/ref")) as f:
                return f.read().strip()
        try:
            return subprocess.check_output(["git", "describe", "--tags"], cwd=self.directory()).decode("utf-8").strip()
        except:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.directory()).decode("utf-8").strip()


class GitRepo:
    def __init__(self, uri, username=None, password=None, branch="master", ignore_paths=None, tag_filter=None):
        self.uri = uri
        self.username = username
        self.password = password
        self.branch = branch
        self.ignore_paths = ignore_paths
        self.tag_filter = tag_filter

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
                "tag_filter": self.tag_filter,
            }
        }
        return result

    def get(self, name):
        return GitRepoResource(name)


class GithubReleaseResource:
    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self):
        return self.name

    def tag(self, default=None):
        if concourse_context():
            with open(os.path.join(self.path, "tag")) as f:
                return f.read().strip()
        return default


class GithubRelease:
    def __init__(self, owner, repo, access_token=None, pre_release=False, release=True):
        self.owner = owner
        self.repo = repo
        self.access_token = access_token
        self.pre_release = pre_release
        self.release = release

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "github-release",
            "icon": "github-circle",
            "source": {
                "owner": self.owner,
                "repository": self.repo,
                "access_token": self.access_token,
                "pre_release": self.pre_release,
                "release": self.release,
            }
        }
        return result

    def get(self, name):
        return GithubReleaseResource(name)


class DockerImageResource:
    def __init__(self, name):
        self.name = name
        self.path = os.path.abspath(self.name)

    def __str__(self):
        return self.name

    def digest(self):
        if concourse_context():
            with open(os.path.join(self.path, "digest")) as f:
                return f.read().strip()
        return "latest"

class DockerImage:
    def __init__(self, repository, username=None, password=None, tag="latest"):
        self.repository = repository
        self.username = username
        self.password = password
        self.tag = tag

    def resource_type(self):
        return None

    def concourse(self, name):
        result = {
            "name": name,
            "type": "docker-image",
            "icon": "docker",
            "source": {
                "repository": self.repository,
                "username": self.username,
                "password": self.password,
                "tag": self.tag
            }
        }
        return result

    def get(self, name):
        return DockerImageResource(name)
    


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


class PutTask:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def concourse(self):
        return {
            "put": self.name,
            "params": self.params,
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
    def __init__(self, name, script, script_dirs, image_resource, resource_chains, serial):
        self.name = name
        self.plan = [InitTask(script_dirs, image_resource)]
        self.image_resource = image_resource
        self.resource_chains = resource_chains
        self.script = script
        self.inputs = []
        self.tasks = OrderedDict()
        self.serial = serial

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        return None

    def get(self, name, trigger=False, passed=None):
        resource_chain = self.resource_chains[name]
        if not passed:
            passed = resource_chain.passed.copy()
        self.plan.append(GetTask(name, trigger, passed))
        resource_chain.passed.append(self.name)
        self.inputs.append(name)
        return resource_chain.resource.get(name)

    def put(self, name, params=None):
        resource_chain = self.resource_chains[name]
        self.plan.append(PutTask(name, params))
        resource_chain.passed.append(self.name)
        self.inputs.append(name)
        return resource_chain.resource.get(name)

    def task(self, timeout="5m", image_resource=None, resources=[], secrets={}, outputs=[], attempts=1):
        if not image_resource:
            image_resource = self.image_resource

        def decorate(fun):
            task = Task(fun, self.name, timeout, image_resource, self.script, self.inputs, outputs, secrets, attempts)
            self.plan.append(task)
            self.tasks[task.name] = task
            return task.fn_cached
        return decorate

    def concourse(self):
        return {
            "name": self.name,
            "plan": list(map(lambda x: x.concourse(), self.plan)),
            "serial": self.serial
        }

    def run(self):
        for k, v in self.tasks.items():
            v.fn_cached()

    def run_task(self, name):
        return self.tasks[name].fn_cached()


class Pipeline():
    def __init__(self, name, image_resource={"type": "registry-image", "source": {"repository": "python", "tag": "3.8-buster"}}):
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        self.script = module.__file__
        self.script_dirs = [os.path.dirname(
            self.script), os.path.dirname(__file__)]
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
            raise Exception("Job " + job + " not found. List of available jobs: " +
                            " ".join(list(self.jobs_by_name.keys())))

    def job(self, name, serial=False):
        result = Job(name, self.script, self.script_dirs, self.image_resource,
                     self.resource_chains, serial=serial)
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


class Password:
    def __init__(self, password):
        self.password = password

    def __str__(self):
        return self.password


def shell(cmd, check=True, cwd=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    print(" ".join(
        list(map(lambda x: "<redacted>" if isinstance(x, Password) else str(x), cmd))))
    return subprocess.run(list(map(lambda x: str(x), cmd)), check=check, cwd=cwd, stdout=stdout, stderr=stderr)
