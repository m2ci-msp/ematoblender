__author__ = 'Kristy'

import bpy
from .bpy_workspace import postfn_gamemaster_reset_decorator


#####################################################
## NEW FUNCTIONS #
#####################################################


def bpy_make_straight_bones_all_with_ik(n, armature_name):
    # create the armature, set name from global value
    bpy.ops.object.mode_set(mode='OBJECT')
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
        b.use_connect = True

    bpy.ops.object.mode_set(mode='POSE')
    armobj = bpy.data.objects[armature_name]
    bpy.context.scene.objects.active = armobj
    global pointer_bones

    for i, b in enumerate(armobj.pose.bones):
        bpy.context.active_bone = b
        bpy.ops.pose.ik_add(with_targets=True)


    bpy.ops.object.mode_set(mode='OBJECT')



###################### old ####################


#TODO: These functions are useful when trying to automatically build an armature for a tongue mehsh.
#TODO: These are not used for playback, could be made by hand instead.

@postfn_gamemaster_reset_decorator
def bpy_create_tongue_bones(n=3, defs=10):
    """Create a chain of length n * (defs +1) where n is the number of sensors on the tongue (usually 3 if adding extra bones for tongue root);
    m is the number of bones between each tongue sensor (more = more flexibility of tongue movement).
    These bones will later move the tongue mesh using parenting."""

    global armature_name

    # create the armature, set name from global value
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.armature_add(radius=1, view_align=False, enter_editmode=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    bpy.context.object.data.name = armature_name
    bpy.context.object.name = armature_name

    # go into edit mode, set base bone name (all bones are Bone.000, Bone.001 etc)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.object.data.edit_bones['Bone'].name = 'Bone.000'
    bonecounter = 1

    # extrude the total number of bones needed and name them, beginning at the origin and moving up along z-axis
    for i in range(n* (defs+1)):
        bpy.ops.armature.extrude_move(ARMATURE_OT_extrude={"forked": False}, TRANSFORM_OT_translate={"value":(0, 0, 1), "constraint_axis":(False, False, False), "constraint_orientation":'GLOBAL', "mirror":False, "proportional":'DISABLED', "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False})
        bonecounter += 1

    # set standard properties for the newly-created bones
    # see http://www.blender.org/api/blender_python_api_2_74_5/bpy.types.EditBone.html
    editbones = bpy.context.object.data.edit_bones
    #editbones = bpy.data.armatures[armature_name].bones # not used due to read/write problems
    for i, b in enumerate(editbones):
        b.use_inherit_rotation = False
        b.use_inherit_scale = False
        b.use_connect = False # TODO: If using IK then must be true, set back!

    # create IK constraints for pointer bones (deformer bones unaffected)
    # create the context for selecting bones
    bpy.ops.object.mode_set(mode='POSE')
    armobj = bpy.data.objects[armature_name]
    bpy.context.scene.objects.active = armobj
    global pointer_bones

    for i, b in enumerate(armobj.pose.bones):
        # put IK constraints on 'pointer' bones (as yet without targets), to be added later when in position
        if i % (defs+1) == 0:  # if bone is controller
            pointer_bones.append(b.name)
            thisbone = b.bone
            armobj.data.bones.active = thisbone
            print("*****\n", thisbone.__dir__())
            bpy.ops.pose.ik_add(with_targets=False)
            b.constraints['IK'].chain_count = defs
            print('these are constraints on bone {}:'.format(b.name), b.constraints.keys())
            bpy.ops.pose.ik_add(with_targets=True)



@postfn_gamemaster_reset_decorator
def match_coils_to_controller_bones():
    """Return a list 'matched_coils_bones' with the coil empties and the bone names that should point to them.
    Creates a shrinkwrapped cube for each coil, that the user should move to the correct position on the tongue mesh."""
    # The numbers refer to the order that the coils are returned from the EMA machine, or are given in the data file,
    # counting in ascending order, starting with 0."""

    #  Cannot return the objects themselves, as these disappear in the switch between object and edit mode.
    # TODO - query rtclient for the XML, parse this to get the sensor numbers. Or maybe just display the XML data
    # TODO: these numbers will refer to the order that sensors are read into the data file. Sometimes they have a desription in the parameters. Should we access the server to show XML information at this point?

    global matched_coils_bones
    matched_coils_bones = []  # reset alignments

    # get external information about sensor indices (e which data belongs to which sensor)
    sd = b_sh.import_sensor_info_json()
    TB_index = sd["ActiveSensors"]["TB"]
    TM_index = sd["ActiveSensors"]["TM"]
    TT_index = sd["ActiveSensors"]["TT"]

   # set the context
    scn = bpy.context.scene
    bpy.ops.object.mode_set(mode='EDIT') # go to edit mode
    print("scene objects are",[x for x in scn.objects])
    print("bone objects are", [x for x in bpy.data.armatures[armature_name].bones])

    # parent each relevant coil to the controller bones from back to front
    for ind, (placeind, placename) in enumerate(sd["ActiveSensors"].items()):
        # get the coil object
        coilobj = scn.objects['CoilEmpty{}'.format(str(placeind).zfill(2))]

        # pointing bones in order root, back, mid, tip already listed
        bonename = pointer_bones[ind]
        # bonename = "Bone.{}".format(str((1+deformers)*(ind+1)).zfill(3))
        # print(bonename)

        armobj = bpy.data.armatures[armature_name]
        boneobj = armobj.bones[bonename]  # only exists in editmode, for object mode use bpy.context.object.data.bones[bonename]

        matched_coils_bones.append((str(coilobj.name), str(boneobj.name)))

        # Make a cube object parented to the coil so that it can be moved etc
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_cube_add()
        cube_obj = [obj for obj in bpy.context.scene.objects if obj.parent is None and obj.name.startswith("Cube")][-1]

        coilobj.location = cube_obj.location
        coilobj.parent = cube_obj # parent coil to cube, cube will be moved, coil rests on tongue tip.

        #cube_obj.parent = coilobj  # parent cube to coil (all currently at origin)
        cube_obj.name = placename
        cube_obj.show_x_ray = True
        cube_obj.show_name = True

        #bpy.data.objects[placename].select = True
        #bpy.context.scene.objects.active = coilobj
        mod = cube_obj.modifiers.new('Shrinkwrap', 'SHRINKWRAP')
        mod.target = bpy.data.objects[tongue_template_name]
        mod.wrap_method='PROJECT'
        mod.use_negative_direction, mod.use_positive_direction = True, True
#        mod.use_keep_above_surface = True

        mod.use_project_z = True
        mod.use_project_x, mod.use_project_y = False, False




@postfn_gamemaster_reset_decorator
def align_armature_to_coils(deformers=10):
    """ Align the bones in rest position by matching them along a spline created between the empties and root.
    To consider: Move the skeleton inwards based on the normals to ensure envelopes catch the right areas?
    Finalise the IK constraints on the relevant bones.

    Prev: Grab the coil-bone alignments, and pull the armature to where the cubes and coils have been put.
    Align the mid-point bones to a spline created between the two points."""
    # these are the matched names

    # TODO: For now, assume sensors on mid-saggital line, do not need to be moved.
    print("These are the names we matched with the coils", matched_coils_bones) # These are fake, cannot be saved globally during testing

    # set the context, select the armature
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_pattern(pattern=armature_name)
    bpy.context.scene.objects.active = bpy.data.objects[armature_name]
    armobj = bpy.data.objects[armature_name]

    # create a spline over the points
    coords = [(0, 0, 0)] + [bpy.data.objects[x[0]].location for x in matched_coils_bones] # arbitrary var for tongue root TODO: Consider this always the root location?
    curvenames = make_spline_thru_points(coords)

    # get the armature's final bone and snap it to the spline
    bpy.ops.object.mode_set(mode='POSE')
    boneobj = armobj.pose.bones[-1] # TODO: Check whether final bone in line
    #armobj.data.bones.active = boneobj

    boneobj.constraints.new('SPLINE_IK')
    #bpy.ops.pose.constraint_add(type='SPLINE_IK')
    boneobj.constraints['Spline IK'].target = bpy.data.objects[curvenames[-1]]
    boneobj.constraints['Spline IK'].chain_count = (deformers + 1) * 5  # some number larger than the bones in the chain
    # assume that the rest of the values are set by default
    # leave spline there, it does not have an effect in the game engine
    bpy.ops.object.mode_set(mode='OBJECT')


    # move it inwards in a fancy manner
    # TODO

    # put IK targets on the relevant bones
    bpy.ops.object.mode_set(mode='POSE')
    for cname, bname in matched_coils_bones:
        bobj = armobj.pose.bones[bname]
        bobj.constraints['IK'].target = bpy.data.objects[cname]


def set_armature_parenting():
    # select the armature
    armobj = bpy.data.objects[armature_name]
    armobj.select = True

    bpy.context.scene.objects.active = armobj

    # select the right type of parenting
    bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE') # ARMATURE_AUTO results in shape change

    # now must increase bone envelopes so that they catch the right stuff
    for b in armobj.data.bones:
        b.envelope_distance = 100 # TODO: This is completely arbitrary
