=============================
pyleset
=============================

.... image:: https://badge.fury.io/py/pyleset.png
    ..:target: http://badge.fury.io/py/pyleset

.... image:: https://travis-ci.org/westurner/pyleset.png?branch=master
    ..:target: https://travis-ci.org/westurner/pyleset

.... image:: https://pypip.in/d/pyleset/badge.png
    ..:target: https://pypi.python.org/pypi/pyleset


A tool for working with filesets as graphs with attributes.


Features
--------

pyleset
~~~~~~~~
Move filesets matching patterns into directories

* ``pyleset --move`` -- move files into folders with a glob pattern
* ``--numbered`` -- files into folders with a glob pattern
* Write changes to disk (``-w`` -> ``write_changes=True``)  

structp
~~~~~~~~
Search filesystem graphs

* scan filesystem paths into graphs (networkx)
* find duplicate files (hashlib)
* diff directory graphs
* save graphs to ``.nxpkl`` files

structp-pics
~~~~~~~~~~~~~~
Extract file metadata

* read EXIF image file metadata (pyexiv2)
* read video file metadata (enzyme)
* read PDF document metadata (PyPdf2)  
* ``yield`` streams of ``('attribute', 'value')`` tuples 


Requirements
--------------

See: `requirements-all.txt <https://github.com/westurner/pyleset/blob/release/0.1.0/requirements-all.txt>`_

.. code::

    # pip requirements file
    ## system packages

    ## structp_pics
    #$ brew install pyexiv2
    #$ apt install python-pyexiv2

    ## tests
    tox
    pytest
    coverage

    ## docs
    sphinx

    ## pyleset
    structlog
    sarge
    pathlib

    ## structp
    path.py
    networkx
    hashlib

    ## structp_pics
    enzyme
    PyPdf2
    python-magic


Install
--------
Install `pyleset`:

.. code:: bash

    pip install -e https://github.com/westurner/pyleset@release/0.1.0#egg=pyleset

Optional: Install complete set of dependencies for `structp` and
`structp-pics`.

.. code:: bash

   cd ${VIRTUAL_ENV}/src/pyleset
   $EDITOR Makefile
   pip install -r requirements-all.txt  # (pip install pyleset[all])


Usage
-------
* ``pyleset --help``
* ``structp --help``
* ``structp-pics --help``

