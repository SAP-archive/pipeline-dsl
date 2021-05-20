FROM ubuntu:20.04
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends install \
      python3 python3-pip \
      make \
      git \
  # cleanup
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
