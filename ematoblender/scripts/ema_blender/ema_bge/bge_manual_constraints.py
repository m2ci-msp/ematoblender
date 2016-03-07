__author__ = 'Kristy'

import mathutils
from ematoblender.scripts.ema_blender import blender_shared_objects as bsh

"""This file controls manual constraints on objects that are executed every frame.
For example, if one object must always mirror another, it is controlled here.
These are unused."""

#unused
# def execute_every_tick():
#     """Functions that impose other constraints on objects that must be manually executed every tick."""
#     mirror_location_across_yz_plane(bsh.sidelip_mover, bsh.sidelip_follower)
#     pass
#
#
# def mirror_location_across_yz_plane(mover, follower):
#     follower.worldPosition = mathutils.Vector(- mover.worldPosition.x, mover.worldPosition.y, mover.worldPosition.z)
#     # Note No rotation at the moment as neither in Euler angles nor quaternions