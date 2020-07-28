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

from __shared import CACHE_DIR, CONCOURSE_CONTEXT, SCRIPT_DIR, concourse_context

class Task:
    def __init__(self, fun, jobname, timeout, privileged, image_resource, script, inputs, outputs, secrets, attempts, caches):
        name = fun.__name__
        self.name = name
        self.timeout = timeout
        self.privileged = privileged
        self.attempts = attempts
        self.caches = caches
        self.config = {
            "platform": "linux",
            "image_resource": image_resource,
            "outputs": [{"name": CACHE_DIR}] + list(map(lambda x: {"name": x}, outputs)),
            "inputs": [{"name": CACHE_DIR},  {"name": SCRIPT_DIR}] + list(map(lambda x: {"name": x}, inputs)),
            "caches": [{"path": cache} for cache in self.caches],
            "params": {**dict(map(lambda kv: (str(kv[1]), '(({}))'.format(str(kv[1]))), secrets.items())),
                       **{
                "PYTHONPATH": SCRIPT_DIR + ":" + SCRIPT_DIR + "/py-cicd:" + "/usr/local/lib/python/garden-tools",
                "CONTEXT": CONCOURSE_CONTEXT,
                "REQUESTS_CA_BUNDLE": '/etc/ssl/certs/ca-certificates.crt'
            }},
            "run": {
                "path": "/usr/bin/python3",
                "args": [os.path.join(SCRIPT_DIR, "concourse", os.path.basename(script)), "--job", jobname, "--task", name],
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
                    dir = os.path.join("/tmp", "outputs", jobname, out)
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
        self.fn_cached = fn # fn_cached


    def concourse(self):
        concourse = {
            "task": self.name,
            "timeout": self.timeout,
            "privileged": self.privileged,
            "config": self.config,
        }
        if self.attempts != 1:
            # explicitly setting attempts to 1 add clutter to the concourse UI
            concourse["attempts"] = self.attempts
        return concourse


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
            transform.append(f"--transform 's|{dir}|{dir.split('/')[-1]}|g'")
            files = files + \
                list(glob.glob(os.path.join(dir, '**', '*.[ps][yh]'), recursive=True))
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

class OptionalSecret:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

