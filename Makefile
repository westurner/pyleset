
.PHONY: help clean clean-pyc clean-build list test test-all coverage docs \
	release sdist \
	install_apt install_brew install \
	install-from-pypi install-from-pypi-all \
	develop \
	install-from-source install-from-source-all \
	requirements test-requirements 

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
	@echo "install-from-pypi - pip install pyleset"
	@echo "install-from-pypi-all - pip install pyleset[all]"
	@echo ""
	@echo ""
	@echo "develop - python setup.py develop"
	@echo "install-from-source - pip install -e"
	@echo "install-from-source-all - clone, install all requirements from source, install"
	@echo ""
	@echo "requirements - regenerate ./requirements/ requirements.txt files"
	@echo "test-requirements - test requirements.txt generation commands"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr requirements_test/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 pyleset test

test: test-requirements
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
	## Either
	#$(MAKE) install_brew
	#$(MAKE) install_apt

	## Either
	#$(MAKE) install-from-source
	#$(MAKE) install-from-source-all
	#$(MAKE) install-from-pypi
	#$(MAKE) install-from-pypi-all


install-from-source:
	pip install -e https://github.com/westurner/pyleset#egg=pyleset

install-from-source-all:
	( cd $(VIRTUAL_ENV)/src;  \
		git clone https://github.com/westurner/pyleset; \
		cd pyleset; \
		pip install -r requirements/requirements.dev.txt; \
		pip install -r requirements/requirements-test.dev.txt; \
		pip install -e . )

install-from-pypi:
	pip install pyleset

install-from-pypi-all:
	pip install pyleset[all]

develop:
	python setup.py develop

test-requirements:
	rm -rf ./requirements_test/
	python setup.py requirements_test
	ls -al ./requirements_test/

requirements:
	python setup.py requirements
