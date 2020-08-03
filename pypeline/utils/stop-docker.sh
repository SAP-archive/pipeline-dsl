#!/usr/bin/env bash

# Inspired by https://github.com/karlkfi/concourse-dcind

set -o errexit -o pipefail -o nounset

# Waits DOCKERD_TIMEOUT seconds for startup (default: 60)
DOCKERD_TIMEOUT="${DOCKERD_TIMEOUT:-60}"
# Accepts optional DOCKER_OPTS (default: --data-root /scratch/docker)
DOCKER_OPTS="${DOCKER_OPTS:-}"

# Constants
DOCKERD_PID_FILE="/tmp/docker.pid"
DOCKERD_LOG_FILE="/tmp/docker.log"

# Gracefully stop Docker daemon.
stop_docker() {
  if ! [[ -f "${DOCKERD_PID_FILE}" ]]; then
    return 0
  fi
  local docker_pid="$(cat ${DOCKERD_PID_FILE})"
  if [[ -z "${docker_pid}" ]]; then
    return 0
  fi
  echo >&2 "Terminating Docker daemon."
  kill -TERM ${docker_pid}
  local start=${SECONDS}
  echo >&2 "Waiting for Docker daemon to exit..."
  tail --pid=${docker_pid} -f /dev/null
  local duration=$(( SECONDS - start ))
  echo >&2 "Docker exited after ${duration} seconds."
}

stop_docker