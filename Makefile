SHELL := /bin/bash

build: pypeline/*.py
	python setup.py build

install: build
	python setup.py install

test: test-examples test-unit

test-examples: 
	@set -euo pipefail; \
	for i in examples/*.py; do \
		echo $$i; \
		fly vp -c <(python $$i --dump); \
	done
	
test-unit:
	python -m"unittest"