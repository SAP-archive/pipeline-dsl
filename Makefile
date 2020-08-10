SHELL := /bin/bash

build: conpype/*.py
	python setup.py build

install: build
	python setup.py install

test: test-examples test-unit

test-examples: 
	@set -euo pipefail; \
	for i in examples/*.py; do \
		echo $$i; \
		fly vp -c <(PYTHONPATH=$$(PWD) python $$i --dump); \
	done
	
test-unit:
	PYTHONPATH=$$(PWD) python -m"unittest"

coverage:
	coverage run -m unittest
	coverage report