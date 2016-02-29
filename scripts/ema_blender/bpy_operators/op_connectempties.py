__author__ = 'Kristy'

"""
This is a bpy operator where you can define pairs of empties by names that should be parented.
It is a shortcut to doing these parenting relations by hand when importing a mesh to the game scene.
It usees the bpy simple operator template, with changed names and main method.
"""

import bpy


def main(context):
    pairs = [('CoilCube01', 'CoilEmpty01', 'TB_to_coil'),
             ('CoilCube02', 'CoilEmpty02', 'TM_to_coil'),
             ('CoilCube03', 'CoilEmpty03', 'TT_to_coil'),
             ('SL_L', 'InferredEmpty_SL_L', 'SL_L_Empty'),
             ('SL_R','InferredEmpty_SL_R', 'SL_R_Empty'),
             ('CoilCube04','CoilEmpty04', 'UL_to_coil'),
             ('CoilCube06','CoilEmpty06', 'LL_to_coil'),
             ('CoilCube11','CoilEmpty11', 'Jawend_empty'),
             #('CoilCube10', 'UI_to_coil'),
             ]
    for t, p, c in pairs:
        p = context.scene.objects.get(p, False)
        c = context.scene.objects.get(c, False)
        target = context.scene.objects.get(t, False)
        if p and c:
            p.matrix_world = target.matrix_world
            c.parent = p
            # unset the transformation to the parent's location
            c.matrix_parent_inverse = p.matrix_world.inverted()


class ParentingOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.empty_connector"
    bl_label = "Empty connector operator"

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ParentingOperator)


def unregister():
    bpy.utils.unregister_class(ParentingOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.empty_connector()
