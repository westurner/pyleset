
.PHONY: help clean clean-pyc clean-build list test test-all coverage docs release sdist

default: help

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "testall - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "sdist - package"
	@echo ""
	@echo "install_brew - install packages with brew"
	@echo "install_apt - install packages with apt-get"
	@echo ""
	@echo "install - pip install requirements and this package as editable"
	@echo "develop - python setup.py develop"
	@echo ""
	@echo "requirements - rebuild pip requirements-all.txt from setup.py"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 pyleset test

test:
	py.test

test-all:
	tox

coverage:
	coverage run --source pyleset setup.py test
	coverage report -m
	coverage html
	open htmlcov/index.html

docs:
	rm -f docs/pyleset.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ pyleset
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

sdist: clean
	python setup.py sdist
	python setup.py bdist_wheel upload
	ls -l dist


install_brew:
	brew install pyexiv2 libmagic
	# TODO: link into virtualenv (system-site-packages, egg-link,
	# symlink)

install_apt:
	sudo apt-get install python-pyexiv2 libmagic
	# TODO: link into virtualenv (system-site-packages, egg-link,
	# symlink)

install:
	pip install -r requirements-all.txt
	pip install -e .
	#pip install pyleset[all]

develop:
	python setup.py develop

requirements:
	python setup.py -q requirements | tee requirements-all.txt
