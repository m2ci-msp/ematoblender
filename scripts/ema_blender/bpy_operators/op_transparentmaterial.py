__author__ = 'Kristy'
import bpy

"""
Module that contains a bpy simple operator.
The game-engine-compatible transparent texture is applied to the selected objects.
Alpha (transparency) is set at 0.5.
"""


def create_transparent_texture():
    """Return a special white material to control transparency using object color"""
    bpy.ops.material.new()
    whitetex = bpy.data.materials[-1]   # bpy.context.active_object.active_material
    whitetex.use_transparency = True
    whitetex.specular_intensity = 0
    whitetex.use_object_color = True
    return whitetex


def main(context):
    tex = create_transparent_texture()
    for cob in context.selected_objects:
        print('operating on', cob.name)
        cob.data.materials.append(tex)
        cob.draw_type = 'SOLID'
        cob.color = (1, 1, 1, 0.5)


class TransMatOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.transparent_material"
    bl_label = "Apply transparent material to selected"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(TransMatOperator)


def unregister():
    bpy.utils.unregister_class(TransMatOperator)


if __name__ == "__main__":
    register()

    # test call
    #bpy.ops.object.simple_operator()
