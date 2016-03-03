__author__ = 'Kristy'

import bpy

class AddGameMasterOperator(bpy.types.Operator):
    """Add game master etc"""
    bl_idname="object.add_gamemaster"
    bl_label="Add Gamemaster"

    @classmethod
    def poll(cls, context):
        # TODO: Change polling for the fact that it doesn't already exist
        return context.active_object is not None

    def execute(self, context):
        from scripts.ema_blender.ema_bpy.bpy_add_game_objects import add_game_master
        add_game_master()
        return {'FINISHED'}
