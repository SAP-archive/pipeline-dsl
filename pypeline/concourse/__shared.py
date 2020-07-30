import os

CACHE_DIR = 'tasks'
SCRIPT_DIR = 'scripts'
CONCOURSE_CONTEXT = 'concourse'

def concourse_context():
    return os.getenv("CONTEXT") == CONCOURSE_CONTEXT