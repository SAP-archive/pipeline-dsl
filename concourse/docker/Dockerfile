FROM python:3-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends install \
      make \
      git \
      bzip2 \
  # cleanup
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
# workaround needed because of hardcoded path in pipeline_dsl: Task.init()
RUN ln -s /usr/local/bin/python3 /usr/bin/python3
