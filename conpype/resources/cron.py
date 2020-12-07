class Cron:
    def __init__(self, definition):
        self.definition = definition

    def resource_type(self):
        return {
            "name": "cron",
            "type": "docker-image",
            "source": {
                "repository": "phil9909/concourse-cron-resource",
                "tag": "latest",
            },
        }

    def concourse(self, name):
        return {
            "name": name,
            "type": "cron",
            "icon": "clock-outline",
            "source": {
                "cron": self.definition,
                "location": "Europe/Berlin",
            },
        }

    def get(self, name):
        return None
