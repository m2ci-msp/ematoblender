from . import scripts  # imports WrapperPackage/packageA
import sys
sys.modules['scripts'] = scripts  # creates a scripts entry in sys.modules
