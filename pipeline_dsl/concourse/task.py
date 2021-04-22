import os
import json
import base64
import tarfile
import io

from .__shared import CACHE_DIR, SCRIPT_DIR, concourse_context

STARTER_DIR = "starter"
PYTHON_DIR = "pythonpath"


class Task:
    def __init__(self, fun, jobname, secret_manager, image_resource, script, inputs=[], timeout="5m", privileged=False, outputs=[], secrets={}, attempts=1, caches=[], name=None, env={}):
        if not name:
            name = fun.__name__.replace("_", "-")
        self.name = name
        self.timeout = timeout
        self.privileged = privileged
        self.attempts = attempts
        self.caches = caches
        self.secret_manager = secret_manager
        self.config = {
            "platform": "linux",
            "image_resource": image_resource,
            "outputs": [{"name": CACHE_DIR}] + list(map(lambda x: {"name": x}, outputs)),
            "inputs": [{"name": CACHE_DIR}, {"name": SCRIPT_DIR}] + list(map(lambda x: {"name": x}, inputs)),
            "caches": [{"path": cache} for cache in self.caches],
            "params": {
                **dict(map(lambda kv: (str(kv[1]), "(({}))".format(str(kv[1]))), secrets.items())),
                **{
                    "PYTHONPATH": f"{SCRIPT_DIR}/{PYTHON_DIR}:{SCRIPT_DIR}/{STARTER_DIR}:/usr/local/lib/python/garden-tools",
                    "REQUESTS_CA_BUNDLE": "/etc/ssl/certs/ca-certificates.crt",
                },
                **env,
            },
            "run": {
                "path": "/usr/bin/python3",
                "args": [os.path.join(SCRIPT_DIR, STARTER_DIR, os.path.basename(script)), "--job", jobname, "--task", name, "--concourse"],
            },
        }
        cache_file = os.path.join(CACHE_DIR, jobname, name + ".json")

        def fn():
            print(f"Running: {name}")
            kwargs = {}
            for kv in secrets.items():
                kwargs[kv[0]] = self.secret_manager(str(kv[1]))
                if not kwargs[kv[0]] and not isinstance(kv[1], OptionalSecret):
                    raise Exception(f'Secret not available as environment variable "{kv[1]}"')
            for out in outputs:
                dir = out
                if not concourse_context():
                    dir = os.path.join("/tmp", "outputs", jobname, out)
                else:
                    dir = os.path.abspath(out)
                os.makedirs(dir, exist_ok=True)
                kwargs[out] = dir
            result = fun(**kwargs)
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "w") as fd:
                json.dump(result, fd)
            return result

        def fn_cached():
            try:
                with open(cache_file, "r") as fd:
                    return json.load(fd)
            except FileNotFoundError:
                try:
                    return fn()
                except Exception as exc:
                    raise exc from None

        self.fn = fn
        self.fn_cached = fn  # fn_cached

    def concourse(self):
        concourse = {
            "task": self.name.replace("_", "-"),
            "timeout": self.timeout,
            "privileged": self.privileged,
            "config": self.config,
        }
        if self.attempts != 1:
            # explicitly setting attempts to 1 add clutter to the concourse UI
            concourse["attempts"] = self.attempts
        return concourse


class InitTask:
    def __init__(self, init_dirs, image_resource):
        self.init_dirs = init_dirs
        self.image_resource = image_resource

    def package(self):
        buffer = io.BytesIO()
        tar = tarfile.open(fileobj=buffer, mode="x:bz2")
        init_dirs = sorted(list(self.init_dirs.items()), key=lambda d: len(d[1]), reverse=True)

        def filter(tarinfo):
            if not (tarinfo.isdir() or tarinfo.name.endswith(".sh") or tarinfo.name.endswith(".py")):
                return None
            tarinfo.uid = 0
            tarinfo.gid = 0
            tarinfo.uname = "root"
            tarinfo.gname = "root"
            tarinfo.mtime = 0
            return tarinfo

        for dir_concourse, dir_local in init_dirs:
            dir_local = os.path.abspath(dir_local)
            tar.add(dir_local, arcname=dir_concourse, filter=filter)
        tar.close()
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def concourse(self):
        return {
            "task": "init",
            "config": {
                "platform": "linux",
                "image_resource": self.image_resource,
                "outputs": [{"name": CACHE_DIR}, {"name": SCRIPT_DIR}],
                "run": {
                    "path": "/bin/bash",
                    "args": [
                        "-ceu",
                        f'echo "{self.package()}" | base64 -d | tar -C {SCRIPT_DIR} -xvjf -',
                    ],
                },
            },
        }


class OptionalSecret:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name
