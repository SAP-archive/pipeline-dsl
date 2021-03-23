import os
from pipeline_dsl.resources.git import GitRepoResource
from pipeline_dsl.shell import shell
from contextlib import contextmanager


@contextmanager
def modify_git_repo(source_repo, target, message, cached=False):
    user_name = "unknown"
    user_email = "unknown@nowhere"
    if isinstance(source_repo, GitRepoResource):
        source = source_repo.path
        user_name = source_repo.config.get("user.name", user_name)
        user_email = source_repo.config.get("user.email", user_email)
    else:
        source = source_repo
    shell(["rm", "-rf", target])
    shell(["cp", "-a", source, target])
    cwd = os.getcwd()
    try:
        os.chdir(target)
        shell(["git", "config", "user.name", user_name])
        shell(["git", "config", "user.email", user_email])
        shell(["git", "reset", "--mixed", "HEAD"])  # Keep working tree untouched
        shell(["git", "clean", "-f", "-d", "-x"])
        yield
        try:
            if cached:
                shell(["git", "diff", "--cached", "--exit-code", "--quiet"])
            else:
                shell(["git", "diff", "--exit-code", "--quiet"])
        except Exception:
            shell(["git", "commit", "-a", "-m", message])
    finally:
        os.chdir(cwd)
