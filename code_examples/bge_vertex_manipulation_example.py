import bge
import mathutils
import time


"""
This is an example script.
It shows how to select a mesh from an object,
then how to manipulate the vertices of that mesh to a set of pre-defined coordinates.
"""

# set a counter
if not hasattr(bge.logic, 'counter'):
    setattr(bge.logic, 'counter', 0)
else:
    bge.logic.counter += 1
    
print('The counter is', bge.logic.counter)

# set some points to manipulate
a = mathutils.Vector((-2,-2,0))
b = mathutils.Vector((5,5,0))
c = mathutils.Vector((-4,4,1))

# draw a line to test flashing
bge.render.drawLine(a,b,(1,0,0))

# select the cube
cube = bge.logic.getCurrentController().owner


import bmesh
import random

#cube.meshes[0].getVertex(0,v_index)
new_coordinates = [mathutils.Vector((x.x+ random.random(), x.y+ random.random(), x.z+ random.random()))  for x in [b,b,a,c,c,c,a,a] ]

# generally each object has one mesh
for mesh in cube.meshes:
    
    # get the material index (operate over all materials)
    for m_index in range(len(mesh.materials)):       
        vertices = [mesh.getVertex(m_index, i) for i in range(mesh.getVertexArrayLength(m_index))]
        
        for v, c in zip(vertices, new_coordinates):
            v.XYZ = c
        '''
        # for each vertex in the material
        for v_index in range(mesh.getVertexArrayLength(m_index)):
            
            # select the vertex object
            vertex = mesh.getVertex(m_index, v_index)
            # see https://www.blender.org/api/blender_python_api_2_74_5/bge.types.KX_VertexProxy.html#bge.types.KX_VertexProxy
            # Do something with vertex here...
            # ... eg: color the vertex red.
            if v_index == 1:
                vertex.XYZ = b
                vertex.x += bge.logic.counter % 10
            if v_index == 0 or v_index==7:
                vertex.XYZ = a
                vertex.y -= bge.logic.counter % 10
            


bme = bmesh.new()
#bme.from_mesh(cube.meshes[0].data)
bme.free()
'''