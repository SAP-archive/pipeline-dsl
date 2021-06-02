from pipeline_dsl.resources.resource import AbstractResource, ConcourseResource
from typing import Optional, Dict


class Cron(AbstractResource):
    def __init__(self, definition: str) -> None:
        self.definition = definition

    def resource_type(self) -> Optional[Dict]:
        return {
            "name": "cron",
            "type": "docker-image",
            "source": {
                "repository": "phil9909/concourse-cron-resource",
                "tag": "latest",
            },
        }

    def concourse(self, name: str) -> ConcourseResource:
        return ConcourseResource(
            name=name,
            type="cron",
            icon="clock-outline",
            source={
                "cron": self.definition,
                "location": "Europe/Berlin",
            },
        )

    def get(self, name: str) -> None:
        return None
