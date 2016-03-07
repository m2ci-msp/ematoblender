__author__ = 'Kristy'

'''Camera philosophy: Keypresses control camera regardless to its empty. Head-correction moves the empty.'''

import mathutils
import math
import bge
from . import bge_splines_lines as sl
from . import bge_menus_overlays as mo
from .. import blender_shared_objects as bsh
from ematoblender.scripts.ema_shared import properties as pps

neutral_position = None # todo: get the basic position
speed_factor=50


def bge_circular_camera_control(keys, target_name='CameraFocus', camera_name='CircularCamera'):
    """ Control a camera that points at and is parented to an empty by manipulating the empty.
    Function hard codes that movement is:
    - Move the camera in a circle with L/R,
    - move in and out with U/D.
    - Pan left/right with comma and period."""

    # unused: rotate_rate = 4
    # unused: pan_rate = 4

    scn = bge.logic.getCurrentScene()
    ce = scn.objects.get(target_name, 0)  # eg 'CameraFocus'
    cam = scn.objects.get(camera_name, 0)

    # uncomment for debugging output
    print('up: {}, down:{}, left:{}, right:{}'.format(keys['upkey'], keys['downkey'], keys['leftkey'], keys['rightkey']))

    # up/down control closeness
    if keys['upkey']:
        print('up was pressed')
        #ce.worldPosition.y -= 0.1
        cam.localPosition.z -= 0.1 * speed_factor

    if keys['downkey']:
        #ce.worldPosition.y += 0.1
        cam.localPosition.z += 0.1 * speed_factor

    # left/right control rotation
    if keys['leftkey']:
        #ce.applyRotation(mathutils.Vector((0, 0, -0.01 * rotate_rate)), True)
        cam.localPosition.x += 0.1 * speed_factor

    if keys['rightkey']:
        #ce.applyRotation(mathutils.Vector((0, 0, 0.01 * rotate_rate)), True)
        cam.localPosition.x -= 0.1 * speed_factor

    # comma/period zoom in/out
    if keys['commakey']:
        #ce.localPosition.x -= 1 * pan_rate ORIGINAL
        cam.worldPosition.x *= 1 + 0.1
        cam.worldPosition.y *= 1 + 0.1
        #cam.worldPosition.y +=-0.1 * speed_factor
        #cam.localPosition.y -=0.1 * speed_factor # move outwards
        #cam.applyRotation(mathutils.Vector((0,math.radians(1* speed_factor),0)), True)
    if keys['periodkey']:
        cam.worldPosition.x *= 1 - 0.1
        cam.worldPosition.y *= 1 - 0.1
        #ce.localPosition.x += 1 * pan_rate
        #cam.localPosition.y +=0.1 * speed_factor # move inwards
        #cam.applyRotation(mathutils.Vector((0,-math.radians(1* speed_factor),0)), True)

    if keys['ekey']:
        print('i am here')
        bge_apply_head_movement()

    if keys['okey']:
        bge_point_cam_at_origin(camname="CircularCamera")

    if keys['tkey']: # track the mouse
        bge.render.showMouse(True)
        bge_rotate_with_mouse()

    mo.bge_update_avatar_rotation(cam.worldOrientation)
    #print(ce, type(ce))


def bge_apply_head_movement(cameraempty='CameraFocus'):
    """Move the camera position relative to the parent empty based on the head-correction matrix"""
    matlist, *cam_pos = bsh.head_inversion
    print('got matlist', matlist)
    if matlist is not None:
        mat = mathutils.Matrix(matlist)
    else:
        print('no matrix made yet')
        return
    global neutral_position
    if neutral_position is not None:

        scn = bge.logic.getCurrentScene()
        cam = scn.objects.get(cameraempty, 0)
        print('The camera is here', cam_pos)
        cam.worldPosition = mathutils.Vector(*cam_pos)  # todo: working on this
        #print('first position', cam.worldTransform)
        #print('applying mat', mat)
        #cam.localTransform = mathutils.Matrix() * (mat-neutral_position)
        #print('world transform',cam.worldTransform)
        #print(cam.worldPosition)

    else:
        neutral_position = mat


def bge_point_cam_at_origin(camname="CircularCamera"):
    """On this camera press, point the camera at worldPosition 0,0,0."""
    scn = bge.logic.getCurrentScene()
    cam = scn.objects.get(camname, 0)
    if cam:
        origin = mathutils.Vector((0, 0, 0))
        curr_pos = cam.worldPosition

        cam.alignAxisToVect(curr_pos-origin, 2, 1.0)  # z = 2 # works but rotates whole camera weirdly

        # this and my method compound the rotation, using built-ins
        #dist,world, local = cam.getVectTo(mathutils.Vector((0,0,0)))

        #print('world position', curr_pos)
        #vector_to = sl.get_rotation_towards_vector(origin-curr_pos)
        #print('vector to', vector_to)
        #facing_rot =(curr_pos-origin).to_track_quat('X', 'Z').to_euler()
        #cam.applyRotation(facing_rot, True)


def bge_rotate_with_mouse(camname='CircularCamera'):
    """Rotate with the mouse position, if holding t (track)"""
    from .bge_standard_gamefns import get_scene_info
    scn, objs, cont, own, acts = get_scene_info()
    print([x for x in own.sensors])
    mouse = own.sensors["MouseSensor"]
    print(mouse.position)
    x_pos = bge.render.getWindowWidth()/2 - mouse.position[0]
    y_pos = bge.render.getWindowHeight()/2 - mouse.position[1]

    print(x_pos, y_pos)

    cam = objs.get(camname, 0)
    speed = 0.005
    if cam:
        cam.applyRotation(mathutils.Euler((math.radians(y_pos * speed), math.radians(x_pos* speed), 0 ), 'XYZ'), True)
        # if resetting mouse position:
        # bge.render.setMousePosition(int(bge.render.getWindowWidth() / 2),
        # int(bge.render.getWindowHeight() / 2))
    pass


#######################################################
##           GIVE VIEWPORTS TO EACH LISTED CAMERA
#######################################################

def get_viewport_coords(index, totalvps, space_coords, vertical):

    l, b, r, t = space_coords
    # the space that can be divided
    ww = r-l
    wh = t-b

    # choose the sizes of the viewports
    if vertical:
        width = 1/totalvps * ww
        height = wh

        # round because pixel coordinates
        left = round(l + index*width)
        right = round(left + width)
        bottom = round(b)
        top = round(bottom + height)
    else:
        width = ww
        height = 1/totalvps * wh

        # round because pixel coordinates
        left = round(l)
        right = round(left + width)
        bottom = round(b + index*height)
        top = round(bottom + height)

    return left, bottom, right, top


def use_viewports(vertical=True):
    """Share the cameras listed in pps equally between viewports.
    Choose vertical or horizontal split.
    """

    scn = bge.logic.getCurrentScene()
    cams = [scn.objects.get(cam) for cam in pps.display_cameras]

    if len(cams) == 1:  # if one camera is listed in Properties, force this perspective
        scn.active_camera = cams[0]

    elif len(cams) > 1:  # only use viewports if more than one camera listed
        print('the cams are', cams)
        scn.active_camera = cams[0]

        # get the size of the game screen
        wh = bge.render.getWindowHeight()
        ww = bge.render.getWindowWidth()
        print('render height is', wh, ww)

        for i, cam in enumerate(cams):
            cam.useViewport = True
            coords = get_viewport_coords(i, len(cams), (0, 0, ww, wh,), vertical)
            print(coords)
            cam.setViewport(*coords)
