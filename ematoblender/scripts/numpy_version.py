# ensure that the script can be executed by python 2
from __future__ import print_function
try:
    import numpy
    print(numpy.__version__, end="")
except ImportError:
    print('IMPORT_FAIL', end="")
