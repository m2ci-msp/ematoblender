__author__ = 'Kristy'
"""Functions that edit the text-overlay scene, eg for status, webcam, menus."""

import bge
import mathutils
import math

from . import bge_standard_gamefns as sg
from ..blender_networking import send_to_gameserver, recv_from_gameserver
from .. import blender_shared_objects as bsh
from ...ema_shared import properties as pps

##########################################################################
##                   STATUS OVERLAY SCENE
##########################################################################


def bge_get_statusbar_scene():
    """Return the item of the scene with the statusbar in it."""
    all_scenes = bge.logic.getSceneList()
    i = [x.name for x in all_scenes].index(pps.name_of_statusbar_object)
    text_scene = all_scenes[i]
    return text_scene


def bge_display_status_text(newtext=None):
    """Take the last server response, eg the OK message, display on screen"""

    text_scene = bge_get_statusbar_scene()
    sb = text_scene.objects.get('StatusBar', 0)
    if newtext is not None and sb:
        try:
            sb.text = newtext  # change text in the status bar
        except SystemError:
            print('Could not set status as connection closing.')


def bge_update_avatar_rotation(angle,):
    """Look for the avatar by name in the statusbar scene. Rotate to the given angle."""
    text_scene = bge_get_statusbar_scene()
    av = text_scene.objects.get(pps.rotation_avatar, 0)
    if av:
        av.worldOrientation = angle.inverted() * mathutils.Euler((math.radians(180), math.radians(180), math.radians(0))).to_matrix()


def bge_update_overlay_status_decorator(func):
    """Decorator for server state change commands that checks the server status message afterwards."""
    def status_update_wrapper(*args, **kwargs):
        # update onscreen status bar, menus etc
        func(*args, **kwargs)
        send_to_gameserver(bsh.gs_soc_blocking, mode='STATUS')
        reply = recv_from_gameserver(bsh.gs_soc_blocking)
        bge_display_status_text(newtext=reply)
    return status_update_wrapper


def bge_update_webcam(planename='FacePlane'):
    """
    Run the setup on first execution, update the video in subsequent ticks.
    For persistence, the video source is stored in bge.logic.video.
    """

    if not hasattr(bge.logic, 'video'):  # Runs on second logic tick as waits on other imports
        text_scene = bge_get_statusbar_scene()
        fp = text_scene.objects.get(planename, 0)  # get the plane it it should be displayed on

        # get the reference pointer to the internal texture # TODO: Check that this is initialised correctly
        image_prefix = 'IM'; placeholdername = 'images/face_blank.png'
        # OLD: matID = bge.texture.materialID(fp, 'MAFaceMaterial') print('@@@@@@@@@@ Material ID', matID)

        bge.logic.video = bge.texture.Texture(fp, 0)  # 0 is matID #TODO: Update this to actually check for the name??

        # define a source for the new texture
        bge.logic.video.source = bge.texture.VideoFFmpeg("0", 0)  # first arg is the file/webcams, second is what to do
        print('Video source updated to', bge.logic.video.source)
        bge.logic.video.source.play()

    else:
        # Update image of the webcam on each tick
        bge.logic.video.refresh(True)
        print('Modally updating video source {} with status {}'
              .format(bge.logic.video.source, bge.logic.video.source.status))


##########################################################################
##                   POPUP MENU OVERLAY SCENE
##########################################################################


def bge_get_menu_scene():
    all_scenes = bge.logic.getSceneList()
    text_scene = all_scenes[pps.name_of_popup_object]
    print('Got the scene', text_scene)
    return text_scene


def show_menu_overlay():
    scn, objs, cont, own, acts = sg.get_scene_info()
    act = own.actuators['POPUP']
    cont.activate(act)


def hide_menu_overlay():
    scn, objs, cont, own, acts = sg.get_scene_info()
    act = own.actuators['POPUP_REMOVE']
    cont.activate(act)