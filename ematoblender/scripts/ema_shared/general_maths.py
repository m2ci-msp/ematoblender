__author__ = 'Kristy'
import math
import mathutils


def get_intermediate_coords(k1, k2, k3, n=10):
    """Return n vectors (3d) with coordinates that give the Bezier curve between two points.
    Testing in Blender with the handles as the midpoint show a smooth curve through the TM sensor coords.
    All bones should be unconnected, but with IK to the next bone to set the rotation."""
    print(mathutils.geometry.__dir__())
    print(k1, k2, k3, type(k1), type(k2), type(k3))
    result = mathutils.geometry.interpolate_bezier(k1, k2, k2, k3, n)
    print(result)
    return result


def get_rotation_towards_vector(vect_to):
    """Given a 3d vector, return the Euler XYZ rotation that points from the origin towards it."""
    if vect_to == (0.0, 0.0, 0.0):
        raise ValueError  # zero-length vector

    x, y, z = vect_to
    xy_hyp = math.sqrt(math.pow(x, 2) + math.pow(y, 2))
    z_rot = math.sin(y/xy_hyp)
    z_xy_hyp = math.sqrt(math.pow(x, 2) + math.pow(xy_hyp, 2))
    y_rot = math.tan(z/z_xy_hyp)

    return mathutils.Euler((0.0, y_rot, z_rot), 'XYZ')


def average_quaternions(quat_list):
    """inspired by Unity http://wiki.unity3d.com/index.php/Averaging_Quaternions_and_Vectors"""
    quat_list = [mathutils.Quaternion(q) for q in quat_list]
    exp_avg = mathutils.Vector()
    for q in quat_list:
        #print(q, 'is q')
        exp_avg += q.to_exponential_map()
    exp_avg /= len(quat_list)
    return mathutils.Quaternion(exp_avg)




if __name__ == "__main__":
    a=get_rotation_towards_vector(mathutils.Vector((0,0,4)))
    print(a)