__author__ = 'Kristy'
import bpy

# NOT used at the moment!

#todo: ongoing - IF PUTTING BONES ON SURFACE OF COMPLEX MESH
def make_spline_from_mesh(meshname):
    """Take the shortest path over the mesh to get the surface. Convert to a curve, return it."""
    #TODO - ongoing as of Wed evening

    # select the mesh
    bpy.ops.object.select_pattern(pattern=tongue_template_name)
    # go to edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    # select the shortest path based on closest coords to matched_coils_bones
    coords = [(0, 0, 0)] + [bpy.data.objects[x[0]].location for x in matched_coils_bones] # (root, back, mid, tip)

    # select two faces
    bpy.ops.mesh.shortest_path_pick(extend=True)

    # duplicate the selection
    # bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1}, TRANSFORM_OT_translate={"value":(21.6314, 1.28026, -3.78573), "constraint_axis":(False, False, False), "constraint_orientation":'GLOBAL', "mirror":False, "proportional":'DISABLED', "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False})

    # separate the selction

    # convert the selection to a curve
    #bpy.ops.object.convert(target='CURVE')





# todo: CURRENT FN, ALIGNS BONES THROUGH MANUAL PLACEMENT
def make_spline_thru_points(coords, curvenames=[]):
    """Draw a spline through the pre-set TT, TM, TB coils.
    Heavily drawn from http://blender.stackexchange.com/questions/6750/poly-bezier-curve-from-a-list-of-coordinates
    Curvenames stores the names of all the splines created, for later access."""

    print("\n\nCoordinates given", coords)
    # create the Curve Datablock
    curveData = bpy.data.curves.new('myCurve', type='CURVE')
    curveData.dimensions = '3D'
    curveData.resolution_u = 2


    # map coords to spline
    polyline = curveData.splines.new('POLY') # TODO: Why this and not [‘POLY’, ‘BEZIER’, ‘BSPLINE’, ‘CARDINAL’, ‘NURBS’]
    polyline.points.add(len(coords)-1)
    for i, coord in enumerate(coords):
        x,y,z = coord
        polyline.points[i].co = (x, y, z, 1)

    # create Object
    newname = 'TongueCurve.'+str(len(curvenames)).zfill(3)
    curveOB = bpy.data.objects.new(newname, curveData)
    #curveOB.location = coords[0]

    # attach to scene and validate context
    scn = bpy.context.scene
    scn.objects.link(curveOB)

    # do not select (thus commented out)
    # scn.objects.active = curveOB
    # curveOB.select = True

    # return names for future reference
    curvenames.append(newname)
    return curvenames

