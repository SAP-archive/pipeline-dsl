from contextlib import contextmanager
from pypeline.concourse.__shared import concourse_context
from pypeline.shell import shell
from pypeline.concourse.task import PYTHON_DIR
from pypeline.concourse.__shared import SCRIPT_DIR

START_SCRIPT = f"{PYTHON_DIR}/pypeline/utils/start-docker.sh"
STOP_SCRIPT = f"{PYTHON_DIR}/pypeline/utils/stop-docker.sh"

@contextmanager
def docker_daemon():
    if concourse_context():
        shell([os.path.join(SCRIPT_DIR,START_SCRIPT)])
        try:
            yield
        finally:
            shell([os.path.join(SCRIPT_DIR,STOP_SCRIPT)])
    else:
        yield
