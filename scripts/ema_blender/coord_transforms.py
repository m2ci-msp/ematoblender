__author__ = 'Kristy'

import mathutils
import scripts.ema_io.ema_gameserver.data_manipulation as dm
from scripts.ema_shared import properties as pps
from scripts.ema_blender.ema_bpy.bpy_setup_cameras import delete_standard_camera
import scripts.ema_blender.blender_shared_objects as bsh
import scripts.ema_blender.coil_info as ci
import scripts.ema_shared.general_maths as bm

class ObjectResizingCS(dm.BitePlane):
    """Class that takes either three points or two points (plus the assumption that Z is up)
    and generates coordinate systems. These are used to resize objects between scenes."""

    def __init__(self, *coords):
        print("Initialising a coordinate system for object resizing.")
        import importlib as imp
        imp.reload(dm)
        self.n_inputs = len(coords)
        print('CS coord coords are ', coords)

        if self.n_inputs == 3:
            super().__init__(*coords)
        elif self.n_inputs == 2:
            super().__init__(coords[0], coords[1], mathutils.Vector((0,0,0)))

    def compute_local_cs(self):
        """Compute a system based on the coordinates given, assuming up is up if only two coords are given."""
        print('doing child compute_local_cs')
        if self.n_inputs == 3:
            super().compute_local_cs()
        else:

            #compute vectors based on the sensor locations
            right_to_left = self.right_coil - self.left_coil

            self.origin = (self.right_coil + self.left_coil) * 1/2
            print('child origin is', self.origin)

            # normalise the vectors
            right_to_left.normalize()
            self.x_axis = right_to_left

            # assume z-axis is fixed
            self.y_axis = mathutils.Vector.cross(self.x_axis, mathutils.Vector((0, 0, 1)))
            self.y_axis.normalize()
            # if parallel

            self.z_axis = mathutils.Vector.cross(self.y_axis, self.x_axis)
            self.z_axis.normalize()



def bpy_move_tongue_to_coils():
    print('@@@@@@@\n\n doing mogve tongue to coils')
    """Parent the empties on the tongue rig to the cube control objects"""
    import bpy
    # get the coil locations
    tt_loc, tm_loc, tb_loc = [ci.find_sensor_location_by_name(i) for i in ["TT", "TM", "TB"]]
    for i in range(pps.tongue_intervals):
            rigemp = bpy.data.objects.get(bsh.tongue_top_empty_name(i), 0)
            if rigemp:
                bsh.tongue_top_empties.append(rigemp)
    rigempties = bsh.tongue_top_empties
    rigcoords = bm.get_intermediate_coords(tt_loc, tm_loc, tb_loc, n=len(rigempties)+1)
    # assign the tip (armature location), each empty to the interpolated position
    arm = bpy.context.scene.get(pps.tongue_armature_name, 0)
    if arm:
        print('got your arm!')
        arm.location = rigcoords[0]
    for obj, coord in zip(rigempties, rigcoords[1:]):
        obj.location = coord


def bge_move_tongue_to_coils():
    import bge
    # get the coil locations
    tt_loc, tm_loc, tb_loc = [ci.find_sensor_location_by_name(i) for i in ["TT", "TM", "TB"]]

    rigempties = []

    scene = bge.logic.getCurrentScene()

    # until counting +=1 turns up no object, keep looking for empties
    i=1
    lastrig = scene.objects.get(bsh.tongue_top_empty_name(i), 0)
    while lastrig:
        rigempties.append(lastrig)
        i+=1
        lastrig = scene.objects.get(bsh.tongue_top_empty_name(i), 0)


    rigcoords = bm.get_intermediate_coords(tt_loc, tm_loc, tb_loc, n=len(rigempties)+1)

    # assign the tip (armature location), each empty to the interpolated position
    arm = scene.objects.get(pps.tongue_armature_name, 0)
    if arm:
        print('!!!!!!!! setting arm worldpos')
        arm.worldPosition = rigcoords[0]
        print(len(rigcoords), len(rigempties))
    for obj, coord in zip(rigempties, rigcoords[1:]):
        print('rigempty is', obj, 'coord is', coord)
        obj.worldPosition = coord
        #gobj = scene.objects.get(obj.name, 0)
       # gobj.worldPosition = coord
    arm.update()
    return


class PointsTransformationMatrix(mathutils.Matrix):
    """
    Class that defines a transformation matrix based on settings in properties.
    If these define a different axis ordering or flips, then it transforms all points.
    Else it is an identity matrix.

    __new__ used as __init__ does not work for subclasses of mathutils.
    Known issue, see http://blenderartists.org/forum/archive/index.php/t-282858.html
    """

    def __new__(self, attr_dict):
        """Initialise the matrix, taking a dictionary from the properties file.
        :param attr_dict: dictionary with keys axis_order => string, flip_xyz => tuple of bool,
        :return: mathutils.Matrix 4x4
        """
        print('Initialising with axis_dict', attr_dict)
        self = super().__new__(self)

        # flip axes
        flip_tuple = attr_dict.get('flip_xyz', False)
        if flip_tuple and len(flip_tuple) == 3:
            for i, val in enumerate(attr_dict['flip_xyz']):
                if val:
                    self[i][i] = - self[i][i]  # reflect along the ith axis

        # switch axis ordering
        switch_tuple = attr_dict.get('axis_order', False)
        if switch_tuple and len(switch_tuple) == 3:

            # TODO: Add conditions to check that all three axes are present
            initialvals = {'X': self[0][0:3], 'Y': self[1][0:3], 'Z': self[2][0:3]}
            for i, an in enumerate(switch_tuple):
                print('row %i becomes' % i, self[i][0:3])
                self[i][0:3] = initialvals[an.upper()]
        return self


