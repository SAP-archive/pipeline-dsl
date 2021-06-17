from pipeline_dsl.resources.resource import AbstractResource, ConcourseResource
from typing import Optional, Dict


class GoogleCloudStorage(AbstractResource["GoogleCloudStorage"]):
    def __init__(self, bucket: str, regexp: str, credentials: str) -> None:
        self.bucket = bucket
        self.regexp = regexp
        self.credentials = credentials

    def resource_type(self) -> Optional[Dict]:
        return {
            "name": "gcs",
            "type": "docker-image",
            "source": {
                "repository": "frodenas/gcs-resource",
                "tag": "latest",
            },
        }

    def get(self, name: str) -> "GoogleCloudStorage":
        return self

    def concourse(self, name: str) -> ConcourseResource:
        result = ConcourseResource(
            name=name,
            type="gcs",
            icon="file-cloud",
            source={
                "bucket": self.bucket,
                "regexp": self.regexp,
                "json_key": self.credentials,
            },
        )
        return result
