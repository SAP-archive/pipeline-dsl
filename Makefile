SHELL := /bin/bash
TARGET_CICD_IMAGE := "europe-west3-docker.pkg.dev/sap-se-gcp-istio-dev/public/cicd_pipeline_dsl:latest"

build: pipeline_dsl/*.py
	python3 setup.py build

install: build
	python3 setup.py install

test: test-examples test-unit

test-examples:
	@set -euo pipefail; \
	for i in examples/*.py; do \
		echo $$i; \
		fly vp -c <(PYTHONPATH=$$(pwd) python3 $$i --dump); \
	done

test-unit:
	PYTHONPATH=$$(pwd) python3 -m"unittest"

dist:
	python3 setup.py sdist

coverage:
	PYTHONPATH=$$(pwd) coverage run --include=./* -m unittest
	coverage html
	coverage report --fail-under=75

cicd-image-build:
	docker build -t ${TARGET_CICD_IMAGE} concourse/docker

cicd-image-push: cicd-image-build
	docker push ${TARGET_CICD_IMAGE}
