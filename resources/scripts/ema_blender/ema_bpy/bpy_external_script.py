'''Executes the named script in Blender.'''

import bpy
import os
import sys
print('-------------------------------------------------------------')


def runscript(scriptname):
    """Run a script in the same location as the blend file."""
    prefix = bpy.data.filepath
    globals = {}
    locals = {}
    filename = os.path.join(os.path.dirname(bpy.data.filepath), scriptname)
    exec(compile(open(filename).read(), filename, 'exec'), globals, locals)

def runclient():
    print("about to run client main")
    runscript('rtclient.py')

def deletecubes():
    print("about to delete cubes in fn")
    runscript('delete_added_cubes.py')

def printsomething():
    print('something')

def run_bpy():
    runscript('bpy_emareadin.py')
    
def run_test():
    runscript('temp.py')

if __name__=="__main__":
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if not path in sys.path:
        sys.path.insert(1, path)
    #run_test()
    run_bpy()
    #deletecubes()
    del path
    print(sys.path)