class Pool:
    def __init__(self, uri, branch, pool, username, password):
        self.uri = uri
        self.branch = branch
        self.pool = pool
        self.username = username
        self.password = password

    def resource_type(self):
        return {
            "name": "pool-stable",
            "type": "docker-image",
            "source": {
                "repository": "concourse/pool-resource",
                "tag": "1.1.1",
            },
        }

    def get(self, name):
        return self

    def concourse(self, name):
        result = {
            "name": name,
            "type": "pool-stable",
            "icon": "lock",
            "source": {
                "uri": self.uri,
                "branch": self.branch,
                "pool": self.pool,
                "username": self.username,
                "password": self.password,
            },
        }
        return result
