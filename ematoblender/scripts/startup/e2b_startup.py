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

packagedir = os.path.abspath(os.path.dirname(__file__)+'/../../')  # ematoblender directory


def check_saved():
    # is the .blend file saved
    if not bpy.data.is_saved:
        print('The current .blend file must be saved before you can add links to the game script.')
        return False
    else:
        return bpy.path.abspath("//")


def add_to_path():
    # put the ematoblender/scripts directory into sys.path
    print("Now adding {} to sys.path".format(packagedir))
    if packagedir not in sys.path:
        sys.path.append(packagedir)


def add_blenddir_to_path():
    # add the blend file's directory to the path
    blend_dir = os.path.dirname(bpy.data.filepath)
    if blend_dir not in sys.path:
        sys.path.append(blend_dir)


def check_script_access():
    """Check whether the essential bpy_emareadin and bge_emareadin scripts are accessible."""
    try:
        import scripts.ema_shared.properties as pps
        # get the path to the script minus any '.main' suffix
        lessmain = lambda x: x[:-5] if x.endswith('.main') else x
        bpy_script_path, bge_script_path = lessmain(pps.bpy_script_path), lessmain(pps.bge_script_path)
        print('PROPERTIES FILE FOUND, SCRIPT PATHS ARE:', bpy_script_path, bge_script_path)
    except ImportError:
        # these vals are hard-coded and duplicates use for testing if the properties file is not accessible
        bpy_script_path = 'scripts.ema_blender.ema_bpy.bpy_emareadin'
        bge_script_path = 'scripts.ema_blender.ema_bge.bge_emareadin'

    available_modules = [x[0] for x in
                         bpy.path.module_names(os.path.normpath(packagedir), recursive=True)]
    for x in available_modules:
        print(x)

    if bge_script_path not in available_modules:
        print('Warning - the game script is not accessible.')
        raise ImportWarning

    elif bpy_script_path not in available_modules:
        print('Warning - the bpy scene building script is not accessible.')
        raise ImportWarning


def register():
    print("E2B: Starting blender with the Ematoblender add-ons startup process")
    add_to_path()
    check_script_access()
    print('E2B: Registering all the operators used in menus.')
    # register all the operators needed later
    from scripts.ema_blender.bpy_operators.op_connectempties import ParentingOperator
    bpy.utils.register_class(ParentingOperator)

    from scripts.ema_blender.bpy_operators.op_transparentmaterial import TransMatOperator
    bpy.utils.register_class(TransMatOperator)

    from scripts.ema_blender.bpy_operators.ops_bpy_palate_trace import ModalDrawOperator, PalateVertsToMesh
    bpy.utils.register_class(ModalDrawOperator)
    bpy.utils.register_class(PalateVertsToMesh)

    print('E2B: Ematoblender\'s startup process complete')


def unregister():
    print("Ematoblender closing too.")