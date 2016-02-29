__author__ = 'Kristy'

'''Script that controls setting up the scene in Blender, using bpy module.
You can access this script manually (not as an add-on) by copying the run_bpy.py script into the text editor and running.'''
#TODO: Explain where the .blend file must be saved to access this.


# Blender essentials
import mathutils
import bpy
import math
import time
import importlib

# shared functions with bge, connectivity with outside server
from . import bpy_add_game_objects as ago
from . import bpy_import_assets as ia
from . import bpy_link_assets_coils as lac
from . import bpy_setup_armatures as sa
from . import bpy_setup_cameras as cam
from . import bpy_setup_meshes as sm
from . import bpy_setup_sound as ss
from . import bpy_splines as spl
from . import bpy_workspace as ws
from . import bpy_move_objects as mo
from . import bpy_static_video as vid

from scripts.ema_blender import coil_info as ci
from scripts.ema_blender import blender_shared_objects as bsh
from scripts.ema_blender import coord_transforms as ct
from scripts.ema_blender import blender_networking as bn

from scripts.ema_shared import miscellanous as misc
from scripts.ema_shared import properties as pps
from scripts.ema_shared import general_maths as bm
from scripts.ema_shared.miscellanous import reload_modules_for_testing


def main():
    # to test:  sa,  spl,
    if pps.development_mode: # put here the namespaces that are changing during editing session
        reload_modules_for_testing(spl, ws, ago, cam, pps, ia, lac, bsh, misc, mo, bn, sm, ss, ci, vid, ct, bm)

    print('BUILDING BLENDER-INTERNAL OBJECTS')
    ago.add_game_master()  # must be first in the process, as some other functions refer to this object
    ws.set_workspace_properties()
    ws.set_texture_view()

    # spawn default coil-cubes and empties
    ago.spawn_hidden_coils(bsh.ema_mesh_name_rule)
    # spawn cubes that automatically follow behaviour of other cubes
    ago.spawn_inferred_coil('SL_L', 'only_positive_axis', 'SL', 'X')
    ago.spawn_inferred_coil('SL_R', 'mirror_axis', "SL_L", "X")
    ago.spawn_inferred_coil('TR', 'take_midpoint', "MR", "ML")

    vid.create_video_plane()
    cam.add_circling_camera()
    cam.add_midsaggital_camera()
    cam.add_frontal_camera()

    # set background and shadow colours in BGE
    bpy.context.scene.world.ambient_color = pps.game_background_color
    bpy.context.scene.world.horizon_color = pps.game_contrast_color

    print('COLLECTING EXTERNAL COIL INFORMATION')
    ci.get_sensor_roles()
    ago.recolor_for_roles()

    use_networking = True  # set as false if debugging Blender without the server on
    if use_networking:
        bsh.gs_soc_blocking = bn.setup_socket_to_gameserver(blocking=True)
        print('TYPE OF SOC_BLOCKING', bsh.gs_soc_blocking)
        # here: debugging networking stuff
        print('PERFORMING NETWORKING WITH SERVER FOR BUILDING')
        print(bn.get_test_response(bsh.gs_soc_blocking))

        # show the next dataframe
        print('Showing initial dataframe')
        params, firstdf = bn.get_live_setup_data()  # makes bp recording
        print('Parameters are:', params)
        mo.show_all_coils_in_position(firstdf)
        mo.show_inferred_coils_in_position()


    print('LOADING EXTERNALLY CONSTRUCTED ASSETS')
    ia.add_statusbar_scene()    # add status bar and webcam image
    ia.add_menu_scene()         # add the popup menu scene

    try:
        ia.add_external_lips_rig()  # add the lips rig
        lac.link_lips_to_coils()
    except Exception as e:
        print('Something went wrong importing lips:', e)

    try:
        ia.add_external_rigged_tongue()  # add the tongue rig
        ct.bpy_move_tongue_to_coils()
        ###sm.set_tongue_physics()
    except Exception as e:
        print("Something went wrong importing tongue", e)

    print('MANIPULATING EXTERNAL ASSETS TO FIT POSITIONAL DATA')
    #TODO: FIRSTLY SCALE ITEMS APPROPRIATELY: EG TO FIT ST SL-UL IS SAME SIZE AS COILS' SL_UL

    # final steps
    ago.make_all_objs_backface_culled()

if __name__ == "__main__":
    testing = True
    main()
