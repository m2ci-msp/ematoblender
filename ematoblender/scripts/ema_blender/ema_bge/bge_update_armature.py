__author__ = 'Kristy'
import bge
from .. import coil_info as ci
from . import bge_splines_lines as sl
from ...ema_shared import general_maths as bm

###############################################
##   NEW APPROACH - UPDATE ARMATURES WITH IK EMPTIES
###############################################
# do in bge


#old
def update_tongue_surface():
    scn = bge.logic.getCurrentScene()
    hes = bsh.tongue_top_empties if bsh.tongue_top_empties is not None \
        else [scn.objects.get(bsh.tongue_top_empty_name(i)) for i in range(pps.tongue_intervals)]

    ao = scn.objects.get(pps.tongue_armature_name, 0)
    if ao:
        tt, tm, tb = [ci.find_sensor_location_by_name(n) for n in ['TT', 'TM', 'TB']]

        coords = bm.get_intermediate_coords(tt, tm, tb, len(hes)+1)
        ao.location = coords[0]  # set the tongue tip location
        for he, coord in zip(hes, coords[1:]):
            he.location = coord

        ao.update()
    else:
        print("Tongue armature not found in scene. This is problematic.")

from . import bge_splines_lines as splines
from . import bge_standard_gamefns as gf
from .. import blender_shared_objects as bsh
from ...ema_shared import properties as pps


def update_these_bones(armature_name='Mid-Saggital'):
    """Update all of the bones in the armature named 'Armature' ."""
    scene = bge.logic.getCurrentScene()  # Get the whole bge scene
    objs = scene.objects  # Get the objects in the scene

    # Methods to select armature and bones
    ob = objs.get(armature_name)  # armature, as name is known
    ob.update()


def update_all_bones():
    """Update all of the armatures in the scene."""
    scene = bge.logic.getCurrentScene()
    for obj in scene.objects:
        if type(obj) == bge.types.BL_ArmatureObject:
            obj.update()


    # old
    # for armname in pps.updateable_armatures_names:
    #     armobj = scene.objects.get(armname, 0)
    #     if armobj:
    #         armobj.update()

def update_tongue_bones_from_spline():
    """Use if the tongue is made of unconnected bones and they should follow the path of a spline through empties."""

    # get the location of the empties the spline should follow
    scene, objs, *_ = gf.get_scene_info()
    tb_loc, tm_loc, tt_loc = bsh.tongue_control_empties['TB'].worldPosition, \
                             bsh.tongue_control_empties['TM'].worldPosition, \
                             bsh.tongue_control_empties['TB'].worldPosition


    bones = objs.get(pps.name_of_tongue_armature, False)
    if bones:
        print("Tongue armature found, will be updated to spline now.")
        #old b_sh.armature_names['tongue'] # this should be the object
        print('check type here!', type(bones))


    # get a spline the bone should follow
    interpolated_coords = bm.get_intermediate_coords(tb_loc, tm_loc, tt_loc)
    #apply_bones_to_coords(interpolated_coords, bones)
    # TODO: Test that using IK replaces this functionality


def apply_bones_to_coords(coordlist, skeleton):
    """ Coordlist is the result of the get_intermediate_coords fn, ie a list of Vectors
    Skeleton is the data object of the armature, as per the internet example.
    ik_empty is the empty that the very tip bone aims at.
    The skeleton should (to show up nicely) be composed on unconnected, uninheriting, deforming bones, each with an IK constraint of len=1.
    """
    if len(coordlist)-1 != len(skeleton.channels) or len(coordlist) < 2:
        print("Number of points and bones does not match")
    for (i, coord), chan in zip(enumerate(coordlist[:-1]), skeleton.channels):  # hopefully each bone in order from root to tip
        # set the rotation based on the gradient towards the next location on the curve
        nextloc = coordlist[i+1]
        vect_to = nextloc - coord  # this vector is the difference between the two coordinates
        chan.location = vect_to   # channel.location can be better defined as "position displacement of the bone relative to its parent expressed as a Vector, read-write."

    skeleton.update()


def main():
    print('updating the lip armature')
    update_these_bones(armature_name='LipArmature')


if __name__ == "__main__":
    main()
