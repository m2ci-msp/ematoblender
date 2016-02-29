import bpy

def main():
    for obj in bpy.context.scene.objects:
        obj.select = ( obj.name.startswith("Cube."))
    bpy.ops.object.delete()

if __name__=="__main__":
    main()