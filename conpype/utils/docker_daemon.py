from contextlib import contextmanager
from conpype.concourse.__shared import concourse_context
from conpype.shell import shell
from conpype.concourse.task import PYTHON_DIR
from conpype.concourse.__shared import SCRIPT_DIR
import os

START_SCRIPT = f"{PYTHON_DIR}/conpype/utils/start-docker.sh"
STOP_SCRIPT = f"{PYTHON_DIR}/conpype/utils/stop-docker.sh"


@contextmanager
def docker_daemon():
    if concourse_context():
        shell([os.path.join(SCRIPT_DIR, START_SCRIPT)])
        try:
            yield
        finally:
            shell([os.path.join(SCRIPT_DIR, STOP_SCRIPT)])
    else:
        yield
