SHELL := /bin/bash

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
