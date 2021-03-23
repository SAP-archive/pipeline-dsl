class GoogleCloudStorage:
    def __init__(self, bucket, regexp, credentials):
        self.bucket = bucket
        self.regexp = regexp
        self.credentials = credentials

    def resource_type(self):
        return {
            "name": "gcs",
            "type": "docker-image",
            "source": {
                "repository": "frodenas/gcs-resource",
                "tag": "latest",
            },
        }

    def get(self, name):
        return self

    def concourse(self, name):
        result = {
            "name": name,
            "type": "gcs",
            "icon": "file-cloud",
            "source": {
                "bucket": self.bucket,
                "regexp": self.regexp,
                "json_key": self.credentials,
            },
        }
        return result
