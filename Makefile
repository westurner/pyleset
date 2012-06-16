PACKAGE     = package
PYSETUP     = ./setup.py
PYBIN       = `/usr/bin/env python`

all: test

test:
    $(PYBIN) $(PYSETUP) test


