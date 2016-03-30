__author__ = 'Kristy'
import bpy
import mathutils
import math
from .bpy_workspace import postfn_gamemaster_reset_decorator
from .. import blender_shared_objects as bsh


@postfn_gamemaster_reset_decorator
def delete_standard_camera():
    """Delete any camera named 'Camera'."""
    # get the initial camer
    camobjs = [x for x in bpy.data.objects if x.name == 'Camera' or x.name.startswith('Camera.')]
    for camobj in camobjs:
        #bpy.context.scene.objects.unlink(camobj)
        camobj.select = True
        bpy.ops.object.delete()


def add_parented_camera(empty_loc, cam_loc, empty_name, cam_name):
    """ Add an empty, add a camera, parent the empty to the camera, make the camera look at the empty.
    If empty_name is already taken, attach to this empty regardless of its position."""

    empty_loc, cam_loc = mathutils.Vector(empty_loc), mathutils.Vector(cam_loc)

    # make empty object
    eo = bpy.data.objects.get(empty_name, False)
    if not eo:
        eo = bpy.data.objects.new(empty_name, None)
        eo.location = empty_loc
        bpy.context.scene.objects.link(eo)

    # make camera data and object
    c = bpy.data.cameras.new(cam_name)
    c.clip_end = 10000  # camera can see 10m ahead
    co = bpy.data.objects.new(cam_name, c)
    co.location = cam_loc
    co.rotation_mode = "QUATERNION"
    co.rotation_quaternion = look_at(co.location, eo.location)

    # parent these
    bpy.context.scene.objects.link(co)
    co.parent = eo

    # add to scene
    bpy.context.scene.update()
    return eo, co


@postfn_gamemaster_reset_decorator
def add_circling_camera():
    """Add a camera around the origin. Based on the name,
    you can move around on xy plane and zoom in-out in BGE."""

    delete_standard_camera()

    eo, co = add_parented_camera((0, 0, 0), (0, 100, 0), "CameraFocus", "CircularCamera")

    # for testing scale by 10 so camera at y=-10000 (don't do in practise as too far away!)
    eo.delta_scale = mathutils.Vector((eo.delta_scale.x, eo.delta_scale.y*10, eo.delta_scale.z))

    # save the object references
    bsh.circling_cam_empty = eo


def add_midsaggital_camera():
    """ Add a static camera that shows the mid-saggital view."""
    # TODO: Think about setting these locations in properties, 35 works well for VENI data.
    eo, co = add_parented_camera((0, 20, 0), (100, 0, 0), "MSFocus", "MSCamera")


def add_frontal_camera():
    """ Add a static camera that shows the frontal view. """
    eo, co = add_parented_camera((0,0,0), (0, -100, 0), "FFocus", "FCamera")


def look_at(loc, point):
    # return rotation_euler from first object to point
    # inspired by http://blender.stackexchange.com/questions/5210/pointing-the-camera-in-a-particular-direction-programmatically
    loc_camera = loc
    print('cam loaction is', loc_camera)

    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')
    print('rot quat', rot_quat)

    # assume we're using euler rotation
    return rot_quat



@postfn_gamemaster_reset_decorator
def move_camera_focus(newlocation):
    """Move the focus of the camera some location by moving its target empty.
    The newlocation is a Vector."""
    camemp = bsh.circling_cam_empty
    camemp = newlocation

