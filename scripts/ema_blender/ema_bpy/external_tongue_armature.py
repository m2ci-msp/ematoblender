__author__ = 'Kristy'

# run run_bpy first to set path

import bpy
import scripts.ema_shared.properties as pps
import scripts.ema_blender.blender_shared_objects as bsh


def bpy_make_straight_bones_all_with_ik(n, armature_name):
    # create the armature, set name from global value
    hook_empties = []
#
    print('----------------------------')
    bpy.ops.object.armature_add(radius=1, view_align=False, enter_editmode=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    bpy.context.object.data.name = armature_name
    bpy.context.object.name = armature_name

    # go into edit mode, set base bone name (all bones are Bone.000, Bone.001 etc)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.object.data.edit_bones['Bone'].name = 'Bone.000'
    bonecounter = 1

    # extrude the total number of bones needed and name them, beginning at the origin and moving up along z-axis
    for i in range(n):
        bpy.ops.armature.extrude_move(ARMATURE_OT_extrude={"forked": False}, TRANSFORM_OT_translate={"value":(0, 0, 1), "constraint_axis":(False, False, False), "constraint_orientation":'GLOBAL', "mirror":False, "proportional":'DISABLED', "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False})
        bonecounter += 1

    # set standard properties for the newly-created bones
    # see http://www.blender.org/api/blender_python_api_2_74_5/bpy.types.EditBone.html
    editbones = bpy.context.object.data.edit_bones
    #editbones = bpy.data.armatures[armature_name].bones # not used due to read/write problems
    for i, b in enumerate(editbones):

        b.use_inherit_rotation = False
        b.use_inherit_scale = False
        b.use_connect = False

    bpy.ops.object.mode_set(mode='POSE')
    armobj = bpy.data.objects[armature_name]
    bpy.context.scene.objects.active = armobj
    global pointer_bones

    for j, b in enumerate(reversed(armobj.pose.bones)):

        i = len(armobj.pose.bones) - j

        constraint = b.constraints.new('IK')
        # make an empty at the tail

        emp = bpy.data.objects.new(bsh.tongue_top_empty_name(i), None)
        bpy.context.scene.objects.link(emp)
        hook_empties.append(emp)

        emp.location = b.tail
        print(emp.location, b.bone.tail)

        print('pose bone is', b)
        b.constraints["IK"].target = emp
        b.constraints["IK"].use_stretch = True
        b.constraints["IK"].chain_count = 1
        b.constraints["IK"].use_tail = True



    bpy.ops.object.mode_set(mode='OBJECT')
    return hook_empties, armobj

def main():
    hes, ao = bpy_make_straight_bones_all_with_ik(pps.tongue_intervals, pps.tongue_armature_name)
    bsh.tongue_top_empties = hes

if __name__ == "__main__":
    main()