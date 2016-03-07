__author__ = 'Kristy'
import mathutils

"""
This module describes how to place coils given an incoming dataframe in bpy.
"""

import bpy
#from .bpy_workspace import postfn_gamemaster_reset_decorator
from ..ema_bpy import bpy_link_assets_coils as lac
from .. import coil_info as ci
from .. import blender_networking as bn
from .. import blender_shared_objects as bsh
from .. import coord_transforms as ct

from ematoblender.scripts.ema_shared import properties as pps


def show_all_coils_in_position(df, active=True, biteplate=True, reference=True):
    """
    Access the next frame from the server, put the cubes in that position.
    Hide all coils at 0,0,0, these are likely biteplate sensors not in this tsv.
    If show all, show all coils even if they are not listed in the JSON. Else just those with JSON entry.
    """

    if type(df) is None:
        raise TypeError

    emacoils = df.give_coils()  # dataframe in a list, each item is a coil
    print('ABOUT TO VISUALISE THIS  RECEIVED COORDINATE INFO:', emacoils, '\n')

    # import time, importlib
    # importlib.reload(ct)
    # importlib.reload(pps)

    ptm = ct.PointsTransformationMatrix(pps.global_coordinate_transform)
    print('ptm', ptm)


    # collect the list of cubes that, according to the JSON file, represent sensors.
    if len(bsh.ema_active_meshes) == 0\
            and len(bsh.ema_biteplate_meshes) == 0\
            and len(bsh.ema_reference_meshes) == 0:
        act, bp, ref = ci.get_sensor_roles()

    # object must be consistently assigned to the right sensor number

    coils_to_show = [x for x in bsh.ema_active_meshes if active] +\
                    [x for x in bsh.ema_biteplate_meshes if biteplate] +\
                    [x for x in bsh.ema_reference_meshes if reference]
    print('COILSTOSHOW', coils_to_show)

    for emind, cubeobj, name in coils_to_show:       #bsh.ema_driven_meshes: # TODO: This iterator doesn't work! But it should be
        #print("Setting a location of", cubeobj.abs_loc)
        try:
            ema_coil = emacoils[emind]
            new_loc = ema_coil.abs_loc if ema_coil.bp_corr_loc is None else ema_coil.bp_corr_loc
            cubeobj.location = mathutils.Vector(new_loc) + mathutils.Vector(ci.find_transform_by_index(emind))
            # TODO: Update rotation
        except IndexError:
            print('This coil is not available', emind, name)
            continue

        s = pps.cube_scale
        cubeobj.scale = (s, s, s)  # if needed to make larger so visible on video
        if cubeobj.location == mathutils.Vector((0.0, 0.0, 0.0)) and name != 'UI':  # hide if at 0,0,0
            pass #cubeobj.hide, cubeobj.hide_render = True, True
        else:
            cubeobj.hide, cubeobj.hide_render = False, False
            cubeobj.show_name = True
            #TODO: Transform the rotation values too

            # add any global transform defined in the properties file
            cubeobj.location = ptm * cubeobj.location


def apply_properties_transform(location):
    ptm = ct.PointsTransformationMatrix(pps.global_coordinate_transform)
    return tuple(ptm * mathutils.Vector(location))


def apply_properties_object_transform(obj):
    ptm = ct.PointsTransformationMatrix(pps.global_coordinate_transform)
    obj.matrix_world = ptm * obj.matrix_world


########## inferred location fns #######
def show_inferred_coils_in_position():
    """Take the tupes of inferred meshes.
    Execute their rules and arguments.
    Rulestrings should capture the appropriate fn version for bpy/bge context.
    """
    for i, cob, name, rulestring, *ruleargs in bsh.ema_inferred_meshes:
        execstring = rulestring+'(cob,"' + '","'.join(*ruleargs) + '")'
        print('executing: ', execstring)
        exec(execstring)


def get_obj_from_placename(name):
    """Get the bge object from the placename"""
    scene = bpy.context.scene
    literal_obj = scene.objects.get(name, False)
    if literal_obj:
        return literal_obj

    # no object with that name, must look in sensor_index file
    import scripts.ema_blender.coil_info as ci
    ind = ci.find_sensor_index(name)

    # get the location of the appropriately-named cube

    cubeobj = scene.objects.get(bsh.ema_mesh_name_rule(ind), False)

    if cubeobj:
        return cubeobj
    else:
        return None


def take_midpoint(obj, *goalobjs):
    """Set obj's location to the midpoint of cubes with *names."""
    goalobjs = [get_obj_from_placename(g) if type(g) is str else g for g in goalobjs]
    obj.location.x = sum([g.location.x for g in goalobjs])/len(goalobjs)
    obj.location.y = sum([g.location.y for g in goalobjs])/len(goalobjs)
    obj.location.z = sum([g.location.z for g in goalobjs])/len(goalobjs)


def mirror_axis(obj, refl_obj, axisnames):
    """Set obj's location to that of cube with refl_name, mirrored in axisname."""
    refl_obj = get_obj_from_placename(refl_obj) if type(refl_obj) is str else refl_obj
    # TODO: Does not yet reflect the rotation value
    obj.location = refl_obj.location
    if 'X' in axisnames.upper():
        obj.location.x = - refl_obj.location.x
    if 'Y' in axisnames.upper():
        obj.location.y = - refl_obj.location.y
    if 'Z' in axisnames.upper():
        obj.location.z = - refl_obj.location.z


def only_positive_axis(obj, orig_obj, axisnames):
    """Set object's location value in that dimension to modulus."""
    orig_obj = get_obj_from_placename(orig_obj) if type(orig_obj) is str else orig_obj
    obj.location = orig_obj.location
    # TODO: Does not yet reflect/change the rotation value
    if 'X' in axisnames.upper():
        obj.location.x = abs(orig_obj.location.x)
    if 'Y' in axisnames.upper():
        obj.location.y = abs(orig_obj.location.y)
    if 'Z' in axisnames.upper():
        obj.location.z = abs(orig_obj.location.z)

if __name__ == "__main__":
    print('testing!')
    print(bn.get_live_setup_data())