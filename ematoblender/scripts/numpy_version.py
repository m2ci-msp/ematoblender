try:
    import numpy
    print(numpy.__version__)
except ImportError:
    print('IMPORT_FAIL')
