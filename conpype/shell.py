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
    stdout = stderr = subprocess.PIPE if capture_output else None

    print(" ".join(
        list(map(lambda x: "<redacted>" if isinstance(x, Password) else str(x), cmd))))
    try:
        return subprocess.run(list(map(lambda x: str(x), cmd)), check=check, cwd=cwd, stdout=stdout, stderr=stderr)
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print(error)
        frame = inspect.stack()[1]
        print(f"    At {frame.filename}:{frame.lineno} in function {frame.function}")
        sys.exit(1)
