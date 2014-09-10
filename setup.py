#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
doclink = """
Documentation
-------------

The full documentation is at http://pyleset.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

install_requires = [
    'structlog',
    'sarge',
    '',
]

setup(
    name='pyleset',
    version='0.0.1',
    description='Work with filesets',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='Wes Turner',
    author_email='wes@wrd.nu',
    url='https://github.com/westurner/pyleset',
    packages=[
        'pyleset',
    ],
    package_dir={'pyleset': 'pyleset'},
    include_package_data=True,
    install_requires=install_requires,
    entry_points="""
    [console_scripts]
    pyleset = pyleset.pyleset:main
    """,
    license='MIT',
    zip_safe=False,
    keywords='pyleset',
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
