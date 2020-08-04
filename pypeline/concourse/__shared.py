import os

CACHE_DIR = 'tasks'
SCRIPT_DIR = 'scripts'
__concourse_context = False

def concourse_context():
    global __concourse_context
    return __concourse_context

def set_concourse_context(value):
    global __concourse_context
    __concourse_context = value
