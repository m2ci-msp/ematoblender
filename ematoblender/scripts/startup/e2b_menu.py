__author__ = 'Kristy'


"""
Menu to do useful ematoblender things in blender, as a panel that appears in the Properties menu.
This is in the 3D view.

Has the following roles:
1. [Initial setup] (everything else is blacked out if this has not been pressed)
 Setup the gamemaster
 Delete the cube,
 Setup workspace (may need to change GM decorator for this),
 set ambient colours,
  set texture view
  all objects are backface-culled

2. [Setup coil objects] Once or more - Make/collect the objects, get their roles, recolour them

3. [Setup cameras] If again reloads (or adds each time? With location options?)

4. [Load menus and graphics] If again reloads, videoplane too

5. [Load external model] Launches file chooser, used to load the head, tongue mesh

6. [Connect mesh and coils] Parents the model/coils appropriately

7. [Load tongue weight model] Load the Datamodel in JSON

8. [Position Palate] Grab palate object

9. [Get dataframe] Move the coils based on one DATAFRAME

TODO: Firstly define all the functions I want to run as bpy operators.
Then they can be run in the GUI from a button

"""

import bpy


class EmaReadInPanel(bpy.types.Panel):
    """Panel in the properties menu that controls the Ematoblender functions needed in bpy."""
    bl_label = "E2B Build Scene"
    bl_idname = "E2B_SCENE_CONSTRUCT"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Load the game logic:")
        row = layout.row()
        row.operator("object.add_gamemaster")

        layout.label(text="Spawn scene objects:") # Spawn basic coils
        row = layout.row()
        row.operator("object.add_coil_objects")
        layout.label(text="Load basic game assets:")
        layout.label(text="Load the rigged face from blend:")
        layout.label(text="Load the tongue and palate models (popup):")


        layout.label(text="Set positions:") # buttons for streaming data, moving face,
        layout.label(text="Fix relationships:") # parent everything

        layout.label(text='Palate trace options')

        layout.label(text='Play the game')



        layout.label(text="Spawn scene objects:")

        layout.label(text="Spawn scene objects:")
        row = layout.row()
        row.operator("render.render") # TODO: load game assets (menus, lamps etc)

        row = layout.row()
        row.operator("render.render") # TODO: Load the face mesh



        layout.label(text="Load assets")

        row = layout.row()
        row.operator("object.transparent_material")

        layout.label(text="Palate Trace")

        row = layout.row()
        row.operator("view3d.palate_trace")

        row = layout.row()
        row.operator("view3d.palate_mesh")

        layout.label(text="Position/connect objects")

        layout.label(text="Get mocap data")

        row = layout.row()
        row.operator("object.empty_connector")


def register():
    bpy.utils.register_class(EmaReadInPanel)


def unregister():
    bpy.utils.unregister_class(EmaReadInPanel)

if __name__=="__main__":
    register()

