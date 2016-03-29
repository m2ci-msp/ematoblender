__author__ = 'Kristy'
import bpy

from . import bpy_workspace as ws


from ematoblender.scripts.ema_shared import properties as pps
from ematoblender.scripts.ema_shared.miscellanous import get_random_color
from ematoblender.scripts.ema_blender import blender_shared_objects as bsh


@ws.postfn_gamemaster_reset_decorator
@ws.prefn_objectmode_noselection_decorator
def add_game_master():
    """Make the game master object with connected sensors/controllers (controls the bge scripts)."""
    scn, objs, *_ = ws.get_context_info()

    # add a cube due to Blender quirks so there is at least something in the scene
    bpy.ops.mesh.primitive_cube_add()
    # remove all existing cubes (eg stuff added on startup, or stuff added previously)
    for obj in objs:
        obj.select = (obj.name.startswith("Cube") or obj.name.startswith("GameMaster"))
        if obj.select:
            bpy.ops.object.delete()

    # add an empty mesh to be the Gamemaster
    bpy.ops.object.add(radius=0.0, type='MESH')
    gm_obj = bpy.context.object
    gm_obj.name = 'GameMaster'
    #gm_obj.layers = [True] * 20

    # add Always sensor to the Gamemaster to execute the main game script at frequency (time information)
    bpy.ops.logic.sensor_add(type='ALWAYS', name='HIFREQ', object='GameMaster')
    hifreq_sensor = bpy.data.objects['GameMaster'].game.sensors['HIFREQ']
    hifreq_sensor.use_tap, hifreq_sensor.use_pulse_false_level, hifreq_sensor.use_pulse_true_level = False, False, True

    # set sensor frequency, handling changes in field name between v. 2.74 and 2.75
    if hasattr(hifreq_sensor, 'frequency'):
        hifreq_sensor.frequency = pps.hifreq_sensor_skips
    elif hasattr(hifreq_sensor, 'skippedTicks'):
        hifreq_sensor.skippedTicks = pps.hifreq_sensor_skips
    elif hasattr(hifreq_sensor, 'tick_skip'):
        hifreq_sensor.tick_skip = pps.hifreq_sensor_skips

    # set a Python controller to execute the game engine script (script information)
    bpy.ops.logic.controller_add(type='PYTHON', name='GameScript', object='GameMaster')
    hifreq_python_controller = bpy.context.scene.objects['GameMaster'].game.controllers['GameScript']
    hifreq_python_controller.mode = 'MODULE'

    # link the game script to the hifreq_python_controller
    hifreq_python_controller.module = pps.bge_script_path  # should look like scripts.ema_bge.bge_emareadin.main

    # link the sensor and the controller
    hifreq_sensor.link(hifreq_python_controller)

    # set an AND controller to the hifreq game sensor
    bpy.ops.logic.controller_add(type='LOGIC_AND', name='HFAND', object='GameMaster')
    hifreq_and_controller = bpy.context.scene.objects['GameMaster'].game.controllers['HFAND']
    hifreq_sensor.link(hifreq_and_controller)

    # add an actuator to play sound (sound added later)
    bpy.ops.logic.actuator_add(type='SOUND', name='SoundAct')
    sound_actuator = bpy.context.scene.objects['GameMaster'].game.actuators['SoundAct']
    sound_actuator.mode = 'PLAYSTOP'
    # note: DO NOT LINK THIS ACTUATOR TO ANY ALWAYS CONTROLLERS, ELSE THE SCRIPT FUNCTIONALITY IS OVERRIDDEN

    add_mouse_sensor()


def setup_sensor_cont_for_act(obj, act):
    """For the given actuator, set up a hifrequency always sensor and AND controller."""

    # add the sensor
    bpy.ops.logic.sensor_add(type='ALWAYS', name='HIFREQ', object=obj.name)
    sens = obj.game.sensors['HIFREQ']
    sens.use_tap, sens.use_pulse_false_level, sens.use_pulse_true_level = True, False, True

    # add the controller
    bpy.ops.logic.controller_add(type='LOGIC_AND', name='HFAND', object=obj.name)
    cont = obj.game.controllers['HFAND']

    # link the sensor and controller
    sens.link(cont)

    # link the controller and the actuator
    act.link(cont)


def add_mouse_sensor():
    bpy.ops.logic.sensor_add(type='MOUSE', name='MouseSensor')
    mouse_sensor = bpy.context.scene.objects['GameMaster'].game.sensors['MouseSensor']
    hifreq_and_controller = bpy.context.scene.objects['GameMaster'].game.controllers['HFAND']
    mouse_sensor.link(hifreq_and_controller)


@ws.prefn_gamemaster_reset_decorator
@ws.postfn_gamemaster_reset_decorator
def spawn_hidden_coils(naming_rule, n=16,):
    """Make lots (n) of coil Empty objects that can be called up to control the tongue's bones or other bones.
    N should be at least the number of sensors available on the EMA machine/in the data.
    This also makes a coloured cube which becomes the parent of the empty.
    The cubes can become transparent using obj.color and changing the alpha.
    :param naming_rule: a lambda expression that takes an integer and returns a string (name of the cube object)
    """

    print('SPAWNING {} ICOSPHERE + EMPTY COIL OBJECTS WITH NAMING RULE {}'.format(n, naming_rule))

    scn = bpy.context.scene
    whitetex = create_transparent_texture()

    for i in range(n):
        # Create the empty for the coil objects
        empname = 'CoilEmpty{}'.format(str(i).zfill(2))
        cob = add_cube_parented_to_empty(scn, empname, naming_rule(i), whitetex)
        bsh.all_ema_meshes.append((i, cob))
    return


def spawn_inferred_coil(name, rule, *ruleargs, texture=None):
    """
    Make and return one cube+empty object, according to the naming rule.
    Append the cube object to the bsh.ema_inferred_meshes list.
    :param naming_rule: a lambda expression that takes an integer and returns a string (name of the cube object)
    :param rule: fn taking the cubeobj as an argument that sets the appropriate location.
    :return: the cube that was created
    """
    scn = bpy.context.scene
    cubtex = create_transparent_texture() if texture is None else texture
    empname = 'InferredEmpty_'+name
    cob = add_cube_parented_to_empty(scn, empname, name, cubtex, hidden=False)
    bsh.ema_inferred_meshes.append((0, cob, name, rule, ruleargs))
    return cob


def reload_inferred_coil(name, rule, *ruleargs):
    """
    Used to reload spawned objects from a saved riged scene.
    Inferred objects saved in bsh.ema_inferred_meshes are lost on restart.
    """
    import bpy
    import scripts.ema_blender.blender_shared_objects as bsh
    scn = bpy.context.scene
    cob = scn.objects.get(name, False)
    if cob:
        bsh.ema_inferred_meshes.append((0, cob, name, rule, ruleargs))


def add_cube_parented_to_empty(scene, emptyname, cubename, texture, hidden=True):
    """Add one empty with name emptyname.
    Add one icosphere with cubename.
    If hidden, hide_render and hide are set to True
    :return : the cube object
    """
    # Create a cone for each coil object
    bpy.ops.mesh.primitive_ico_sphere_add()
    cob = bpy.context.object
    cob.name = cubename
    if hidden:
        cob.hide_render, cob.hide = True, True
    cob.data.materials.append(texture)

    # Put a random colour on each cube to help with identification
    cob.draw_type = 'SOLID'
    cob.color = get_random_color()

    # old approach, doesn't allow transparency of colorsetting
    # cob.data.materials.append(bpy.data.materials.new(name="cubecolor")) cob.data.materials[0].diffuse_color = get_random_color()

    # below is old, use SEEK STEERING actuator rather than parent
    # make the cube the parent of the empty
    # ob.parent = cob
    # ob.select = True

    if emptyname is not None:
        ob = bpy.data.objects.new(emptyname, None)
        ob.show_name = False
        scene.objects.link(ob)
        scene.objects.active = ob

        # TODO: Rewrite with actuator object not context.object
        scene.objects.active = ob
        bpy.ops.logic.actuator_add(type='STEERING', name='Catchup')
        act = ob.game.actuators['Catchup']

        act.target = cob
        act.distance = 0.7
        act.acceleration = 200
        act.turn_speed = 200
        act.velocity = 100
        act.facing = False
        act.lock_z_velocity = False
        act.self_terminated = False

        setup_sensor_cont_for_act(ob, act)

    # return the cube object, ob can be accessed as child
    return cob


def make_all_objs_backface_culled():
    """Apply backface culling option to all objects."""
    for mat in bpy.data.materials:
        mat.game_settings.use_backface_culling = True


def create_transparent_texture():
    """Return a special white material to control transparency using object color"""
    bpy.ops.material.new()
    whitetex = bpy.data.materials[-1]   # bpy.context.active_object.active_material
    whitetex.use_transparency = True
    whitetex.specular_intensity = 0
    whitetex.use_object_color = True
    return whitetex


def recolor_for_roles():
    """Depending on the names of the coils, give them a specific color."""
    blue = (0.0, 0.0, 1.0, 1)
    red = (1.0, 0.0, 0.0, 1)
    yellow = (1.0, 0.74, 0.006, 1)
    green = (0, 1.0, 0, 1)
    color_dict = {'TT': red, 'TM': red, 'TB': red,
                  'LL': green, 'UL': green, 'SL': green,
                  'SL_L':green, 'SL_R': green,
                  'MR': yellow, 'ML': yellow, 'FT': yellow,
                  'LI': blue,
                  }
    for ind, obj, place, *_ in bsh.ema_active_meshes + bsh.ema_biteplate_meshes + \
                               bsh.ema_reference_meshes + bsh.ema_inferred_meshes:
        new_col = color_dict.get(place, False)
        if new_col:
            print('recoloring {} to {}'.format(obj.name, str(new_col)))
            obj.color = new_col
