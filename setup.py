#!/usr/bin/env python
"""
pyleset/setup.py
"""
from __future__ import print_function
import os
import sys

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

README = open('README.rst').read()
DOCLINK = """
Documentation
-------------

The full documentation is at http://pyleset.rtfd.org."""
HISTORY = open('HISTORY.rst').read().replace('.. :changelog:', '')

PACKAGES = (
    ('structp_pics', {'brew': 'pyexiv2', 'apt': 'python-pyexiv2'}),
)

REQUIREMENTS = (
    ('tests', ['tox', 'pytest', 'coverage']),
    ('docs', ['sphinx']),
    ('pyleset', ['structlog', 'sarge', 'pathlib']),
    ('structp', ['path.py', 'networkx', 'hashlib']),
    ('structp_pics', ['enzyme', 'PyPdf2', 'python-magic']),
)


def merge_items_to_list(value_tuples=REQUIREMENTS):
    """
    flatten a (key, [list]) iterable and preserve source order
    """
    value_set = set()
    value_list = list()
    for key, value in value_tuples:
        for req in value:
            if req not in value_set:
                value_set.add(req)
                yield req

EXTRAS_REQUIRE = dict(REQUIREMENTS)
EXTRAS_REQUIRE['all'] = list(merge_items_to_list(REQUIREMENTS))


def _write_requirements_txt(reqs=REQUIREMENTS, pkgs=PACKAGES):
    """
    Yields:
        str: output strings
    """
    yield ""
    yield "# pip requirements file"

    yield '## system packages'
    for key, packages in pkgs:
        if key != 'all':
            yield ''
            yield ('## %s' % key)
            for pkgmgr, _pkgs in packages.items():  # TODO TODO TODO TODO TODO TODO
                yield "#$ %s install %s" % (pkgmgr, _pkgs)

    for key, requirements in reqs:
        if key != 'all':
            yield ''
            yield ("## %s" % key)
            for req in requirements:
                yield req


def write_requirements_txt(reqs=REQUIREMENTS):
    for line in _write_requirements_txt(reqs=reqs):
        print(line)


class RequirementsCommand(Command):
    """setuptools command"""
    description = "print out a set for requirements.txt"""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        write_requirements_txt()


setup(
    name='pyleset',
    version='0.1.0',
    description='Work with filesets',
    long_description=README + '\n\n' + DOCLINK + '\n\n' + HISTORY,
    author='Wes Turner',
    author_email='wes@wrd.nu',
    url='https://github.com/westurner/pyleset',
    packages=[
        'pyleset',
        'structp',
    ],
    package_dir={
        'pyleset': 'pyleset',
        'structp': 'structp'},
    include_package_data=True,
    install_requires=EXTRAS_REQUIRE['pyleset'],
    tests_require=EXTRAS_REQUIRE['tests'],
    extras_require=EXTRAS_REQUIRE,
    entry_points="""
    [console_scripts]
    pyleset = pyleset.pyleset:main
    structp = structp.structp:main
    structp-pics = structp.pics:main
    """,
    cmdclass={
        'requirements': RequirementsCommand,
    },
    license='MIT',
    zip_safe=False,
    keywords='pyleset structp',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
