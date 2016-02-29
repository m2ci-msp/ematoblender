__author__ = 'Kristy'
import bpy
from scripts.ema_shared import properties as pps
#note: meshes and objects can be created in three different ways:
# http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Three_ways_to_create_objects


def set_tongue_physics():
    # select the mesh
    bpy.ops.object.select_pattern(pattern=pps.tonguemesh_name)

    # apply the physics to the mesh
    bpy.context.object.game.physics_type = 'SOFT_BODY'

    bpy.context.object.game.soft_body.use_cluster_rigid_to_softbody = True
    bpy.context.object.game.soft_body.use_cluster_soft_to_softbody = True


