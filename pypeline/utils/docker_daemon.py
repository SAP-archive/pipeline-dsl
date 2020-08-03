from contextlib import contextmanager



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
