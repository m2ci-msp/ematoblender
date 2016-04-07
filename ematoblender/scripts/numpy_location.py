# ensure that the script can be executed by python 2
from __future__ import print_function
import imp
print(imp.find_module('numpy')[1], end='')
