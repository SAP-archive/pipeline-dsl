import sys
import os
import json
import shutil
import subprocess
import platform
import base64
import glob
import inspect
from collections import OrderedDict

class Password:
    def __init__(self, password):
        self.password = password

    def __str__(self):
        return self.password

def shell(cmd, check=True, cwd=None, capture_output=False):
    print(" ".join(
        list(map(lambda x: "<redacted>" if isinstance(x, Password) else str(x), cmd))))
    return subprocess.run(list(map(lambda x: str(x), cmd)), check=check, cwd=cwd, capture_output=capture_output)
