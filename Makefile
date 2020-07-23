build: pypeline/*.py
	python setup.py build

install: build
	python setup.py install