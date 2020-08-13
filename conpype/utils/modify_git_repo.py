import os
from conpype.shell import shell
from contextlib import contextmanager

@contextmanager
def modify_git_repo(source, target, message, cached=False):
    shell(["rm", "-rf", target])
    shell(["cp", "-a", source, target])
    cwd = os.getcwd()
    try:
        os.chdir(target)
        shell(["git", "reset", "--hard", "HEAD"])
        shell(["git", "clean", "-f", "-d", "-x"])
        yield
        try:
            if cached:
                shell(["git", "diff", "--cached", "--exit-code", "--quiet"])
            else:
                shell(["git", "diff", "--exit-code", "--quiet"])
        except:
            shell(["git", "commit", "-a", "-m", message])
    finally:
        os.chdir(cwd)
