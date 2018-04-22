"""
fahmunge
A tool for automated processing of Folding@home data to produce [mdtraj](http://mdtraj.org)-compatible trajectory sets.
"""

# Make Python 2 and 3 imports work the same
# Safe to remove with Python 3-only code
from __future__ import absolute_import

from . import fah
from . import automation
from . import core21

# versioneer
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
