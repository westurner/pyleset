#!/usr/bin/env python
"""
pyleset/setup.py
"""
from __future__ import print_function
import codecs
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
DOCLINK = ""
HISTORY = open('HISTORY.rst').read().replace('.. :changelog:', '')

# requirements.txt
import collections
import itertools
import urllib
try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

REQUIREMENT_FIELDS = ('name', 'editable', 'version', 'vcs')
_Requirement = collections.namedtuple('Requirement', REQUIREMENT_FIELDS)


class Requirement(_Requirement):

    """A pip requirement"""

    def __new__(self, *args, **kwargs):
        for key, arg in itertools.izip_longest(REQUIREMENT_FIELDS, args):
            if arg:
                kwargs[key] = arg
            else:
                kwargs[key] = kwargs.get(key, None)
        if not kwargs.get('vcs'):
            kwargs['vcs'] = self.determine_vcs(kwargs.get('editable'))
        return super(self, Requirement).__new__(self, **kwargs)

    def pip_requirement_str(self):
        """
        Returns:
            str: Requirement name string (e.g. ``pyleset``)
        """
        return u"%s" % self.name

    def pip_requirement_version_str(self):
        """
        Returns:
            str: Requirement name/version string (e.g. ``pyleset ==0.1.0``)
                 or just the requirement name if no version is specified
        """
        version = self.version
        if not version:
            return self.pip_requirement_str()
        return u"%s %s" % (self.name, self.version)

    def pip_requirement_editable_str(self):
        """
        Returns:
            str: Requirement pip editable string
                 (e.g. ``-e git+https://github.com/westurner/pyleset``)
                 or just the requirement name/version string if no
                 vcs/editable url is specified.
        """
        if not self.editable or not self.vcs:
            return self.pip_requirement_version_str()
        return u"-e %s+%s#egg=%s" % (self.vcs, self.editable, self.name)

    @staticmethod
    def determine_vcs(url):
        """
        Guess which VCS a URL points to

        Args:
            url (str): URL to an editable repository

        Returns:
            str or None: vcs name (``git``, ``hg``, ``bzr``, ``svn``, ``cvs``)
        """
        if not url:
            return None
        scheme, rest = urllib.splittype(url)
        host, _rest = urllib.splithost(rest)
        if scheme == 'ssh':
            if host.startswith('git@'):
                return 'git'
            if host.startswith('hg@'):
                return 'hg'
        if scheme in ('https', 'http'):
            if host.endswith('github.com'):
                return 'git'
        if scheme in ('git', 'hg', 'bzr', 'svn', 'cvs'):
            return scheme
        return None


PACKAGES = [
    ('structp_pics', {'brew': 'pyexiv2', 'apt-get': 'python-pyexiv2'}),
]

REQUIREMENTS = (
    ('pyleset', [
        Requirement('structlog',
                    'https://github.com/hynek/structlog'),
        Requirement('sarge',
                    'https://bitbucket.org/vinay.sajip/sarge',
                     vcs='hg'),
        Requirement('pathlib',
                    'https://bitbucket.org/pitrou/pathlib'),
    ]),
    ('structp', [
        Requirement('path.py',
                    'https://github.com/jaraco/path.py'),
        Requirement('networkx',
                    'https://github.com/networkx/networkx'),
    ]),
    ('structp_pics', [
        Requirement('enzyme',
                    'https://github.com/Diaoul/enzyme'),
        Requirement('PyPdf2',
                    'https://github.com/mstamy2/PyPDF2'),
        Requirement('python-magic',
                    'https://github.com/ahupp/python-magic'),
    ]),
)

TEST_REQUIREMENTS = (
    ('tests', [
        # Requirement('tox'),
        Requirement('pytest',
                    'https://bitbucket.org/hpk42/pytest',
                    vcs='hg'),
        Requirement('coverage',
                    'https://bitbucket.org/ned/coveragepy',
                    vcs='hg',
                    # git_'https://github.com/nedbat/coveragepy' #
                    # mirror
                    ),
    ]),
    ('docs', [
        Requirement('sphinx',
                    'https://bitbucket.org/birkenfeld/sphinx',
                    vcs='hg',
                    ),
    ]),
)


class RequirementsMap():

    """Methods for working with requiment sets as
    ``OrderedDict((key, [list])``"""

    @classmethod
    def get_requirements(cls, tests_require=None, extras_require=None):
        """
        Make setuptools-compatible tests_require list and extras_require dict
        """
        _tests_require = []
        _extras_require = {}
        if tests_require:
            _tests_require = list(cls.to_list(tests_require))
        if extras_require:
            _extras_require = cls.to_setuptools_dict(extras_require)
            _extras_require['all'] = list(cls.to_list(extras_require))
        return _tests_require, _extras_require

    @staticmethod
    def to_list(value_tuples=REQUIREMENTS):
        """
        Merge/flatten a (key, [list]) iterable in order, removing uniques

        Yields:
            str: unique (first-instance) package names
        """
        value_set = set()
        for key, value in value_tuples:
            for req in value:
                if req.name not in value_set:
                    value_set.add(req.name)
                    yield req.name  # pip_requirement_version_str()
                else:
                    print('# duplicate: %s' % str(req))

    @staticmethod
    def to_setuptools_dict(requirements):
        """
        Create a setuptols extras_require dict

        Returns:
            OrderedDict: {'section': ['re','quire','ments']}
        """
        def _to_dict(_requirements):
            for key, requirements_list in _requirements:
                yield (key, [req.pip_requirement_version_str()
                             for req in requirements_list])
        return OrderedDict(_to_dict(requirements))

    @staticmethod
    def generate_packages_txt(pkgs):
        """
        Generate a commented pip requirements header for system packages

        Yields:
            str: text lines
        """
        if not pkgs:
            return
        yield '### system packages'
        for key, packages in pkgs:
            if key != 'all':
                yield ('## %s' % key)
                if packages:
                    for pkgmgr, _pkgs in packages.items():  # TODO TODO
                        yield "#$ %s install %s" % (pkgmgr, _pkgs)
                    yield ''
        yield ''

    @staticmethod
    def generate_requirements_txt(reqs, editable=False):
        """
        Generate a documented requirements.txt file

        Args:
            reqs (dict): {'section': [Requirement,]}

        Yields:
            str: text lines
        """
        if not reqs:
            return
        requirement_func = Requirement.pip_requirement_version_str
        if editable:
            requirement_func = Requirement.pip_requirement_editable_str
        yield "### pip packages"
        for key, requirements in reqs:
            if key != 'all':
                if requirements:
                    yield ("## %s" % key)
                    for req in requirements:
                        yield requirement_func(req)
                    yield ''

    @classmethod
    def write_requirements(cls, reqs=None, pkgs=None, editable=False):
        """
        Generate a pip requirements.txt for specified requirements and packages

        Keyword Arguments:
            reqs (dict): {'section': [Requirement,]}
            pkgs (dict): {'section': {'pkgmgr': 'pkgname',}}
            editable (bool): write editable package strings (if possible)

        Yields:
            str: requirements.txt text blocks (possibly containing newlines)
        """
        yield "#"*72
        yield "#### pip requirements file"
        if pkgs:
            for block in cls.generate_packages_txt(pkgs):
                yield block
        if reqs:
            for block in cls.generate_requirements_txt(reqs, editable=editable):
                yield block
        yield ""

    @classmethod
    def print_requirements(cls,
                            reqs=None,
                            pkgs=None,
                            editable=False,
                            file=sys.stdout,
                            tee=False):
        """
        Print requirements.txt to the specified file (sys.stdout by default)

        Args:
            reqs (dict): {'section': [Requirement,]}
            pkgs (dict): {'section': {'pkgmgr': 'pkgname',}}
            editable (bool): write editable package strings (if possible)
            file (filelike): file to print lines to

        Returns:
            None
        """
        for line in cls.write_requirements(
                reqs=reqs,
                pkgs=pkgs,
                editable=editable):
            print(line, file=file)
            if tee and file is not sys.stdout:
                print(line, file=sys.stdout)

    @classmethod
    def write_requirements_dir(cls, path,
                               test_requirements=None,
                               requirements=None,
                               packages=None,
                               tee=False):
        """
        Write a directory of requirements/requirements[-name][.dev].txt files

        Args:
            path (str): path to create and write requirements.txt files into

        Keyword Arguments:
            test_requirements (dict): {'section': [Requirement,]}
            requirements (dict): {'section': [Requirement,]}
            pkgs (dict): {'section': {'pkgmgr': 'pkgname',}}

        Returns:
            str: path to directory
        """
        if not os.path.exists(path):
            os.makedirs(path)

        requirements = requirements or {}
        #requirements_dict = OrderedDict(requirements)

        packages = packages or {}
        try:
            packages_dict = OrderedDict(packages)
        except ValueError:
            print(packages)
            packages_dict = OrderedDict(*list(packages))
            raise

        # requirements.txt
        filename = os.path.join(path, 'requirements.txt')
        print("writing: %s" % filename)
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            cls.print_requirements(
                requirements, packages, file=f, tee=tee)

        # requirements.dev.txt
        print("writing: %s" % filename)
        filename = os.path.join(path, 'requirements.dev.txt')
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            cls.print_requirements(
                requirements, packages, editable=True, file=f, tee=tee)

        # requirements-test.txt
        filename = os.path.join(path, 'requirements-test.txt')
        print("writing: %s" % filename)
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            cls.print_requirements(
                test_requirements, file=f, tee=tee)

        # requirements-test.dev.txt
        filename = os.path.join(path, 'requirements-test.dev.txt')
        print("writing: %s" % filename)
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            cls.print_requirements(
                test_requirements, editable=True, file=f, tee=tee)

        file_pairs = (
            ('', requirements),
            ('-test-', test_requirements))

        # requirements[-name][-section][-dev].txt
        for name, requirements_variable in file_pairs:
            for section, _requirements in requirements_variable:
                _section_packages = packages_dict.get(section, {})
                if _section_packages:
                    _packages = (
                        (section, _section_packages),)
                else:
                    _packages = tuple()
                __requirements = (
                    (section, _requirements),)

                filename = os.path.join(
                    path, 'requirements--%s%s.txt' % (name, section))
                print("writing: %s" % filename)
                with codecs.open(filename, 'w', encoding='utf-8') as f:
                    cls.print_requirements(
                        __requirements, _packages, file=f, tee=tee)

                filename = os.path.join(
                    path, 'requirements--%s%s.dev.txt' % (name, section))
                print("writing: %s" % filename)
                with codecs.open(filename, 'w', encoding='utf-8') as f:
                    cls.print_requirements(
                        __requirements,
                        _packages,
                        editable=True,
                        file=f,
                        tee=tee)

        return path


TESTS_REQUIRE, EXTRAS_REQUIRE = RequirementsMap.get_requirements(
    TEST_REQUIREMENTS, REQUIREMENTS)


class TestRequirementsTxt(object):

    """
    Test Requirements and RequirementsMap functionality
    """

    EDITABLE_URL = 'https://github.com/westurner/pyleset'

    def test(self, stop_on_error=False):
        if hasattr(self, 'setUp'):
            self.setUp()
        for attr in dir(self):
            if not attr.startswith('test_'):
                continue
            print("#"*72)
            print("### <%s>" % attr)
            func = getattr(self, attr)
            try:
                output = func()
                print("### output:", output)
            except Exception as e:
                print('### ERROR')
                print(e)
                if stop_on_error:
                    raise
                else:
                    print(__import__('traceback').format_exc())
                pass
            finally:
                print("### </%s>" % attr)
        if hasattr(self, 'tearDown'):
            self.tearDown()

    def test_01_determine_vcs(self):
        for url in [
                self.EDITABLE_URL,
                'git://github.com/westurner/pyleset',
                'http://github.com/westurner/pyleset',
                'https://github.com/westurner/pyleset',
                'ssh://git@github.com/westurner/pyleset']:
            vcs = Requirement.determine_vcs(url)
            print(vcs)
            assert vcs == 'git'
        for url in [
                'hg://bitbucket.org/westurner/pyleset',
                'ssh://hg@bitbucket.org/westurner/pyleset']:
            vcs = Requirement.determine_vcs(url)
            print(vcs)
            assert vcs == 'hg'
        for url in [
                'bzr://launchpad.com/~westurner/pyleset']:
            vcs = Requirement.determine_vcs(url)
            print(vcs)
            assert vcs == 'bzr'
        for url in [
                'svn://svn.googlecode.com/westurner/pyleset',
                'svn://svn.sourceforge.net/westurner/pyleset']:
            vcs = Requirement.determine_vcs(url)
            print(vcs)
            assert vcs == 'svn'

    def test_02_requires_dicts(self):
        tests_require, extras_require = RequirementsMap.get_requirements(
            TEST_REQUIREMENTS,
            REQUIREMENTS)
        assert isinstance(tests_require, list)
        assert isinstance(extras_require, (dict, OrderedDict))

        import json
        print("## TESTS_REQUIRE")
        print(json.dumps(tests_require, indent=2))
        print("## EXTRAS_REQUIRE")
        print(json.dumps(extras_require, indent=2))

    def test_10_Requirement(self):
        editable_url = self.EDITABLE_URL
        r = Requirement('pyleset')
        print(r)
        assert r
        assert r.name == 'pyleset'
        assert r.version is None
        assert r.vcs is None
        assert r.editable is None
        r = Requirement('pyleset', version='==0.1.0')
        print(r)
        assert r
        assert r.name == 'pyleset'
        assert r.version == '==0.1.0'
        assert r.vcs is None
        assert r.editable is None
        r = Requirement('pyleset', editable_url, '==0.1.0', 'git')
        print(r)
        assert r
        assert r.name == 'pyleset'
        assert r.version == '==0.1.0'
        assert r.vcs == 'git'
        assert r.editable == editable_url
        r = Requirement('pyleset', editable_url, '==0.1.0')
        print(r)
        assert r
        assert r.name == 'pyleset'
        assert r.version == '==0.1.0'
        assert r.vcs == 'git'
        assert r.editable == editable_url

    def test_11_Requirement_strings(self):
        editable_url = self.EDITABLE_URL
        r = Requirement('pyleset', editable_url, '==0.1.0')
        print(r)
        assert r
        _str = r.pip_requirement_str()
        print(_str)
        assert _str == 'pyleset'
        _str = r.pip_requirement_version_str()
        print(_str)
        assert _str == 'pyleset ==0.1.0'
        _str = r.pip_requirement_editable_str()
        print(_str)
        assert _str == (
            '-e git+https://github.com/westurner/pyleset#egg=pyleset')

    def test_20_pip_requirements(self):
        cls = RequirementsMap
        requirements = REQUIREMENTS
        test_requirements = TEST_REQUIREMENTS
        packages = PACKAGES
        output = cls.print_requirements()
        output = cls.print_requirements(editable=True)

        output = cls.print_requirements(requirements)
        output = cls.print_requirements(requirements, editable=True)
        output = cls.print_requirements(requirements, packages)
        output = cls.print_requirements(requirements, packages, editable=True)

        output = cls.print_requirements(test_requirements)
        output = cls.print_requirements(test_requirements, editable=True)
        output = cls.print_requirements(test_requirements, packages)
        output = cls.print_requirements(test_requirements, packages,
                                        editable=True)
        output

    def test_30_write_pip_requirements_dir(self):
        path = 'build/requirements_test'
        requirements = REQUIREMENTS
        test_requirements = TEST_REQUIREMENTS
        packages = PACKAGES
        output = RequirementsMap.write_requirements_dir(
            path,
            test_requirements=test_requirements,
            requirements=requirements,
            packages=packages,
            tee=True)
        assert output


class RequirementsCommand(Command):

    """setuptools command"""
    description = "Generate requirements.txt and ./requirements/"""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # ./requirements.txt
        RequirementsMap.print_requirements(REQUIREMENTS, PACKAGES)

        # ./requirements/requirements[-test][.dev].txt
        RequirementsMap.write_requirements_dir(
            'requirements',
            test_requirements=TEST_REQUIREMENTS,
            requirements=REQUIREMENTS,
            packages=PACKAGES)


class RequirementsTestCommand(Command):

    """setuptools command"""
    description = "Run requirements.txt tests"""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        tests = TestRequirementsTxt()
        tests.test(stop_on_error=True)
        # return unittest.main()


setup(
    name='pyleset',
    version='0.1.0',
    description='Work with filesets as graphs with attributes.',
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
    tests_require=TESTS_REQUIRE,
    extras_require=EXTRAS_REQUIRE,
    entry_points="""
    [console_scripts]
    pyleset = pyleset.pyleset:main
    structp = structp.structp:main
    structp-pics = structp.pics:main
    """,
    cmdclass={
        'requirements': RequirementsCommand,
        'requirements_test': RequirementsTestCommand,
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
