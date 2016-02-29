__author__ = 'Kristy'
import bpy
from . import bpy_workspace as ws
import os
import json
from scripts.ema_shared import properties as pps
from scripts.ema_blender import blender_shared_objects as bsh

import scripts.ema_shared.general_maths as bm
import scripts.ema_blender.coil_info as ci


def link_lips_to_coils():
    """Use the shared objects lip_control_points to fix the lips to the relevant sensors."""
    #todo: PRESCALE AND PLACE ARMATURE SO THIS DOESN'T GET TOO WEIRD
    lip_ul = bpy.data.objects.get(pps.UL_empty_name, 0)
    lip_ll = bpy.data.objects.get(pps.LL_empty_name, 0)
    lip_sll = bpy.data.objects.get(pps.SL_empty_name_right, 0)

    for i, obj, place in bsh.ema_active_meshes:
        if place == 'UL':
            #lip_ul.location = obj.location
            lip_ul.parent = obj
        elif place == 'LL':
            #lip_ll.location = obj.location
            lip_ll.parent = obj
        elif place == 'SL':
            #lip_sll.location = obj.location
            lip_sll.parent = obj








# lets after the user has placed sensors on the tongue manually
@ws.postfn_gamemaster_reset_decorator
@ws.prefn_gamemaster_reset_decorator
def post_alignment_by_hand():
    """Do all the things that need to be done after the TT, TM, TB cubes and empties have been shrinkwrap-moved..."""
    cubes = ['TT', 'TM', 'TB']

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # move the origin of the shrinkwrapped things to the mesh surface, move the children there too
    for cn in cubes:
        bpy.ops.object.select_pattern(pattern=cn)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        cubeobj = bpy.data.objects[cn]
        thisempty = cubeobj.children[0]
        thisempty.location = cubeobj.location

    # make the shrinkwrapped things into cubes again
        cubeobj.modifiers.remove(cubeobj.modifiers['Shrinkwrap'])

