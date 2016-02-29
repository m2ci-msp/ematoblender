__author__ = 'Kristy'

'''Create the context (UV texture of an arbitrary image on a plane) so that a video texture can be displayed in BGE.
This texture uses Alpha Add, so that the black of the ultrasound is not shown.
Inspired by:
 http://www.tutorialsforblender3d.com/Blender_GameEngine/Alpha/Alpha_GLSL_3.html
 http://pymove3d.sudile.com/stations/blender-basics/h_material/hi_material_uv_mapping.html
 https://www.youtube.com/watch?v=jgAippm3QXw
 '''

import bpy
import os
from scripts.ema_blender.ema_bpy.bpy_workspace import set_workspace_properties, postfn_gamemaster_reset_decorator
from scripts.ema_shared import properties as pps

@postfn_gamemaster_reset_decorator
def create_video_plane(alpha='ADD', planename='UltrasoundPlane', placeholderfile='./images/black.jpg'):
    """Create a plane at the cursor location that nominally shows the placeholderfile, but really is a video updated by name.
    Alpha controls whether black parts are shown as transparent (ADD is transparent, and transparent when no video is shown if a black image is used.
    Set alpha as 'OPAQUE' to show black images/video as such in the GE."""

    print('ADDING VIDEO PLANE WITH INITIAL IMAGE: {}'.format(placeholderfile))
    set_workspace_properties()  # put into game mode

    # add a plane called UltrasoundPlane
    bpy.ops.mesh.primitive_plane_add()
    plane = bpy.context.object
    plane.name = planename

    # add a material to the plane called 'Screen'
    bpy.ops.material.new()
    screenmat = bpy.data.materials[-1]
    screenmat.name = 'Screen'
    screenmat.use_shadeless = True

    # remove all shadow behaviour
    screenmat.use_shadows = False
    screenmat.use_cast_shadows = False
    screenmat.use_cast_buffer_shadows = False

    # apply the material to the plane
    plane.data.materials.append(screenmat)

    # game settings
    screenmat.game_settings.use_backface_culling = True
    screenmat.game_settings.alpha_blend = alpha

    # todo: save this placeholder in repositoy, access relative to blend file
    if not os.path.isabs(placeholderfile):
        fp = os.path.normpath(pps.abspath_to_repo + os.path.sep + placeholderfile)
    else:
        fp = placeholderfile
    _, placeholdername = os.path.split(fp)
    print('opening', fp)
    bpy.ops.image.open(filepath=fp)

    # Add any texture
    mytex = bpy.data.textures.new('holdertex', type="IMAGE")
    image = bpy.data.images[placeholdername]
    mytex.image = image


    # connect texture and material
    slot = screenmat.texture_slots.add()
    screenmat.active_texture = mytex
    slot.texture_coords = 'UV'
    slot.mapping = "FLAT"

    # put the plane in edit mode, project the image onto the plane (UV coords)
    bpy.ops.object.mode_set(mode='EDIT')

    first_context = bpy.context.area.type
    bpy.context.area.type = 'IMAGE_EDITOR'
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            bpy.ops.image.open(filepath=fp)
    bpy.context.area.type = first_context

    bpy.ops.object.mode_set(mode='OBJECT')

if __name__ == "__main__":
    create_video_plane(alpha='ADD', planename='UltrasoundPlane', placeholderfile='./images/black.jpg')
