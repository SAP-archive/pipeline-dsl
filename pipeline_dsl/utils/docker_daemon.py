from contextlib import contextmanager
from pipeline_dsl.concourse.__shared import concourse_context
from pipeline_dsl.shell import shell
from pipeline_dsl.concourse.task import PYTHON_DIR
from pipeline_dsl.concourse.__shared import SCRIPT_DIR
import os

START_SCRIPT = f"{PYTHON_DIR}/pipeline_dsl/utils/start-docker.sh"
STOP_SCRIPT = f"{PYTHON_DIR}/pipeline_dsl/utils/stop-docker.sh"


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
