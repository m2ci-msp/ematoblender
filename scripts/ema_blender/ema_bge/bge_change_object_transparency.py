__author__ = 'Kristy'

# How to set this up (complex!)
    # make a new material
    #set the object's material as color 1,1,1,1
    # activate transparency
    # under options activate object color

    # object color can be accessed as obj.color = [r,g,b,a]

import bpy

def create_transparent_texture():
    bpy.ops.material.new()
    whitetex = bpy.data.materials[-1]   #bpy.context.active_object.active_material
    whitetex.use_transparency = True
    whitetex.use_object_color = True
    return whitetex


def make_possibly_transparent(obj, percent_trans=50):
    obj.data.materials.append(create_transparent_texture())
    obj.color[-1] = percent_trans/100



# # select the object that should be transparent
# objname = 'Cube.001'  # whatever name
# obj = bpy.data.objects[objname]
# obj.select = True
# bpy.context.scene.objects.active = obj
#
# # add the material and set settings
#
# obj.data.materials.append(whitetex)
# print(whitetex)
#
# # if a material color is  desired, set using
# obj.color = [1,1,1,1]  # r,g,b,a




import bge
import random



def main():

    cont = bge.logic.getCurrentController()
    own = cont.owner
    #print(own.color[3])
    #own.color = [1,0,0,.1]
    own.color[3] =random.random() # works!!




main()

