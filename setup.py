import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'setuptools',
    'networkx',
    #'pyramid',
    #'SQLAlchemy',
    #'transaction',
    #'repoze.tm2>=1.0b1', # default_commit_veto
    #'zope.sqlalchemy',
    #'WebError',
    #'pyramid_simpleform',
    #'pyramid_jinja2',
    #'Jinja2',
    #'cryptacular',
]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='structp',
    version='0.0.1',
    description='',
    long_description=README + '\n\n' +  CHANGES,
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        #"Topic :: Internet :: WWW/HTTP",
        #"Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        #"Topic :: Internet :: WWW/HTTP :: WSGI",
        #"Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
    license="New BSD",
    packages=find_packages(exclude=['tests', 'testdata']),
    include_package_data=True,
    package_data={
        'structp': ['testdata/*'],
        },
    zip_safe=False,
    test_suite='structp.tests',
    install_requires = requires,
    entry_points={
        'console_scripts':[
            'three = structp:main',
            ],
    }

    #[paste.app_factory]
    #main = structp:main
    #""",
    #paster_plugins=['pyramid'],
)


