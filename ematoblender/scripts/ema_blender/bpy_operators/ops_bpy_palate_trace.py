__author__ = 'Kristy'

"""
Modal operator that works in bpy to read the coordinates of one sensor over time.
These coordinates are recorded as edges on a mesh.
A second operator converts these egdes into a mesh using their maximum z-value.
"""

import math
import mathutils

import bpy
import bgl
import blf
import bmesh

from collections import deque
from collections import defaultdict

from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d
from ematoblender.scripts.ema_blender.coil_info import find_sensor_index
from ematoblender.scripts.ema_io.rtc3d_parser import DataFrame
import scripts.ema_blender.blender_networking as bn
import scripts.ema_blender.blender_shared_objects as bsh
import scripts.ema_shared.properties as pps
from ematoblender.scripts.ema_blender.ema_bpy.bpy_move_objects import apply_properties_transform


def draw_text_on_viewport(mystring):
    """Draw mystring into the viewport (eg to indicate progress)."""
# draw some text
    font_id = 0  # XXX, need to find out how best to get this.
    blf.position(font_id, 15, 30, 0)
    blf.size(font_id, 20, 72)

    blf.draw(font_id, mystring)


def draw_callback_px(self, context):
    """Modally called function that draws the lines as they are streamed.
    Firstly updates the viewport's text.
    Then draws the line based on points in self.point_path.
    """
    print("data points", len(self.point_path))

    # get region so can draw intermediate lines
    region = context.region
    rv3d = context.space_data.region_3d


    draw_text_on_viewport("{} vertices added, timestamp {}"
                          .format(str(len(self.point_path)), str(self.latest_ts)))
    # set the line parameters
    # 50% alpha, 2 pixel width line
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 0.5)
    bgl.glLineWidth(2)

    # draw the line here.....
    bgl.glBegin(bgl.GL_LINE_STRIP)
    # start from the origin for visual purposes
    for i in [0]:
        vertex = loc3d2d(region, rv3d, (i, i, i))
        print('vertex is', vertex)
        bgl.glVertex2f(vertex[0], vertex[1])

    for i, loc3d in enumerate(self.point_path):
        loc2d = loc3d2d(region, rv3d, loc3d)
        print(loc2d[0], loc2d[1], 'is the viewport coordinates')
        bgl.glVertex2i(math.floor(loc2d[0]), math.floor(loc2d[1]))
        #bgl.glVertex2i(math.floor(loc2d[0]%10), math.floor(loc2d[1]%10))

    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


class ModalDrawOperator(bpy.types.Operator):
    """
    Draw a line over the palate trace points,
    on finishing make a mesh with these vertices.
    """
    bl_idname = "view3d.palate_trace"
    bl_label = "Modal Palate Trace View3D Operator"

    def modal(self, context, event):
        """Do the modal instructions, whether it runs again depends on the value returned.
        Streams data when key 'c' is pressed.
        Click the left mouse button to finish the mesh creation.
        Click the right mouse button or Esc to cancel the mesh creation.
        If 'RUNNING MODAL' then do the modal handler then repeat,
        if 'FINISHED' it stops, if 'CANCELLED' then stops and revert.
        """
        context.area.tag_redraw()
        draw_text_on_viewport('Building mesh from palate trace.')

        if event.type == 'C':
            bn.send_to_gameserver(bsh.gs_soc_nonblocking) # get a single data frame
            #bn.send_to_gameserver(bsh.gs_soc_nonblocking, mode='STREAM_DF')
            responsedeque = bn.recv_to_deque(bsh.gs_soc_nonblocking)
            alldfs = [r for r in responsedeque if type(r) == DataFrame]
            if len(alldfs) == 0:
                return {'RUNNING_MODAL'}  # nothing received, skip

            self.df = alldfs[-1]
            self.latest_ts = self.df.give_timestamp_secs()
            for ind in self.trace_inds:  # for TT, TM, TB readings
                coil = self.df.give_coils()[ind]
                if getattr(coil, 'bp_corr_loc', None) is not None:
                    print('Got a legitimate reading', coil.bp_corr_loc)
                    self.point_path.append(coil.bp_corr_loc)
                elif hasattr(coil, 'abs_loc'):
                    print('got an absolute reading')
                    self.point_path.append(apply_properties_transform(coil.abs_loc))
                else:
                    print('This data frame failed', self.df)

        if event.type == 'MOUSEMOVE':
            pass #self.point_path.append((event.mouse_region_x, event.mouse_region_y))

        elif event.type == 'LEFTMOUSE':
            print("LMB event detected.")
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            #bn.send_to_gameserver(bsh.gs_soc_nonblocking, mode='STOP_STREAM')
            self.execute(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.execute(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        """
        Invoke starts the event by setting the self._handle attribute,
         then starting the window manager's modal_handler.
         """

        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.point_path = []
            self.latest_ts = 0.0
            self.df = dict()
            self.trace_inds = [find_sensor_index('TT'), find_sensor_index('TM'), find_sensor_index('TB')]

            bsh.gs_soc_nonblocking = bn.setup_socket_to_gameserver()
            #bn.send_to_gameserver(bsh.gs_soc_nonblocking, mode='START_STREAM')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

    def execute(self, context):
        """
        This is called when right before the function is finished.
        Makes the streamed data into a mesh object, rather than just a drawing on the viewport.
        """
        print('Performing the "execute" function.')
        # Create a mesh object to store polygon line
        mesh_obj = bpy.data.meshes.new("meshLine")

        # create a object data for mesh object
        obj_crt = bpy.data.objects.new("meshLine", mesh_obj)

        # link object to scene
        context.scene.objects.link(obj_crt)
        context.scene.objects.active = obj_crt

        # Now copy the mesh object to bmesh
        bme = bmesh.new()
        bme.from_mesh(obj_crt.data)
        #matx = obj_crt.matrix_world.inverted()

        # Add vertices
        list_verts = []
        for i in self.point_path:
            newvert = bme.verts.new(i)
            #print('newest vert is', newvert)
            list_verts.append(newvert) # ALEXANDER: THIS LIST OF VERTS THEN CONTAINS EACH VERTEX IN THE ORDER THEY WERE ADDED
        bme.verts.index_update()
        #print('verts list', [v for v in bme.verts])

        # Add edges to bmesh
        total_edge = len(list_verts)
        for j in range(total_edge - 1):
            bme.edges.new((list_verts[j], list_verts[(j + 1) % total_edge]))
            bme.edges.index_update()

        # add this data to bmesh object
        bme.to_mesh(obj_crt.data)
        bme.free()

        # set the origin of the bmesh blender object to a reasonable position
        scene = bpy.context.scene
        active = scene.objects.active
        scene.objects.active = obj_crt
        #print('old origin location is', obj_crt.location)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        #print('new origin location is', obj_crt.location)
        scene.objects.active = active

        # intialise all variables zero Value
        self.point_path[:] = []
        list_verts[:] = []
        self.depth_location = mathutils.Vector((0.0, 0.0, 0.0))
        return {'FINISHED'}

class PalateVertsToMesh(bpy.types.Operator):
    bl_idname = "view3d.palate_mesh"
    bl_label = "Palate Mesh from Trace View3D Operator"

    def invoke(self, context, event):
        """Take an object like a palate trace.
        Exclude points outside the interquartile range on x and y axes.
        Only looking at the vertices, put them in x-y buckets and choose the highest z-point.
        For unpopulated buckets, interpolate between the surrounding existing values."""
        # take the active object, get its vertices
        pobj = bpy.context.active_object
        pobjdat = pobj.data
        bme = bmesh.new()
        bme.from_mesh(pobjdat)


        # filter the data so only interquartile datapoints found
        xlist, ylist, zlist = [list(a) for a in zip(*[v.co for v in bme.verts])]
        xlist.sort(); ylist.sort(); zlist.sort()
        x_lower, x_upper = xlist[math.floor(len(xlist)*0.05)], xlist[math.floor(len(xlist)*0.95)]
        y_lower, y_upper = ylist[math.floor(len(ylist)*0.05)], ylist[math.floor(len(ylist)*0.95)]
        #z_lower, z_upper = zlist[math.floor(len(zlist)*0.25)], zlist[math.floor(len(zlist)*0.75)]

        print('boundaries', x_lower, x_upper, y_lower, y_upper)

        goodverts = []
        for v in bme.verts:
            x,y,z = v.co
            if x >= x_lower and x <= x_upper \
                and y >= y_lower and y<=y_upper: # TODO add Z condition if needed
                goodverts.append(v)

        print('the number of goodverts I got is', len(goodverts))


        datapoints = len(goodverts)
        axlen_x = 1  # NOTE THIS IS FOR A MID-SAGITTAL TRACE ONLY
        axlen_y = math.floor(math.sqrt(datapoints)/10) # NOTE: CHANGING THIS VALUE ACTS AS SMOOTHING
        print("Making palate shape from {} datapoints".format(datapoints))
        minx, maxx = min([v.co[0] for v in goodverts]), max([v.co[0] for v in goodverts])
        miny, maxy = min([v.co[1] for v in goodverts]), max([v.co[1] for v in goodverts])
        bucketsizex = (maxx - minx) / axlen_x
        bucketsizey = (maxy - miny) / axlen_y
        square_verts = sorted([(int((v.co[0]-minx) // bucketsizex),
                                int((v.co[1]-miny) // bucketsizey),
                                v.co[2]) for v in goodverts],
                              key=lambda x: (x[0], x[1]))

        print('axlen is', axlen_x)
        # make an array with every x-y bucket and the highest z-found there
        keys = [(x,y) for x in range(axlen_x+1) for y in range(axlen_y+1)]
        highestz = {k: None for k in keys}
        for x, y, z in square_verts:
            #print('xyz values', x, y, z)
            currentz = highestz[(x,y)]
            if type(currentz) is not float or (z > currentz): # if current score is none or a higher point is found
                highestz[(x,y)] = z
        #print('initial highestz is', highestz)

        # check how many unfilled z-positions there are
        empties = deque()
        for k, v in highestz.items():
            if v is None:
                empties.append(k)
        print('{} Z boxes are unfilled'.format(len(empties)))


        # find missing values with three neighbours, interpolate these values.
        skipcount = 0
        border = 3
        while len(empties) > 0:
            xe, ye = empties.popleft()
            neighbours = [k for k in [(xe, ye+1), (xe, ye-1), (xe+1, ye), (xe-1, ye)] if highestz.get(k, 0)]

            #print('I am empty with coordinates and n neighbours', (xe,ye), neighbours)
            if len(neighbours) >= border: # 2, 3 or 4 neighbours exist, interpolate
                skipcount = 0
                # TODO: Check that granularity is such that some of these are actually found
                highestz[(xe, ye)] = sum(highestz[n] for n in neighbours)/len(neighbours)

            else:
                skipcount += 1
                empties.append((xe,ye))

                if skipcount > axlen_x*10:  # arbitrary iteration condition
                    border -= 1
                    print('shrinking border to', border)
            if border == 0:
                break

                # now the highestz dictionary should be filled, check this
        print('z-values are:', highestz.values())

        xlines = defaultdict(list)  # save the points in list by x value
        ylines = defaultdict(list)  # save the points in list by y value
        pm = bmesh.new()  # make a new mesh for the filled palate

        # for the good points create a vertex and add to the edge/face list
        for ix in range(axlen_x):
            for iy in range(axlen_y):
                vertexval = ((ix * bucketsizex)+minx, (iy*bucketsizey)+miny, highestz[(ix,iy)])
                if vertexval[2] is not None:
                    newvert = pm.verts.new(vertexval)
                    xlines[vertexval[0]].append(newvert)
                    ylines[vertexval[1]].append(newvert)
        pm.verts.index_update()

        # make edges from the previously saved lists
        newedges = []
        for l in list(xlines.values()) + list(ylines.values()):
            for j in range(len(l)-1):
                vert1 = l[j]
                vert2 = l[j+1]
                # plausible value for continuous surface
                if abs(vert1.co[2] - vert2.co[2]) <= 4 * math.sqrt(math.pow(bucketsizex, 2) + math.pow(bucketsizey, 2)):
                    newedge = pm.edges.new((l[j], l[j+1]))
                    newedges.append(newedge)
        pm.edges.index_update()

        print('edges are', newedges)

        # make faces from the loops
        bmesh.ops.edgenet_fill(pm, edges=newedges)
        print('edges filled')
        print('my faces are', [f for f in pm.faces])

        # create the object to put this in
        bpm = bpy.data.meshes.new('FilledPalate')
        bpm_obj = bpy.data.objects.new('FilledPalate', bpm)
        context.scene.objects.link(bpm_obj)
        context.scene.objects.active = bpm_obj
        bpm_obj.location = pobj.location

        pm.to_mesh(bpm_obj.data)
        pm.free()

        # Save the mesh and wrap everything up
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ModalDrawOperator)
    bpy.utils.register_class(PalateVertsToMesh)


def unregister():
    bpy.utils.unregister_class(ModalDrawOperator)
    bpy.utils.register_class(PalateVertsToMesh)


def main():
    register()

if __name__ == "__main__":
    main()

