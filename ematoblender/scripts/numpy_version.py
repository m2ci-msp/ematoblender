try:
    import numpy
    print(numpy.__version__, end="")
except ImportError:
    print('IMPORT_FAIL', end="")
