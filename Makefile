SHELL := /bin/bash

build: pipeline_dsl/*.py
	python setup.py build

install: build
	python setup.py install

test: test-examples test-unit

test-examples: 
	@set -euo pipefail; \
	for i in examples/*.py; do \
		echo $$i; \
		fly vp -c <(PYTHONPATH=$$(pwd) python $$i --dump); \
	done
	
test-unit:
	PYTHONPATH=$$(pwd) python -m"unittest"

coverage:
	PYTHONPATH=$$(pwd) coverage run -m unittest
	coverage html
	coverage report
