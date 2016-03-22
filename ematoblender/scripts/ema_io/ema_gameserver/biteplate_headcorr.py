__author__ = 'Kristy'

# my code based on Alexander Hewer's
import mathutils
import os

from . import data_manipulation as dm
from ..rtc3d_parser import DataFrame
from ...ema_shared import properties as pps
from ...ema_blender import coil_info as ci


class HeadCorrector(object):
    """Container class for various bite-plane and reference plane objs
    Handles loading head-corrector objects,
    Recording head-corrector objects from a TSV
    Recording head-corrector objects from live data
    Pickling the objects etc.
    
    self.load handles the acquisition of the data
    self.save handles saving the data
    """
    recordsecs = 10
    
    def __init__(self):
            
        self.biteplane = NotImplemented
        self.refplane = NotImplemented # coordinate system around reference sensors in global space
        self.inputmode = NotImplemented
        
        self.active_indices = NotImplemented
        self.reference_indices = NotImplemented
        self.biteplate_indices = NotImplemented
        
        self.get_coil_role_indices()
        
    # todo: given dataframe, headcorrect only
    
    # todo: given dataframe, biteplate correct only
    
    # todo: given dataframe, biteplate and headcorrect
    
    def get_coil_role_indices(self):
        self.active_indices, self.biteplate_indices, self.reference_indices = \
        ci.get_sensor_indices_by_role()
    
    def load_from_tsv_file(self, tsv_name):
        tsv_name = os.path.normpath(os.getcwd() + os.sep + tsv_name) \
        if not os.path.isabs(tsv_name) else tsv_name
        if os.path.isfile(tsv_name):
            from ..ema_staticserver.mocap_file_parser  import TSVParser
            bytesdfs = TSVParser(tsv_name).give_all_motion_frames()
            dfs = [DataFrame(rawdf=b) for b in bytesdfs]
            print("about to process:", dfs[0])
            if len(dfs) > 1:
                av = self.process_frames_pre_calc(dfs)
                self.calc_COBs_from_df(av)
            else:
                raise ValueError("There is not enough data in the TSV file for a head-correction.")

        else:
            print('The TSV file could not be loaded')
            raise FileNotFoundError(tsv_name)
            
    def load_live(self, serverobj, seconds=5):
        """Using the server object, """
        response = self.inform_recording_start()
        
        # if response is to abort:
        if not response == 1:
            print("Live streaming aborted.")
        
        # if streaming ready, stream biteplate recording for 5 seconds
        else:
            dfs = self.record_for_seconds(serverobj, secs=self.__class__.recordsecs)
            av = self.process_frames_pre_calc(dfs)
            self.calc_COBs_from_df(av)
            
            self.inform_recording_end()
            
    @staticmethod
    def inform_recording_start():
        """launch a dialog on Windows to pause until biteplate-recording is ready"""
        #TODO: Is system used on other OS? If so, inform appropriately.
        if os.name == 'nt':
            import ctypes
            ready = ctypes.windll.user32.MessageBoxA(0, b"Click OK when ready to start biteplate recording.\nHold still with sensors attached.",b"Biteplate recording", 1)
        elif os.name == 'posix':
            print('TODO: Launch a unix-style dialog to pause while changing rtserver to biteplate recording')
            ready = 1
        else:
            ready = 1
        return ready
        
    @staticmethod
    def inform_recording_end():
        """TODO: Inform the user about the recordings, 
        instruct them to prepare the tongue sensors.
        """
        print('NOW PREPARE FOR NORMAL STREAMING')
        if os.name == 'nt':
            import ctypes
            notification = ctypes.windll.user32.MessageBoxA(0,
            b"Set up your wave/server for streaming of active sensor data",
            b"Biteplate recording finished", 0)
        
        
    def record_for_seconds(gameserverobj, secs=None):
        """Ask the gameserverobj to stream secs of data.
        If secs==None, then the time value from the pps file is used.
        """
        gameserberobj.repl._stop_b = True  # stop the normal behaviour of the data queue
            
        print('About to stream utilising the replies queue:', 
        gameserverobj.repl._b.is_alive())

        # start streaming, get either secs or (in properties) defined seconds of streaming data
        gameserverobj.gs_start_streaming()      
        print('started streaming')
        time.sleep(pps.head_correction_time if secs is None else secs)

        # stop streaming
        gameserverobj.gs_stop_streaming()
        print('stopped streaming')
        time.sleep(1)

        # access all the streamed data, empty the queue, saved elements in replies
        print('qsize is ',gameserverobj.repl._q34.qsize())
        all_streamed = []
        while not server.repl._q34.empty():
            streamed_df = DataFrame(rawdf=gameserverobj.repl._q34.get()[2])
            print('this streamed df was', streamed_df)
            all_streamed.append(streamed_df)
            
        # reset internal settings
        gameserverobj.repl.latest_df = None
        gameserverobj.repl.last_x_dfs.clear()
        gameserverobj.repl._stop_b = False  # restart the normal behaviour of streamed data
        
        #print('\n\nstreamed data looks like', all_streamed[:1])
        return all_streamed # a list of dataframe objects streamed
            
    def process_frames_pre_calc(self, list_of_dfs):
        """Remove the first and last ms of the list
        Then remove outliers from the list
        Then average the remaining frames, returning an average object.
        """
        last_frames = dm.remove_first_ms_of_list(list_of_dfs,
                       ms=1 if pps.head_correction_exclude_first_ms is None
                       else pps.head_correction_exclude_first_ms)
        no_outliers= dm.remove_outliers(last_frames)
        print("no_outliers is", no_outliers[-1])
        print("averaguing", DataFrame(fromlist=no_outliers))

        return DataFrame(fromlist=no_outliers)
    
    def load_pickled_from_file(self, pickledfile):
        """If available, unpickle biteplate reps from these locations."""
        if os.path.isfile(pickledfile):
            print('loading the pickled biteplate from', pickledfile)
            pobj = pickle.load(open(bp_fn, 'rb'))
            self.__dict__= pobj.__dict__
        else:
            raise FileNotFoundError

    def save_changes_of_base(self):
        """Save the Biteplane and Referenceplane Changes of Base to pickled files."""
        pickle.dump(bp_in_rs, open(os.path.normpath(__file__ + "../../../" + os.path.sep + pps.biteplate_cs_storage), 'wb'))
        pickle.dump(rp_in_gs, open(os.path.normpath(__file__ + "../../../" + os.path.sep + pps.refspace_cs_storage), 'wb')) 

    def give_bp_rs(self):
        """Return the biteplane obj and the refplane object"""
        return self.biteplane, self.refplane
        
    def __str__(self):
        return 'correcting matrices are\n'+ \
        str(self.refplane.give_local_to_global_mat()) + "\n" + \
        str(self.biteplane.give_global_to_local_mat())
                
    def calc_COBs_from_df(self, df):
        """Calculate the changes of base off one average dataframe"""
        
        # isolate the coil objects
        refcoils = [df.give_coils()[i] for i in self.reference_indices]
        bpcoils = [df.give_coils()[i] for i in self.biteplate_indices]
        
        lind, rind, find = [ci.find_sensor_index(n) for n in ['BP1', 'BP2', 'BP3']]  #todo: check order
        
        # create a coordinate-system based on reference sensors (fully-defined here)
        self.refplane = ReferencePlane(*[x.abs_loc for x in refcoils[:3]])

        # transform the bpcoils into the FOR of the refplane
        for c in bpcoils:
            c.ref_loc = self.refplane.project_to_lcs(c.abs_loc)  
            
        # create an origin-less biteplane FOR in reference space
        self.biteplane = BitePlane(*[df.give_coils()[x].ref_loc for x in [lind, rind, find]])


class BitePlane(object):
    """Use biteplate coordinates to construct a local coordinate system centered around an origin.
    The biteplate represents a transverse plane (or as near as possible) through the skull"""

    # Orientation a la Blender's Front/Top etc:
    #  yz is sagittal
    #  xy is transverse
    #  zx is coronal

    # x points dextral, y points posterior, z points superior
    # initial origin is within biteplate

    def __getstate__(self):
        """Used for pickling, but saves Vector objects as tuples."""
        result = self.__dict__.copy()
        for k, v in result.items():
            if type(v) == mathutils.Vector:
                result[k] = tuple(v)
            if type(v) == mathutils.Matrix:
                result[k] = None
        return result

    def __setstate__(self, dict):
        """Used for unpickling, set tuples to mathutils.Vectors."""
        for k, v in dict.items():
            if type(v) == tuple:
                dict[k] = mathutils.Vector(v)
        self.__dict__ = dict

    def __init__(self, leftcoords, rightcoords, frontcoords):
        """Collect the coil positions.
        Leftcoords/Rightcoords are on the left/right respectively from the experimenter's perspective,
        ie for the subject dexter/sinister."""

        print('Initialising a BitePlane object')
        self.left_coil = mathutils.Vector(leftcoords)
        self.right_coil = mathutils.Vector(rightcoords)
        self.front_coil = mathutils.Vector(frontcoords)

        self.origin = mathutils.Vector()

        self.x_axis = mathutils.Vector()
        self.y_axis = mathutils.Vector()
        self.z_axis = mathutils.Vector()

        self.transform_mat = None

        self.compute_local_cs()

    def compute_local_cs(self):
        """Compute the axes of the local coordinate system in the global coordinate system."""

        # compute vectors based on the sensor locations
        right_to_left  = self.right_coil - self.left_coil

        lr_midpoint = (self.right_coil + self.left_coil) * 1/2
        front_to_back = self.front_coil - lr_midpoint

        # normalise the vectors
        right_to_left.normalize()
        front_to_back.normalize()

        # take the right_to_left vector as the x-axis
        self.x_axis = right_to_left

        # take a z-axis that is orthonormal to the plane of right_to_left and back_to_front
        self.z_axis = mathutils.Vector.cross(right_to_left, front_to_back)
        self.z_axis.normalize()

        # recompute the y-axis as orthonormal to the x-z plane
        self.y_axis = mathutils.Vector.cross(self.z_axis, self.x_axis)  # TODO: Initially  x, z, but y-axis needs to project backwards
        self.y_axis.normalize()

        # set the origin as the centre of the biteplate
        self.origin = lr_midpoint
        self.ui_origin = False

    def set_origin(self, ui_loc):
        """Set the origin to the upper-incisor location in global space."""
        self.origin = ui_loc
        self.ui_origin = True

    def project_to_lcs(self, global_loc):
        """Return the coordinates in the current coordinate system."""
        shifted_position = mathutils.Vector(global_loc) - self.origin
        return mathutils.Vector((shifted_position * self.x_axis,
                                 shifted_position * self.y_axis,
                                 shifted_position * self.z_axis
                                ))

    def project_to_global(self, local_loc):
        """Take coordinates in this local coordinate system, return the coordinates in the global system."""
        local_loc = mathutils.Vector(local_loc)
        global_loc = local_loc.x * self.x_axis
        global_loc += local_loc.y * self.y_axis
        global_loc += local_loc.z * self.z_axis
        global_loc += self.origin

        return global_loc

    def create_matrices(self):
        """Create the global_to_local and local_to_global transformation matrices."""
        trans_mat = mathutils.Matrix.Translation(-self.origin)
        # to local
        rot_mat = mathutils.Matrix()  # creates identity matrix
        rot_mat[0][0:3] = self.x_axis
        rot_mat[1][0:3] = self.y_axis
        rot_mat[2][0:3] = self.z_axis
        transform_mat = rot_mat * trans_mat  # this is used for pre-multiplication, so translation is applied first

        # to global
        inv_transform_mat = mathutils.Matrix.Translation(self.origin) * rot_mat.transposed()  # this is used for post-multiplication
        return transform_mat, inv_transform_mat

    def give_global_to_local_mat(self):
        # make the translation matrix that transforms global to local
        return self.create_matrices()[0]

    def give_local_to_global_mat(self, listed=False):
        # this is untested. aims to indicate how camera should track if showing head mvmt
        inv_tranfrom_mat = self.create_matrices()[1]
        if not listed:
            return inv_tranfrom_mat
        else:
            return [list(x) for x in inv_tranfrom_mat]


class ReferencePlane(BitePlane):
    """Class describing a coordinate system from the head-sensors in the
    space of either global coords or biteplate-corrected coords, depending on input given."""

    def __init__(self, leftcoords, rightcoords, frontcoords):
        print('Initialising a reference plane object')
        super().__init__(leftcoords, rightcoords, frontcoords)
        super().set_origin((mathutils.Vector(frontcoords) +
                            mathutils.Vector(rightcoords) +
                            mathutils.Vector(leftcoords)) / 3)  # make the origin of the referenceplane system the centre

    # project to local coordinates using inherited system
    # project back to original coordinate system


class ScalingPlane(BitePlane):

    def __init__(self, leftcoords, rightcoords, frontcoords):
        print('Initialising a reference plane object')
        super().__init__(leftcoords, rightcoords, frontcoords)
        super().set_origin((mathutils.Vector(rightcoords) +
                            mathutils.Vector(leftcoords)) / 2)  # make the origin of the referenceplane system the centre


def main():
    bp = BitePlane((3.732703,-79.734947,-222.91179),(-36.90427,32.382603,-166.20944), (-55.746994,22.703554,-168.1194))
    print(bp.project_to_global((0,0,0)))
    bpm = bp.give_local_to_global_mat()
    print(bpm)
    print(mathutils.Vector((0,0,0))* bpm)
    tsv_name = "/home/kristy/local/repos/ematoblender/data/Example3.tsv"
    fromtsv = HeadCorrector()
    fromtsv.load_from_tsv_file(tsv_name)
    print(fromtsv)


if __name__ == "__main__":
    main()


    #rf = ReferencePlane((88.924011,46.925743,-132.47382),(-18.506304,-0.313194,-160.08165),(-25.692158,9.625629,-165.58427))



#
#
# # below from Alexander Hewer
# import os
# import bpy
# import mathutils
#
# class BitePlane:
#
#     def __init__(self, obj):
#
#         self.leftCoil = obj.pose.bones['BiteLeft']
#         self.rightCoil = obj.pose.bones['BiteRight']
#         self.backCoil = obj.pose.bones['BiteBack']
#
#         self.origin = mathutils.Vector()
#         self.Xaxis = mathutils.Vector()
#         self.Yaxis = mathutils.Vector()
#         self.Zaxis = mathutils.Vector()
#
#         self.source = mathutils.Vector()
#         self.target = mathutils.Vector()
#
#         self.computeBitePlane()
#
#     def computeBitePlane(self):
#
#         # compute vectors inside the plane
#         rightToLeft = self.leftCoil.location - self.rightCoil.location
#         leftToBack = self.backCoil.location - self.leftCoil.location
#
#         # normalize
#         rightToLeft.normalize()
#         leftToBack.normalize()
#
#         # compute basis
#         self.Xaxis = rightToLeft
#         self.Yaxis = mathutils.Vector.cross(self.Xaxis, leftToBack)
#         self.Yaxis.normalize()
#         self.Zaxis = mathutils.Vector.cross(self.Xaxis, self.Yaxis)
#
#         # compute origin
#         self.origin = self.backCoil.location # ( self.rightCoil.location + self.leftCoil.location + self.backCoil.location ) / 3
#
#     def project(self, location):
#
#         # shift origin
#         shiftedPosition = location - self.origin
#
#         transformedPosition = mathutils.Vector()
#         transformedPosition.x = shiftedPosition * self.Xaxis
#         transformedPosition.y = shiftedPosition * self.Yaxis
#         transformedPosition.z = shiftedPosition * self.Zaxis
#
#         return transformedPosition
#
#
# #        transformedPosition = mathutils.Vector()
# #        transformedPosition += location.x * self.Xaxis
# #        transformedPosition += location.y * self.Yaxis
# #        transformedPosition += location.z * self.Zaxis
# #        transformedPosition += self.origin
#
# #        return transformedPosition
#
# class ReferenceFrame:
#
#     def __init__(self, obj):
#
#         self.threshold = 3
#         self.noseBridge = obj.pose.bones['NoseBridge']
#         self.leftEar = obj.pose.bones['LeftEar']
#         self.rightEar = obj.pose.bones['RightEar']
#
#         self.leftEarToNoseDistance  = (self.leftEar.location - self.noseBridge.location).length
#         self.rightEarToNoseDistance = (self.rightEar.location - self.noseBridge.location).length
#
#         self.origin = mathutils.Vector()
#         self.Xaxis = mathutils.Vector()
#         self.Yaxis = mathutils.Vector()
#         self.Zaxis = mathutils.Vector()
#
#     def isValid(self):
#
#         currentLeftToNoseDistance = (self.leftEar.location - self.noseBridge.location).length
#         currentRightToNoseDistance = (self.rightEar.location - self.noseBridge.location).length
#
#         leftDifference  = abs(self.leftEarToNoseDistance  - currentLeftToNoseDistance )
#         rightDifference = abs(self.rightEarToNoseDistance - currentRightToNoseDistance)
#
#         if leftDifference > self.threshold or rightDifference > self.threshold:
#             return False
#         else:
#             return True
#
#     def updateCoordinateSystem(self):
#
#         # compute vectors inside the plane
#         rightEarToLeftEar = self.leftEar.location - self.rightEar.location
#         leftEarToNoseBridge = self.noseBridge.location - self.leftEar.location
#
#         # normalize
#         rightEarToLeftEar.normalize()
#         leftEarToNoseBridge.normalize()
#
#         # compute basis
#         self.Xaxis = rightEarToLeftEar
#         self.Yaxis = mathutils.Vector.cross(self.Xaxis, leftEarToNoseBridge)
#         self.Yaxis.normalize()
#         self.Zaxis = mathutils.Vector.cross(self.Xaxis, self.Yaxis)
#
#         # compute origin
#         self.origin = ( self.rightEar.location + self.leftEar.location + self.noseBridge.location ) / 3
#
#     def project(self, location):
#
#         # shift origin
#         shiftedPosition = location - self.origin
#
#         transformedPosition = mathutils.Vector()
#         transformedPosition.x = shiftedPosition * self.Xaxis
#         transformedPosition.y = shiftedPosition * self.Yaxis
#         transformedPosition.z = shiftedPosition * self.Zaxis
#
#         return transformedPosition
#
#     def backProject(self, location):
#
#         transformedPosition  = location.x * self.Xaxis
#         transformedPosition += location.y * self.Yaxis
#         transformedPosition += location.z * self.Zaxis
#         transformedPosition += self.origin
#
#         return transformedPosition
#
#
# # read command line parameters from environment
# bvhFile = os.getenv('bite_plane')
# palateTrace = os.getenv('palate_trace')
# output = os.getenv('output')
#
# # empty scene
# bpy.ops.object.mode_set(mode='OBJECT')
# for ob in bpy.context.scene.objects:
#     bpy.context.scene.objects.unlink(ob)
#
# # import motion capture data
# bpy.ops.import_scene.obj(filepath=palateTrace, axis_forward='Y', axis_up='Z')
# bpy.ops.import_anim.bvh(filepath=bvhFile)
#
# bpy.ops.object.mode_set(mode = 'POSE')
# scene = bpy.context.scene
#
# for obj in bpy.data.objects:
#     if obj.type == 'ARMATURE':
#         armature = obj
#
# palateTraceMeshName = os.path.splitext(os.path.basename(palateTrace))[0]
#
# palateTraceVertices = bpy.data.objects[palateTraceMeshName].data.vertices
#
# bitePlane = BitePlane(armature)
# referencePlane = ReferenceFrame(armature)
#
# referencePlane.updateCoordinateSystem()
#
# # get position into bitePlane coordinate system
# for vertex in palateTraceVertices:
#     vertex.co = referencePlane.backProject(vertex.co)
#     vertex.co = bitePlane.project(vertex.co)
#
# # remove armature
# bpy.ops.object.mode_set(mode='OBJECT')
# for ob in bpy.context.scene.objects:
#     if ob.type == 'ARMATURE':
#         bpy.context.scene.objects.unlink(ob)
#
#
# bpy.context.scene.objects.active = bpy.data.objects[palateTraceMeshName]
# bpy.ops.export_scene.obj(filepath=output, use_mesh_modifiers=False, use_normals=False, use_materials=False, use_blen_objects=False, axis_forward='Y', axis_up='Z')
#
# # quit blender
# quit()
