import subprocess


class Password:
    def __init__(self, password):
        self.password = password

    def __str__(self):
        return self.password


def shell(cmd, check=True, cwd=None, capture_output=False, input=None):
    stdout = stderr = subprocess.PIPE if capture_output else None

    print(
        " ".join(
            list(map(lambda x: "<redacted>" if isinstance(x, Password) else str(x), cmd)),
        )
    )
    return subprocess.run(list(map(lambda x: str(x), cmd)), check=check, cwd=cwd, stdout=stdout, stderr=stderr, input=input)
