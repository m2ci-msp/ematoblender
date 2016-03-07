__author__ = 'Kristy'

'''Approximate spline between points in Blender Game Engine'''
# note: you can also draw on images in Blender with
#bpy.data.images['Image Name'].pixels[0:4] = (Red, Green, Blue, Alpha) #Here "Red, Green, Blue, Alfa" are floating values.

import bge
import math
import mathutils
from mathutils import Vector
from ...ema_shared.general_maths import *


def draw_line_through_points(*points, color=(1, 0, 0)):
    """Give a list of points either as vectors or tuples etc.
    Draw a line between them."""
    if len(points) < 2:
        print('too few points to draw a line')
        return

    for i, p in enumerate(points[:-1]):
        q = points[i+1]
        bge.render.drawLine(Vector(p), Vector(q), color)


def draw_lines_through_names_locs_inds(*names, color=(1, 0, 0)):
    """Draw lines through the names or locations. If one is missing, don't draw its lines."""
    import scripts.ema_blender.ema_bge.bge_move_objects as mo
    import scripts.ema_blender.coil_info as ci
    import scripts.ema_blender.ema_bge.bge_standard_gamefns as sgf

    def get_coords(name):
        if type(name) == str:
            return mo.bge_get_location_from_placename(name)
        elif type(name) == mathutils.Vector:
            return name
        elif type(name) == int:
            scn, objs, *_ = sgf.get_scene_info()
            ob = objs.get('CoilCube{}'.format(str(name).zfill(2)), False)
            if ob:
                return ob.worldPosition
            else:
                return None
        else:
            print('wrong type of info given for', name)
            return None

    line_start = get_coords(names[0])
    for i in range(len(names)-1):
        line_end = get_coords(names[i+1])
        if line_start is not None and line_end is not None:
            bge.render.drawLine(line_start, line_end, color)
        line_start = line_end


def draw_spline_between_names(*names):
    locs = [ci.find_sensor_location_by_name(n) for n in names]
    if len(locs)>=3:
        splinecoords = get_intermediate_coords(*locs[:3])
        draw_line_through_points(*splinecoords, color=(1,1,1))
    else:
        draw_line_through_points(*locs, color=(1,1,1))





# take a list of coordinates (in order) and create a natural cubic spline between them
# input: list of x,y,z coords * (n+1) control points (eg 3 control points generally)
# output: n equations (2 equations), with 4n polynomial coefficients (4 coefficients for each eqn), as list of length n [a, b, c, d]


# take two points and a polynomial equation between them. give x points between these two points.
# input: two points, polynomial coefficients, x points desired (includes the two endpoints)
# returns: list of coordinates: start and end as given, plus x-2 points between them on the line


# bge: take coordinates and an armature, place bones between these points

