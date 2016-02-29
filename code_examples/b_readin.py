#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Kristy'

#
# Set up an external namespace for Blender fns to work in.
#


import bge
import rtclient


def execute():
    """The first execution to initialise the connection, etc."""
    print('executing initial')

    # create persistent objects for storing coordinates, connection etc
    bge.logic.positions = {}
    bge.logic.c, bge.logic.r = rtclient.init_connection()
    bge.logic.status = rtclient.test_communication(bge.logic.c, bge.logic.r)


def modal():
    """ Executed once every frame, check for key/button events. """
    print("executing modal")
    keyboard = bge.logic.keyboard

    # w key for setting up the coil objects
    if bge.logic.KX_INPUT_ACTIVE == keyboard.events(bge.events.WKEY):
        size, type, params = rtclient.get_parameters(bge.logic.c, bge.logic.r)

    # d key for one data frame
    if bge.logic.KX_INPUT_ACTIVE == keyboard.events(bge.events.DKEY):
        pass

    # s key for start streaming
    if bge.logic.KX_INPUT_ACTIVE == keyboard.events(bge.events.SKEY):
        pass

    # t key for stop streaming
    if bge.logic.KX_INPUT_ACTIVE == keyboard.events(bge.events.TKEY):
        pass

    # r key for reset to basic positions
    if bge.logic.KX_INPUT_ACTIVE == keyboard.events(bge.events.RKEY):
        pass




def access():
    print('accessing')
    print(bge.logic.c)
    print(bge.logic.r.readdata())
    print(bge.logic.status)




if __name__=="__main__":
    main()




############### BLENDER FUNCTIONS ###################
import bpy
import bge
from bge import logic
import mathutils


def b_make_controllers(myxmlroot):
    """ Read from given XML and make a controller for each marker."""

    # print(myxmlroot)
    # print(ET.tostring(myxmlroot))

    # TODO: Mark these as coil objects (eg give name/parent)
    # TODO: Show name
    # TODO: User chooses active/vs static
    # TODO: User can replace coils on tongue as needed

    markers = myxmlroot.findall("./The_3D/Markers/Marker")
    for i, m in enumerate(markers):
        print(i, m)
        bpy.ops.mesh.primitive_cube_add(radius=0.5, enter_editmode=False, location=(i, 0, 0))
        # other kwargs: layers, view_align


def b_update_locations(df=None):
    """ Read from a data frame object, update controller locations. Presume same order. """
    # TODO: Only iterate over coil objects
    if df is None:
        df = mydf
    print("This is my df", mydf)
    coils = mydf.components[0].coils

    # get the scene
    scene = logic.getCurrentScene()

    # match a location to a Blender object
    newpairs = zip(scene.objects, coils)
    print("This many scene objects", len(scene.objects))
    print("This many coils", len(coils))

    for obj, coil in newpairs:
        print("Object {} Coil {}".format(obj, coil))
        # for testing
        #obj.worldPosition = mathutils.Vector((3,3,3))
        obj.worldPosition = mathutils.Vector(coil.abs_loc)





