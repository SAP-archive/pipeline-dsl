from contextlib import contextmanager
from pypeline.concourse.__shared import concourse_context
from pypeline.shell import shell

@contextmanager
def docker_daemon():
    if concourse_context():
        shell(["scripts/py1/pypeline/utils/start-docker.sh"])
        try:
            yield
        finally:
            shell(["scripts/py1/pypeline/utils/stop-docker.sh"])
    else:
        yield
