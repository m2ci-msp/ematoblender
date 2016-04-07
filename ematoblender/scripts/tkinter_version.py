# ensure that the script can be executed by python 2
from __future__ import print_function
try:
    import tkinter
    print('SUCCESS', end="")
except ImportError:
    print('IMPORT_FAIL', end="")
