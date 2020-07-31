build: pypeline/*.py
	python setup.py build

install: build
	python setup.py install

test:
	set -euo pipefail; for i in examples/*.py; do python $$i --dump > /dev/null; done