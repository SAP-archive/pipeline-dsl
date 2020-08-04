build: pypeline/*.py
	python setup.py build

install: build
	python setup.py install

test: test-examples test-unit

test-examples: 
	set -euo pipefail; for i in examples/*.py; do python $$i --dump > /dev/null; done
	
test-unit:
	python -m"unittest"