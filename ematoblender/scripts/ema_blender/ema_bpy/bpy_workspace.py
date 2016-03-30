__author__ = 'Kristy'
import bpy

#########################################################################
###                         DECORATORS
#########################################################################


def editmode_decorator(func):
    """Switch to editmode, execute fn, switch back to object mode."""
    def editmode_wrapper(*args, **kwargs):
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        func(*args, **kwargs)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    return editmode_wrapper


def posemode_decorator(func):
    """Switch to posemode, execute fn, switch back to object mode."""
    def posemode_wrapper(*args, **kwargs):
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        func(*args, **kwargs)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    return posemode_wrapper


def postfn_gamemaster_reset_decorator(func):
    """When function is complete, make sure that only the object named Gamemaster is active, nothing is selected."""
    def postgamemaster_wrapper(*args, **kwargs):
        func(*args, **kwargs)
        gm_obj = bpy.context.scene.objects['GameMaster']
        gm_obj.select = True
        bpy.context.scene.objects.active = gm_obj
        bpy.ops.object.select_all(action='DESELECT')
    return postgamemaster_wrapper


def prefn_gamemaster_reset_decorator(func):
    """Before function is executed, make sure that:
    only the object named Gamemaster is active,
     nothing is selected."""
    def pregamemaster_wrapper(*args, **kwargs):
        gm_obj = bpy.context.scene.objects['GameMaster']
        gm_obj.select = True
        bpy.context.scene.objects.active = gm_obj
        bpy.ops.object.select_all(action='DESELECT')
        func(*args, **kwargs)
    return pregamemaster_wrapper


def prefn_gamemaster_select_decorator(func):
    """Before function is executed, make sure that:
    only the object named Gamemaster is active,
     the Gamemaster is selected."""
    def pregamemaster_wrapper(*args, **kwargs):
        gm_obj = bpy.context.scene.objects['GameMaster']
        gm_obj.select = True
        bpy.context.scene.objects.active = gm_obj
        func(*args, **kwargs)
    return pregamemaster_wrapper


def prefn_objectmode_noselection_decorator(func):
    """Before the function is executed, make sure it is in object mode, and no objects are selected."""
    def pre_objmode(*args, **kwargs):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        func(*args, **kwargs)
    return pre_objmode

#########################################################################
###             INITIAL FUNCTIONS
#########################################################################


def get_context_info():
    scn = bpy.context.scene
    objs = scn.objects
    selected = [obj for obj in objs if obj.select]
    return scn, objs, selected


def reset_to_gamemaster():
    """Used at the end of fns to reset to object mode with only the Gamemaster selected."""
    gm_obj = bpy.context.scene.objects['GameMaster']
    gm_obj.select = True
    bpy.context.scene.objects.active = gm_obj
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  # go to object mode
    bpy.ops.object.select_all(action='DESELECT')


def set_workspace_properties():
    # set up the basic scene properties
    bpy.context.scene.render.engine = 'BLENDER_GAME'

    # set all 20 layers to visible so that external objects can be imported into these
    for y in range(19, -1, -1):
        bpy.context.scene.layers[y] = True

    #TODO: Set metric units


def do_on_scene_setup_decorator(fn):
    def inner(*args, **kwargs):
        print('Setting render engine to BLENDER_GAME')
        set_workspace_properties()
        print('Setting texture view to TEXTURED')
        set_texture_view()
        fn(*args, **kwargs)
        print('Creating cameras and video planes')
        build_scene_extra_objects()
    return inner


def build_scene_extra_objects():
    """Collects various object building scripts that should be executed in the construction"""
    from . import bpy_static_video as vid
    from . import bpy_setup_cameras as cam
    #vid.create_video_plane() # TODO: Add this when supporting video
    cam.add_circling_camera()
    cam.add_midsaggital_camera()
    cam.add_frontal_camera()


def set_texture_view():
    """Set the viewport shading options to TEXTURED so that the video textures appear correctly.
    Possibly a conflict as object transparency requires MATERIAL mode, but webcam/video requires TEXTURED mode."""

    # Inspired by: http://blender.stackexchange.com/questions/6101/poll-failed-context-incorrect-example-bpy-ops-view3d-background-image-add
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space_data = area.spaces.active
            space_data.viewport_shade = 'TEXTURED'


if __name__ == "__main__":
    # test decorator syntax
    @prefn_objectmode_noselection_decorator
    def print_sum(x, y):
        print('My sum is', x + y)
    print_sum(4, 5)
