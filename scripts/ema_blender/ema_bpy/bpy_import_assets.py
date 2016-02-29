__author__ = 'Kristy'

import bpy
import math
import mathutils
import re, os, copy
from .bpy_workspace import postfn_gamemaster_reset_decorator, prefn_gamemaster_select_decorator
from scripts.ema_shared import properties as pps
from scripts.ema_blender.ema_bpy.bpy_setup_cameras import delete_standard_camera
import scripts.ema_blender.coil_info as ci

##########################################################################
##                    GENERAL IMPORT FUNCTIONS
##########################################################################

'''Note when importing, as the kwargs are hard to decode:
filepath: the name of the blend file, with .blend suffix. Eg `myblend.blend`
filename/meshname: the name of the object to be imported. Eg `MyScene` or `Cube.001`
directory: The absolute path to the object, beginning with the path to the blend, then the blend filename, then the folder within.
 Eg `C:\\Foo\\myblend.blend\\Scene`
 '''


def append_item_from_rel_path(blenderfile=None, itemname=None, relpath=None, locationinblend=None):
    """Blenderfile is foo.blend, itemname is the name of the item to be appended,
    locationinblend is the path within the blend to reach the asset's directory,
    relpath the path to the folder with the asset's blend file from the active blend file."""
    currblendpath = bpy.path.abspath("//")
    abspath = os.path.join(currblendpath, relpath)
    abspath = os.path.normpath(abspath)
    finalpath = abspath + os.path.sep + blenderfile + os.path.sep + locationinblend + os.path.sep
    blenderfile = re.sub('^\.\/', '', blenderfile)
    bpy.ops.wm.append(filepath=blenderfile, filename=itemname, directory=finalpath)


def append_item_from_abs_path(blenderfile=None, itemname=None, abspath=None, locationinblend=None):
    """Blenderfile is foo.blend, itemname is the name of the item to be appended,
    locationinblend is the path within the blend to reach the asset's directory,
    abspath the absolute path to the folder with the asset's blend file."""
    abspath = os.path.normpath(abspath)
    finalpath = abspath + os.path.sep + blenderfile + os.path.sep + locationinblend + os.path.sep
    print(finalpath)
    bpy.ops.wm.append(filepath=blenderfile, filename=itemname, directory=finalpath)


@postfn_gamemaster_reset_decorator
def grab_scene_contents(*objectnames, targetlayers=(1, 2), targetscenename='Scene', originscenename='Scene.001',
                        deleteoriginscene=True, deletedefaultcams=True):
    """Take either the entire contents or just the objects from the originscene, put them in the targetscene.
    The current convention is that imported objects should be on layers 1 and 2.
    """
    #print('Now grabbing contents from scene called "{}" into scene called "{}".'.format(originscenename, targetscenename))

    transferred_objects = []

    # deselect objects in target scene
    bpy.ops.object.select_all(action='DESELECT')

    # save the original scene context to reset to afterwards
    orig_context = bpy.context.screen.scene

    # switch to the other scene
    oldscene = bpy.data.scenes[originscenename]
    newscene = bpy.data.scenes[targetscenename]
    bpy.context.screen.scene = oldscene
    #print("The new context scene is:", bpy.context.scene)
    #bpy.context.scene = bpy.data.scenes[originscenename]
    #print(bpy.context.screen.scene, " is the scene being shown now.")

    print("These are the objects in the scene that is being extracted from:", [x for x in oldscene.objects])
    for obj in oldscene.objects:

        # if objectnames is given, only select these items
        if len(objectnames) > 0:
            #print('Manually entered object names are:', objectnames)
            obj.select = True if obj.name in objectnames else False

        # if no names given, select all the items in the scene
        else:
            #print('Linking this one object called', obj.name)
            transferred_objects.append(obj)
            newscene.objects.link(obj)
            newscene.objects.active = obj
            obj.select = True
            # set the visibility
            for i in range(0,20):
                obj.layers[i] = True if i+1 in targetlayers else False
            #print(obj.layers)

    # deselect the transferred objects
    for obj in transferred_objects:
        #print(bpy.data.scenes[targetscenename].get(obj.name, 'obj not yet linked'))
        obj.select = False

    # switch the context back
    bpy.context.screen.scene = orig_context


    if deleteoriginscene:
        bpy.data.scenes.remove(bpy.data.scenes[originscenename])

    if deletedefaultcams:
        delete_standard_camera()

    #print('Now linked objects', transferred_objects)
    return transferred_objects


##########################################################################
##                 IMPORT SPECIFIC SCENES AND ASSETS
##########################################################################


@postfn_gamemaster_reset_decorator
@prefn_gamemaster_select_decorator
def add_statusbar_scene():
    """Import a text scene from the current directory. This will be used to set status updates, show webcam etc.
    Because it shows continually and thus is not controlled by the HIFREQ logic brick, place an additional logic
    brick on the CircularCamera to show it always.
    TODO: In future this could simply use the main game script and trigger at a lesser interval.
    """
    append_item_from_rel_path(blenderfile=pps.statusbar_dot_blend,
                              itemname=pps.name_of_statusbar_object,
                              relpath=pps.rel_loc_of_statusbar_dot_blend,
                              locationinblend=pps.path_to_statusbar_in_dot_blend)

    # switch back to default scene after adding new one
    bpy.context.screen.scene=bpy.data.scenes['Scene']
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # get the circling camera object, it is on this that the scene is overlaid
    from scripts.ema_blender.blender_shared_objects import circling_cam
    camname = circling_cam.name

    # add a low-frequency sensor logic brick to the camera
    bpy.ops.logic.sensor_add(type='ALWAYS', name='LOWFREQ', object=camname)
    lowfreq_sensor = circling_cam.game.sensors['LOWFREQ']
    lowfreq_sensor.use_tap = True
    lowfreq_sensor.use_pulse_false_level, lowfreq_sensor.use_pulse_true_level = False, True

    if hasattr(lowfreq_sensor, 'frequency'):
        lowfreq_sensor.frequency = pps.lowfreq_sensor_skips
    elif hasattr(lowfreq_sensor, 'skipTicks'):
        lowfreq_sensor.skipTicks = pps.lowfreq_sensor_skips
    elif hasattr(lowfreq_sensor, 'tick_skip'):
        lowfreq_sensor.tick_skip = pps.lowfreq_sensor_skips

    # add an AND controller
    bpy.ops.logic.controller_add(type='PYTHON', name='LowFreqGameScript', object=camname)
    bpy.ops.logic.controller_add(type='LOGIC_AND', name='LOWFREQ_AND', object=camname)
    lowfreq_and = circling_cam.game.controllers['LOWFREQ_AND']

    # add a scene actuator to the camera
    bpy.ops.logic.actuator_add(type='SCENE', name='TextOverlay', object=camname)
    to = circling_cam.game.actuators['TextOverlay']
    to.mode = 'ADDFRONT'
    to.scene = bpy.data.scenes[pps.name_of_statusbar_object]

    # link the logic bricks together
    to.link(lowfreq_and)
    lowfreq_and.link(lowfreq_sensor)


@postfn_gamemaster_reset_decorator
@prefn_gamemaster_select_decorator
def add_menu_scene(scene_name=pps.name_of_popup_object):

    append_item_from_rel_path(blenderfile=pps.popup_dot_blend,
                              itemname=pps.name_of_popup_object,
                              relpath=pps.rel_loc_of_popup_dot_blend,
                              locationinblend=pps.path_to_popup_in_dot_blend)

    # switch back to default scene after adding new one
    bpy.context.screen.scene=bpy.data.scenes['Scene']
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # add a scene actuator to the GameMaster so this can be called from main game script
    bpy.ops.logic.actuator_add(type='SCENE', name='POPUP', object='GameMaster')
    gm = bpy.data.objects['GameMaster']
    to = gm.game.actuators['POPUP']
    to.mode = 'ADDFRONT'
    to.scene = bpy.data.scenes[scene_name]

    # add a removing scene actuator to the camera
    bpy.ops.logic.actuator_add(type='SCENE', name='POPUP_REMOVE', object='GameMaster')
    gm = bpy.data.objects['GameMaster']
    to = gm.game.actuators['POPUP_REMOVE']
    to.mode = 'REMOVE'
    to.scene = bpy.data.scenes[scene_name]

    # link to the high-freq Python controller
    hifreq_python_controller = bpy.context.scene.objects['GameMaster'].game.controllers['GameScript']
    bpy.context.scene.objects['GameMaster'].game.actuators['POPUP'].link(hifreq_python_controller)
    bpy.context.scene.objects['GameMaster'].game.actuators['POPUP_REMOVE'].link(hifreq_python_controller)


#####################################################################
##                      ADD EXTERNAL RIGS
#####################################################################

def find_next_scene_name(goalname):
    # find the lowest available name, in case of duplicates
    i = 0
    for name in sorted([scene.name for scene in bpy.data.scenes]):
        if name == goalname+str(i).zfill(3) or (i == 0 and name == goalname):
             i += 1
    return goalname +str('.') + str(i).zfill(3) if i > 0 else goalname


def add_external_lips_rig(deloldscene=False):
    """Import the lip scene as defined in the properties file, and copy all of its objects into the current scene.
    Update the shared dictionary lip_control_points with the empties that control it, the armature name list too."""
    print("Now beginning the lip importing process")

    orig_scene = bpy.context.scene.name
    lipscene_name = find_next_scene_name(pps.name_of_lip_object)

    # append the tongue scene to the blend
    append_item_from_rel_path(blenderfile=pps.lip_dot_blend,
                              itemname=pps.name_of_lip_object,
                              relpath=pps.rel_loc_of_lip_dot_blend,
                              locationinblend=pps.path_to_lip_in_dot_blend,)

    # sanity check that that scene name does exist after it is imported
    lipscene = bpy.data.scenes.get(lipscene_name, 0)
    if not lipscene_name:
        print("The lip scene does not have the expected name. I expect {}".format(lipscene_name))
        #raise NameError
    else:
        print("The lip scene were imported and is now the scene named: {}".format(lipscene_name))

    # put in position of the appropriate coil objects
    resize_scene_to_three_points(lipscene,
                                 pps.UL_empty_name, pps.SL_empty_name_right, pps.LL_empty_name,
                                "UL", "SL", "LL",)

    # move the contents into first 'Scene'
    trans_objs = grab_scene_contents(targetlayers=[1, 2, 3], targetscenename=orig_scene, originscenename=lipscene_name, deleteoriginscene=deloldscene)
    return trans_objs


def add_external_rigged_tongue(deloldscene=False):
    """Add a rigged tongue mesh and armature from an external file into the main scene.
    Return the name of the mesh, and the name of the armature
    Update the shared dictionary with the empties that control it."""
    orig_scene = bpy.context.scene.name

    scene_name = find_next_scene_name(pps.name_of_tongue_object)

    # append the tongue scene to the blend
    append_item_from_rel_path(blenderfile=pps.tongue_dot_blend,
                              itemname=pps.name_of_tongue_object,
                              relpath=pps.rel_loc_of_tongue_dot_blend,
                              locationinblend=pps.path_to_tongue_in_dot_blend,)


    # sanity check that that scene name does exist
    tonguescene = bpy.data.scenes.get(scene_name, 0)
    print('tonguescene is called', tonguescene)
    if not tonguescene:
        print("The lip scene does not have the expected name. I expect {}".format(scene_name))
#        raise NameError
    else:
        print('the tongue scene is called', scene_name)

    # put in position of the appropriate coil objects
    resize_scene_to_three_points(tonguescene,
                                 pps.TT_empty_name, pps.TM_empty_name, pps.TB_empty_name,
                                 "TT", "TM", "TB", )

    # move the contents into first 'Scene'
    print('target scene name becomes', orig_scene, 'originscenename', scene_name)
    trans_objs = grab_scene_contents(targetscenename=orig_scene, originscenename=scene_name, deleteoriginscene=deloldscene)
    return trans_objs


########################################################################
##                GEOMETRIC METHODS FOR IMPORTING AND RESIZING
########################################################################

def three_point_two_scaling_matrix(aloc1, aloc2, aloc3, bloc1, bloc2, bloc3):

    """Return the transformation to put points from a in b coordinate system, scaled uniformly such that
    the distance from a1 to a2 is that of b1 to b2."""

    import scripts.ema_io.ema_gameserver.biteplate_headcorr as bh
    import importlib as imp
    imp.reload(bh)
    asset_cs = bh.ScalingPlane(aloc1, aloc2, aloc3)
    target_cs = bh.ScalingPlane(bloc1, bloc2, bloc3)
    print('Initial locations are:\n{} {}\n{} {}\n {} {}\n'.format(aloc1, bloc1, aloc2, bloc2, aloc3, bloc3))

    # calculate a scaling factor
    target_dist = (bloc2 - bloc1).length
    current_dist = (aloc2 - aloc1).length
    sf = target_dist/current_dist
    #print('scaling by', sf)
    scaling_factor = mathutils.Matrix([[sf, 0, 0, 1],
                                       [0, sf, 0, 1],
                                        [0, 0, sf, 1],
                                        [0, 0, 0, 1],
                                        ])

    # the transformation matrix used to align points by these three points, and size it such that the first two are the same distance from each other.
    tranf = target_cs.give_local_to_global_mat() * scaling_factor * asset_cs.give_global_to_local_mat()
    return tranf


def resize_scene_to_three_points(sceneobj, objname1, objname2, objname3,  placename1, placename2, placename3):
    """Perform a transformation so that the planes between the 3 objects align with the 3 cord placements.
    Also resize the scene so that the distance between objname1 and objname2 is the same as between placename1 and placename2"""


    aloc1, aloc2, aloc3 = sceneobj.objects[objname1].location, sceneobj.objects[objname2].location, sceneobj.objects[objname3].location,
    bloc1, bloc2, bloc3 = [ci.find_sensor_location_by_name(i) for i in [placename1, placename2, placename3]]

    tm = three_point_two_scaling_matrix(aloc1, aloc2, aloc3, bloc1, bloc2, bloc3)

    for obj in sceneobj.objects:
        obj.matrix_world = tm * obj.matrix_world



    #
    # # check the new coordinates
    # cloc1, cloc2, cloc3 = tranf * aloc1 , tranf * aloc2, tranf*aloc3
    # print('Transformed locations are:\n{} {}\n{} {}\n {} {}\n'.format(cloc1, bloc1, cloc2, bloc2, cloc3, bloc3))
    # print('old distance', target_dist)
    # print('new distance', (cloc1-cloc2).length)
    #
    #
    # return tranf




    # put in position of the appropriate coil objects
# def resize_scene_to_data(sceneobj, objname1, objname2,  placename1, placename2, *optionals):
#     raise NotImplementedError
#     """Perform a transformation so that the scene's two objects are in the positions of coils ind1 and ind2.
#     As three locations would really be needed to anchor the items, presume a constant z-axis in the initial models."""
#     print('%%%%%%%%%%%\n\n The objects in this scene are', [x for x in sceneobj.objects])
#     print('looking for obejcts named', objname1, objname2)
#     #objname3, placename3 = optionals
#
#     # these are missing
#     print('placenames are',placename1, placename2)
#     bloc1, bloc2 = [ci.find_sensor_location_by_name(i) for i in [placename1, placename2]]
#     #bloc3 = ci.find_sensor_location_by_name(placename3)
#
#     # these are found
#     aloc1, aloc2= sceneobj.objects[objname1].location, sceneobj.objects[objname2].location, #\
#                     #sceneobj.objects[objname3].location,
#     print('\n\n\n********', aloc1, aloc2, bloc1, bloc2)
#
#
#     import scripts.ema_shared.coord_transforms as ct
#     asset_cs = ct.ObjectResizingCS(aloc1, aloc2, )
#     target_cs = ct.ObjectResizingCS(bloc1, bloc2,)
#     target_dist = (bloc2 - bloc1).length
#     current_dist = (aloc2 - aloc1).length
#     sf = target_dist/current_dist
#     print('scaling by', sf)
#
#     scaling_factor = mathutils.Matrix([[sf, 0, 0, 1],
#                                        [0, sf, 0, 1],
#                                         [0, 0, sf, 1],
#                                         [0, 0, 0, 1],
#                                         ])
#
#     # make the transformation matrix that should be applied to all objects in the scene
#     trans_mat = asset_cs.give_global_to_local_mat()* scaling_factor * target_cs.give_local_to_global_mat()
#     print('CHECKIGN DISTANCE',
#           asset_cs.project_to_lcs(aloc1)- asset_cs.project_to_lcs(aloc2),
#           target_cs.project_to_lcs(bloc1) - target_cs.project_to_lcs(bloc2)) # these should be the same
#
#     for obj in sceneobj.objects:
#         obj.matrix_world = trans_mat * obj.matrix_world
#         #obj.location = target_cs.project_to_global(  asset_cs.project_to_lcs(obj.location) )
#
#     # sanity check that the objects now have the same location
#     # these are found
#     a2loc1, a2loc2 = sceneobj.objects[objname1].location, \
#                    sceneobj.objects[objname2].location
#
#     b2loc1, b2loc2 = [ci.find_sensor_location_by_name(i) for i in [placename1, placename2]]
#     print('changed locations are', a2loc1, a2loc2, b2loc1, b2loc2)
#
#
#     return #trans_mat







# BELOW IS A DIFFERENT METHOD OF MOVING THINGS TO ANOTHER BLEND FILE, USING A LIBRARIES APPROACH
# def old_load_tongue_mesh(blendpath = "C:\\Users\\Kristy\\Documents\\GitHub\\repos\\ematoblender\\pink_tongue_mesh.blend",
#                      meshname = 'template_closed'):
#     """Copy the scene from the given Blender file, put the named object into the initial scene."""
#     '''Inspired by: http://www.blender.org/api/blender_python_api_2_59_0/bpy.types.BlendDataLibraries.html'''
#     filepath = blendpath
#
#     # load all items from the new file
#     with bpy.data.libraries.load(filepath) as (data_from, data_to):
#         print("data from the file being imported:", data_from.objects)
#
#     # append everything into the current blend file
#     with bpy.data.libraries.load(filepath) as (data_from, data_to):
#         print("This step may take several seconds to import the scene")
#         for attr in dir(data_to):
#             setattr(data_to, attr, getattr(data_from, attr))
#
#
#     # select the template we want in the first scene
#     bpy.ops.object.select_all(action='DESELECT')
#
#     # switch to the other scene
#     bpy.context.screen.scene=bpy.data.scenes['Scene.001']
#     bpy.data.scenes['Scene.001'].objects[meshname].select = True
#
#     #bpy.context.scene.objects.active = bpy.data.objects[meshname]
#     print(bpy.context.selected_objects)
#
#     # import into the scene
#     bpy.ops.object.make_links_scene(scene='Scene')
#     # switch the context back
#     bpy.context.screen.scene=bpy.data.scenes['Scene']
#
#     # delete the other scene?
#     bpy.data.scenes.remove(bpy.data.scenes['Scene.001'])
