__author__ = 'Kristy'

# my code based on Alexander Hewer's
import mathutils


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


if __name__ == "__main__":
    bp = BitePlane((3.732703,-79.734947,-222.91179),(-36.90427,32.382603,-166.20944), (-55.746994,22.703554,-168.1194))
    print(bp.project_to_global((0,0,0)))
    bpm = bp.give_local_to_global_mat()
    print(bpm)
    print(mathutils.Vector((0,0,0))* bpm)


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
