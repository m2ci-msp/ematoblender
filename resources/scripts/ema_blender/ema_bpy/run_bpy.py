import sys
import os
import bpy

# these vals are duplicates, as at this point the pps file may not be accessible
bpy_script_path = 'scripts.ema_blender.ema_bpy.bpy_emareadin'
bge_script_path = 'scripts.ema_blender.ema_bge.bge_emareadin'

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

    # can .blend access ema_bpy.bpy_emareadin?
    elif bge_script_path not in [x[0] for x in bpy.path.module_names(currblendpath, recursive=True)]:
        fail = True
        print('Warning - the game script is not accessible from the file location')
        raise ImportWarning

    # can .blend access ema_bge.bge_emareadin?
    elif bpy_script_path not in [x[0] for x in bpy.path.module_names(currblendpath, recursive=True)]:
        fail = True
        print('Warning - the bpy script you are about to try to build from is inaccessible from the .blend file location.')
    return fail


print('FAILED MODULE TEST:',check_script_access())

from scripts.ema_blender.ema_bpy import bpy_emareadin as be
import importlib as imp
imp.reload(be)
be.main()

print('SCENE CONSTRUCTION COMPLETE')