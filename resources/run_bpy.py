import sys
import os
import bpy

'''
This script is to be opened in Blender in the text editor area, and you can configure this to display on opening any new Blend files.
It is used to check that all the required scripts are available before running the scene-building and game-engine scripts.
It may be that the properties file is not accessible, if the script is included in the Startup File.
Thus it tries to access the bpy and bge scripts directly, eg not from the properties folder, if this fails.

By pressing Alt+P when the cursor is in the text window, this script and the scene-building script are executed.
It also reloads the bpy module on each execution so if you make modifications to bpy_emareadin these should execute.
'''

def check_script_access():
    fail=False
    currblendpath = bpy.path.abspath("//")
    # is the .blend file saved
    if not bpy.data.is_saved:
        print('The current .blend file must be saved before you can add links to the game script.')
        fail = True
        # note: if still necessary can use bpy.ops.wm.save_as_mainfile() to save the blend in a ancestor directory
        # see http://www.blender.org/api/blender_python_api_2_74_5/bpy.ops.wm.html?highlight=wm#module-bpy.ops.wm
        raise FileNotFoundError

    # add the blend file's directory to the path
    blend_dir = os.path.dirname(bpy.data.filepath)
    if blend_dir not in sys.path:
        sys.path.append(blend_dir)

    try:
        import scripts.ema_shared.properties as pps
        # get the path to the script minus any '.main' suffix
        lessmain = lambda x: x[:-5] if x.endswith('.main') else x
        bpy_script_path = lessmain(pps.bpy_script_path)
        bge_script_path = lessmain(pps.bge_script_path)
        print('PROPERTIES FILE FOUND, SCRIPT PATHS ARE:', bpy_script_path, bge_script_path)
    except ImportError:
        # these vals are hard-coded and duplicates use for testing if the properties file is not accessible
        bpy_script_path = 'scripts.ema_blender.ema_bpy.bpy_emareadin'
        bge_script_path = 'scripts.ema_blender.ema_bge.bge_emareadin'

    # can .blend access ema_bpy.bpy_emareadin?
    if bge_script_path not in [x[0] for x in bpy.path.module_names(currblendpath, recursive=True)]:
        fail = True
        print('Warning - the game script is not accessible from the file location')
        raise ImportWarning

    # can .blend access ema_bge.bge_emareadin?
    elif bpy_script_path not in [x[0] for x in bpy.path.module_names(currblendpath, recursive=True)]:
        fail = True
        print('Warning - the bpy script you are about to try to build from is inaccessible from the .blend file location.')

    return fail

print('\n----------------------------------------')
print('EXECUTING THE EMATOBLENDER BUILD PROCESS')
print('PASSED MODULE TEST T/F:', not check_script_access(), '\n')

# load and reload the bpy build script in case changes made
import importlib as imp
from scripts.ema_blender.ema_bpy import bpy_emareadin as be
imp.reload(be)

be.main()