#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Installation:
    pip install git+https://github.com/urschrei/cli-zotero.git

Developing:
    git clone https://github.com/urschrei/cli-zotero.git
    pip install -e cli-zotero

Pypi:
     # Presetup
     pip install twine

     # First tag the source-code
     VERSION=$(python -c "import setup; print(setup.version)")
     echo $VERSION
     git tag $VERSION -m "tarball tag $VERSION"
     git push --tags origin master

     # NEW API TO UPLOAD TO PYPI
     # https://packaging.python.org/tutorials/distributing-packages/

     # Build wheel or source distribution
     python setup.py bdist_wheel --universal

     # Use twine to upload. This will prompt for username and password
     # If you get an error:
     #   403 Client Error: Invalid or non-existent authentication information.
     # simply try typing your password slower.
     twine upload --username erotemic --skip-existing dist/*

     # Check the url to make sure everything worked
     https://pypi.org/project/cli-zotero/

     # ---------- OLD ----------------
     # Check the url to make sure everything worked
     https://pypi.python.org/pypi?:action=display&name=cli-zotero

"""
from setuptools import setup
import sys


def parse_version(package):
    """
    Statically parse the version number from __init__.py

    CommandLine:
        python -c "import setup; print(setup.parse_version('cli-zotero'))"
    """
    from os.path import dirname, join, exists
    import ast

    # Check if the package is a single-file or multi-file package
    _candiates = [
        join(dirname(__file__), package + '.py'),
        join(dirname(__file__), package, '__init__.py'),
    ]
    _found = [init_fpath for init_fpath in _candiates if exists(init_fpath)]
    if len(_found) > 0:
        init_fpath = _found[0]
    elif len(_found) > 1:
        raise Exception('parse_version found multiple init files')
    elif len(_found) == 0:
        raise Exception('Cannot find package init file')

    with open(init_fpath) as file_:
        sourcecode = file_.read()
    pt = ast.parse(sourcecode)
    class VersionVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if getattr(target, 'id', None) == '__version__':
                    self.version = node.value.s
    visitor = VersionVisitor()
    visitor.visit(pt)
    return visitor.version


def parse_requirements(fname='requirements.txt'):
    """
    Parse the package dependencies listed in a requirements file but strips
    specific versioning information.

    TODO:
        perhaps use https://github.com/davidfischer/requirements-parser instead

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
    """
    from os.path import dirname, join, exists
    import re
    require_fpath = join(dirname(__file__), fname)

    def parse_line(line):
        """
        Parse information from a line in a requirements text file
        """
        info = {}
        if line.startswith('-e '):
            info['package'] = line.split('#egg=')[1]
        else:
            # Remove versioning from the package
            pat = '(' + '|'.join(['>=', '==', '>']) + ')'
            parts = re.split(pat, line, maxsplit=1)
            parts = [p.strip() for p in parts]

            info['package'] = parts[0]
            if len(parts) > 1:
                op, rest = parts[1:]
                if ';' in rest:
                    # Handle platform specific dependencies
                    # http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-platform-specific-dependencies
                    version, platform_deps = map(str.strip, rest.split(';'))
                    info['platform_deps'] = platform_deps
                else:
                    version = rest  # NOQA
                info['version'] = (op, version)
        return info

    # This breaks on pip install, so check that it exists.
    if exists(require_fpath):
        with open(require_fpath, 'r') as f:
            packages = []
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    info = parse_line(line)
                    package = info['package']
                    if not sys.version.startswith('3.4'):
                        # apparently package_deps are broken in 3.4
                        platform_deps = info.get('platform_deps')
                        if platform_deps is not None:
                            package += ';' + platform_deps
                    packages.append(package)
            return packages
    return []

version = parse_version('cli_zotero')  # needs to be a global var for git tags

if __name__ == '__main__':
    setup(
        name='cli_zotero',
        version=version,
        entry_points={
            # the console_scripts entry point creates the xdoctest executable
            'console_scripts': [
                'cli-zotero = cli_zotero:main'
            ]
        },
        install_requires=parse_requirements('requirements.txt'),
    )
