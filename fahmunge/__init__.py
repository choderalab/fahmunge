from . import fah
from . import automation
from . import core21

# versioneer
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
