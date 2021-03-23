import sys
import os
import shutil
import subprocess
import argparse
import inspect

from .__shared import CACHE_DIR, SCRIPT_DIR, concourse_context, set_concourse_context
from .job import Job
from .task import STARTER_DIR, PYTHON_DIR


def env_secret_manager(key):
    return os.getenv(os.path.basename(key))


def vault_secret_manager(key):
    return subprocess.check_output(["vault", "read", "-field=value", key]).decode("utf-8")


class Pipeline:
    def __init__(self, name, image_resource={"type": "registry-image", "source": {"repository": "python", "tag": "3.8-buster"}}, script_dirs={}, team="main"):
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        self.script = module.__file__
        dirname = os.path.abspath(os.path.dirname(self.script))
        lib_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.init_dirs = {
            STARTER_DIR: dirname,
            f"{PYTHON_DIR}/{os.path.basename(lib_dir)}": lib_dir,
        }
        if isinstance(script_dirs, list):
            for script in script_dirs:
                dir = os.path.abspath(os.path.join(dirname, script))
                self.init_dirs[os.path.basename(dir)] = dir
        else:
            for key, script in script_dirs.items():
                self.init_dirs[key] = os.path.abspath(os.path.join(dirname, script))
        self.jobs = []
        self.jobs_by_name = {}
        self.resource_chains = {}
        self.resource_types = {}
        self.name = name
        self.image_resource = image_resource
        self.team = team
        self.secret_manager = env_secret_manager

    def __create_secret_manager(self):
        def namespaced_secret_manager(key):
            return self.secret_manager(os.path.join("/concourse", self.team, key))

        return namespaced_secret_manager

    def script_dir(self, key):
        if concourse_context():
            return os.path.realpath(os.path.join(SCRIPT_DIR, key))
        else:
            return self.init_dirs[key]

    def path_append(self, dir):
        self.init_dirs[f"{PYTHON_DIR}/{os.path.basename(dir)}"] = dir
        sys.path.append(dir)

    def __enter__(self):
        parser = argparse.ArgumentParser(description="Python concourse interface")
        parser.add_argument("--job", help="name of the job to run")
        parser.add_argument("--task", help="name of the task to run")
        parser.add_argument("--target", help="upload concourse yaml to the given target")
        parser.add_argument("--concourse", dest="concourse", action="store_true", help="set concourse context to true")
        parser.add_argument("--secret-manager", default="env", choices=["env", "vault"], help="set secret manager")
        parser.add_argument("--dump", dest="dump", action="store_true", help="dump concourse yaml")

        self.args = parser.parse_args()

        set_concourse_context(self.args.concourse)
        if self.args.secret_manager == "vault":
            self.secret_manager = vault_secret_manager

        return self

    def __exit__(self, type, value, tb):
        if not value:
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

    def job(self, name, serial=False, serial_groups=[], old_name=None, groups=[]):
        result = Job(
            name, self.script, self.init_dirs, self.image_resource, self.resource_chains, self.__create_secret_manager(), serial=serial, serial_groups=serial_groups, old_name=old_name, groups=groups
        )
        self.jobs.append(result)
        self.jobs_by_name[name] = result
        return result

    def resource(self, name, resource):
        self.resource_chains[name] = ResourceChain(resource)
        self.resource_types[resource.__class__.__name__] = resource

    def concourse(self):
        groups = {}
        for job in self.jobs:
            for group_name in job.groups:
                if group_name in groups:
                    groups[group_name].append(job.name)
                else:
                    groups[group_name] = [job.name]

        return {
            "pipeline_metadata": {
                "name": self.name,
                "team": self.team,
            },
            "resource_types": list(filter(lambda x: x, map(lambda kv: kv[1].resource_type(), self.resource_types.items()))),
            "resources": list(map(lambda kv: kv[1].resource.concourse(kv[0]), self.resource_chains.items())),
            "jobs": list(map(lambda x: x.concourse(), self.jobs)),
            "groups": [{"name": name, "jobs": jobs} for name, jobs in groups.items()],
        }

    def main(self):
        if self.args.dump:
            import yaml

            yaml.dump(self.concourse(), sys.stdout, allow_unicode=True)
            # fly -t concourse-sapcloud-garden set-pipeline -c  test.yaml -p "create-cluster"
        elif self.args.target:
            import yaml

            config_file = f"/tmp/{self.name}.yaml"
            with open(config_file, "w") as f:
                yaml.dump(self.concourse(), f, allow_unicode=True)
            subprocess.run(["fly", "-t", self.args.target, "set-pipeline", "-c", config_file, "-p", self.name, "-n"], check=True)
        elif self.args.job:
            try:
                print(self.run_task(self.args.job, self.args.task))
            except Exception as e:
                self.__print_error(e)
                sys.exit(1)
        else:
            try:
                print(self.run())
            except Exception as e:
                self.__print_error(e)
                sys.exit(1)

    def __print_error(self, e: Exception):
        frames = inspect.getinnerframes(e.__traceback__)
        BOLD_ERROR = "\033[31;1m  *  "
        NORMAL_ERROR = "\033[31m     "
        ENDC = "\033[0m"
        print("\033[31;1mError: " + str(e) + ENDC)
        for frame in frames:
            prefix = NORMAL_ERROR
            if frame.filename.startswith(os.path.dirname(self.script)):
                prefix = BOLD_ERROR
            print(f"{prefix}At {frame.filename}:{frame.lineno} in function {frame.function}{ENDC}")


class ResourceChain:
    def __init__(self, resource):
        self.resource = resource
        self.passed = []
