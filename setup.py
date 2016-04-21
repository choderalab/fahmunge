"""Some tools for munging FAH trajectories
"""

from __future__ import print_function

DOCLINES = __doc__.split("\n")

import os
import sys
import shutil
import tempfile
import subprocess
import versioneer
from distutils.ccompiler import new_compiler

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

CLASSIFIERS = """\
Development Status :: 3 - Alpha
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)
Programming Language :: C
Programming Language :: Python
Programming Language :: Python :: 3
Topic :: Scientific/Engineering :: Bio-Informatics
Topic :: Scientific/Engineering :: Chemistry
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

def find_packages():
    """Find all of fahmunge's python packages.
    Adapted from IPython's setupbase.py. Copyright IPython
    contributors, licensed under the BSD license.
    """
    packages = []
    for dir,subdirs,files in os.walk('fahmunge'):
        package = dir.replace(os.path.sep, '.')
        if '__init__.py' not in files:
            # not a package
            continue
        packages.append(package.replace('fahmunge', 'fahmunge'))
    return packages


################################################################################
# Writing version control information to the module
################################################################################

def git_version():
    # Return the git revision as a string
    # copied from numpy setup.py
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        GIT_REVISION = out.strip().decode('ascii')
    except OSError:
        GIT_REVISION = 'Unknown'

    return GIT_REVISION


def write_version_py(filename='fahmunge/version.py'):
    cnt = """
# THIS FILE IS GENERATED FROM fahmunge SETUP.PY
short_version = '%(version)s'
version = '%(version)s'
full_version = '%(full_version)s'
git_revision = '%(git_revision)s'
release = %(isrelease)s

if not release:
    version = full_version
"""
    # Adding the git rev number needs to be done inside write_version_py(),
    # otherwise the import of numpy.version messes up the build under Python 3.
    FULLVERSION = VERSION
    if os.path.exists('.git'):
        GIT_REVISION = git_version()
    else:
        GIT_REVISION = 'Unknown'

    if not ISRELEASED:
        FULLVERSION += '.dev-' + GIT_REVISION[:7]

    a = open(filename, 'w')
    try:
        a.write(cnt % {'version': VERSION,
                       'full_version': FULLVERSION,
                       'git_revision': GIT_REVISION,
                       'isrelease': str(ISRELEASED)})
    finally:
        a.close()

setup_kwargs = {}

from distutils.command.clean import clean as Clean
class CleanCommand(Clean):
    """python setup.py clean
    """
    # lightly adapted from scikit-learn package
    # adapted again from parmed
    description = "Remove build artifacts from the source tree"

    def _clean(self, folder):
        for dirpath, dirnames, filenames in os.walk(folder):
            for filename in filenames:
                if (filename.endswith('.so') or filename.endswith('.pyd')
                        or filename.endswith('.dll')
                        or filename.endswith('.pyc')):
                    os.unlink(os.path.join(dirpath, filename))
            for dirname in dirnames:
                if dirname == '__pycache__':
                    shutil.rmtree(os.path.join(dirpath, dirname))

    def run(self):
        Clean.run(self)
        if os.path.exists('build'):
            shutil.rmtree('build')
        self._clean('fahmunge')
        self._clean('test')
cmdclass = dict(clean=CleanCommand)
cmdclass.update(versioneer.get_cmdclass())

setup(name='fahmunge',
      author='Kyle A. Beauchamp',
      author_email='kyleabeauchamp@gmail.com',
      zip_safe=False,
      description=DOCLINES[0],
      long_description="\n".join(DOCLINES[2:]),
      version=versioneer.get_version(),
      license='LGPLv2.1+',
      download_url = "https://github.com/FoldingAtHome/FAHMunge/releases/latest",
      platforms=['Linux'],
      classifiers=CLASSIFIERS.splitlines(),
      packages=["fahmunge"],
      package_dir={'fahmunge': 'fahmunge'},
      **setup_kwargs)
