__author__ = 'Kristy'
import mathutils

from .bge_menus_overlays import bge_update_overlay_status_decorator
from ..blender_networking import send_to_gameserver, recv_from_gameserver
from ..blender_shared_objects import ema_active_meshes
# from ..coil_info import find_transform_by_index
from .. import  blender_shared_objects as bsh
from ..coord_transforms import PointsTransformationMatrix
from .. import coord_transforms as ct
from ...ema_shared import properties as pps


def bge_update_from_df(scene_objs, df, showall=True):
    """Using a list of the objects in the scene and the DataFrame, apply this to the relevant coils."""

    # sanity-checking the objects that will be moved, can be deleted
    #print("these are the coils", scene_objs)

    emacoils = df.give_coils()

    # either all of the objects that fit the naming rule, else tuples listed in bsh.ema_active_meshes
    allmeshes = [(i, scene_objs['CoilCube{}'.format(str(i).zfill(2))], 'place') for i in range(len(emacoils))]\
        if showall else ema_active_meshes

    for ci, co, place in allmeshes:  # index, object, place
        cn = co.name
        ema_coil = emacoils[ci]
        cubeobj = scene_objs[cn]

        #print("\nChanging this existing object:", scene_objs[cn]) # Chosen by name (prefix+num)
        new_location = getattr(ema_coil, 'bp_corr_loc', getattr(ema_coil, 'abs_loc', None))

        #print('transform', mathutils.Vector(ci.find_transform_by_index(ci)))
        cubeobj.worldPosition = mathutils.Vector(new_location)#\
#                       + mathutils.Vector(find_transform_by_index(ci))

        # TODO: Currently using uncorrected rotation values for the moment
        cubeobj.worldOrientation = mathutils.Vector(ema_coil.abs_rot)

        # add any global transform defined in the properties file
        predefined_transform_all_coords(cubeobj)


def predefined_transform_all_coords(gameobj):
    """Collects a predefined transformation matrix from properties, applies this to an object's position.
    """
    ptm = ct.PointsTransformationMatrix(pps.global_coordinate_transform)
    gameobj.worldTransform = ptm * gameobj.worldTransform


def bge_get_location_from_placename(name):
    """Use the coil's place string to get its coordinates as displayed onscreen."""
    # get the index of the coil
    import scripts.ema_blender.coil_info as ci
    ind = ci.find_sensor_index(name)

    # get the location of the appropriately-named cube
    import scripts.ema_blender.ema_bge.bge_standard_gamefns as sgf
    scene, objs, *_ = sgf.get_scene_info()
    cubeobj = objs.get('CoilCube{}'.format(str(ind).zfill(2)), False)

    if cubeobj:
        return cubeobj.worldPosition
    else:
        return None


def get_obj_from_placename(name):
    """Get the bge object from the placename"""
    # get the location of the appropriately-named cube
    import scripts.ema_blender.ema_bge.bge_standard_gamefns as sgf
    scene, objs, *_ = sgf.get_scene_info()
    literal_obj = objs.get(name, False)
    # scene has an object called name
    if literal_obj:
        return literal_obj

    import scripts.ema_blender.coil_info as ci
    ind = ci.find_sensor_index(name)

    cubeobj = objs.get(bsh.ema_mesh_name_rule(ind), False)
    if cubeobj:
        return cubeobj
    else:
        return None


def take_midpoint(obj, *goalobjs):
    """Set obj's location to the midpoint of cubes with *names."""
    goalobjs = [get_obj_from_placename(g) if type(g) is str else g for g in goalobjs]
    obj.worldPosition.x = sum([g.worldPosition.x for g in goalobjs])/len(goalobjs)
    obj.worldPosition.y = sum([g.worldPosition.y for g in goalobjs])/len(goalobjs)
    obj.worldPosition.z = sum([g.worldPosition.z for g in goalobjs])/len(goalobjs)


def mirror_axis(obj, refl_obj, axisnames):
    """Set obj's location to that of cube with refl_name, mirrored in axisname."""
    refl_obj = get_obj_from_placename(refl_obj) if type(refl_obj) is str else refl_obj
    # TODO: Does not yet reflect the rotation value
    obj.worldPosition = refl_obj.worldPosition
    if 'X' in axisnames.upper():
        obj.worldPosition.x = - refl_obj.worldPosition.x
    if 'Y' in axisnames.upper():
        obj.worldPosition.y = - refl_obj.worldPosition.y
    if 'Z' in axisnames.upper():
        obj.worldPosition.z = - refl_obj.worldPosition.z


def only_positive_axis(obj, orig_obj, axisnames):
    """Set object's location value in that dimension to modulus."""
    orig_obj = get_obj_from_placename(orig_obj) if type(orig_obj) is str else orig_obj
    obj.worldPosition = orig_obj.worldPosition
    #TODO: Does not yet reflect/change the rotation value
    if 'X' in axisnames.upper():
        obj.worldPosition.x = abs(orig_obj.worldPosition.x)
    if 'Y' in axisnames.upper():
        obj.worldPosition.y = abs(orig_obj.worldPosition.y)
    if 'Z' in axisnames.upper():
        obj.worldPosition.z = abs(orig_obj.worldPosition.z)


def bge_show_inferred_coils_in_position():
    """Take the tupes of inferred meshes.
    Execute their rules and arguments.
    Rulestrings should capture the appropriate fn version for bpy/bge context.
    """
    for i, cob, name, rulestring, *ruleargs in bsh.ema_inferred_meshes:
        import scripts.ema_blender.ema_bge.bge_standard_gamefns as sgf
        scene, objs, *_ = sgf.get_scene_info()
        try:
            gob = objs.get(name, False)  # get the game object equivalent
        except KeyError as e:
            print('Name collection failing mysteriously', e)
            gob = False
        except UnicodeDecodeError as e:
            print('Unicode Error on some object:', name)
            gob = False
        if gob:
            execstring = rulestring+'(gob,"' + '","'.join(*ruleargs) + '")'
            print('executing: ', execstring)
            exec(execstring)
            predefined_transform_all_coords(gob)
        else:
            print('Game object eqivalent not found for', cob)
