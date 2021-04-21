class PyPi:
    def __init__(self, name):
        self.name = name

    def resource_type(self):
        return {
            "name": "pypi",
            "type": "docker-image",
            "source": {
                "repository": "cfplatformeng/concourse-pypi-resource",
                "tag": "latest",
            },
        }

    def get(self, name):
        return self

    def concourse(self, name):
        result = {
            "name": name,
            "type": "pypi",
            "icon": "language-python",
            "source": {
                "name": self.name,
            },
        }
        return result
