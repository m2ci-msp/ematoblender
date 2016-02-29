__author__ = 'Kristy'

# working directory
abspath_to_repo = 'C:/Users/Kristy/Documents/GitHub/repos/ematoblender'

# networking

gameserver_port = 9995
gameserver_host = 'localhost'

waveserver_port = 9007  # TODO: Change to 3030 if using NDI WAVE
waveserver_host = 'localhost'  # on RUG machine '145.97.132.29' or similar

# if using the server switcher, where is the file list stored?
mocap_list_of_files = './data/switcher_file_list.txt'

# filename we are streaming from
streaming_source = None  # this is for reference only

# filename for the simultaneous sound file
sound_override = None  # if absolute path this will actually be used to import the sound
video_override = 'F:\\PostureData\\VP01_uti.mp4'

# if performing RT streaming, where to record TSV and WAV relative to top of repository
tsv_output_dir = './output'
wav_output_dir = './output'
wave_writing_chunk_size = 1024

# biteplate storage
biteplate_cs_storage = './temp/biteplate_in_refspace.p'
refspace_cs_storage = './temp/refspace_in_global.p'

# blender game setting

# logic tick frequency that the main script should execute at
'''
Note: hifreq_sensor_skips works well at val=10 for debugging,
but must be val=0 for debugging lines to appear smoothly and not disappear.
Value of 5 works well with the UDP configuration.
'''
hifreq_sensor_skips = 5
lowfreq_sensor_skips = 100

# location of the bpy/game engine script relative to the .blend file. Must be a nested directory
bpy_script_path = 'scripts.ema_blender.ema_bpy.bpy_emareadin.main'
bge_script_path = 'scripts.ema_blender.ema_bge.bge_emareadin.main'

# relative location of the JSON file with the sensor information
json_loc = './sensor_info.json'


# location of menu scenes (relative to current .blend)

# location of status/webcam scene for overlay
rel_loc_of_statusbar_dot_blend = './text_scene' # "./blender_objects"
statusbar_dot_blend = 'textscene_for_survey.blend' #"text_video_scene_latest_2_nov_development.blend"  # TODO: Change back
path_to_statusbar_in_dot_blend = "Scene"
name_of_statusbar_object = "TextScene"

# name of an avatar to demonstrate rotation if available
rotation_avatar = 'Avatar'

# location of popup menu scene for occasional overlay
rel_loc_of_popup_dot_blend = "./blender_objects"
popup_dot_blend = "popup_menu_latest.blend"
path_to_popup_in_dot_blend = "Scene"
name_of_popup_object = "PopupMenu"

# location of video to be displayed if manual (abs)
ultrasound_video_loc = 'F:\\PostureData\\VP01_uti.mp4'
ultrasound_placeholder_image_loc = './images/black.jpg'  # relative if relative to WD, abs if elsewhere


'''Assets made up of multiple Blender objects, such as a lip rig with both meshes, armatures and empties,
can best be imported by copying the entire scene using the wm.append commands,
then moving them into the main scene as appropriate.'''

# location of tongue object scene for import
rel_loc_of_tongue_dot_blend = "./blender_objects"
tongue_dot_blend = "blue_tongue_rig_latest.blend"  # TODO: Make
path_to_tongue_in_dot_blend = "Scene"
name_of_tongue_object = "Scene"  # presumes object is in default scene, called 'Scene'
name_of_tongue_armature = 'tongue_arm'  # name of the tongue armature that is changed to fit a spline

# names of objects on tongue that need to be connected to data input
# the value is a string that is the name of the empty object.
# it is connected to a coil empty, as defined by other properties.
import scripts.ema_blender.blender_shared_objects as bsh
TT_empty_name = bsh.tongue_top_empty_name(1)
TM_empty_name = bsh.tongue_top_empty_name(5)
TB_empty_name = bsh.tongue_top_empty_name(10)

tonguemesh_name = 'tonguemesh'
cube_scale = 1

# tongue armature
deformers = 2  # the number of bones between each coil on the tongue #TODO: Trying to phase out, for smaller many-boned tongue


# location of lip object for import
rel_loc_of_lip_dot_blend = "./blender_objects"
lip_dot_blend = "lip_rig_latest.blend"
path_to_lip_in_dot_blend = "Scene"
name_of_lip_object = "Scene"  # presumes object is in default scene, called 'Scene'
name_of_lip_armature = 'LipArmature'

# names of objects on lips that need to be connected to data input
SL_empty_name_left = 'SL_L'
SL_empty_name_right = 'SL_R'
UL_empty_name = 'UL_Empty'
LL_empty_name = 'LL_Empty'

# show debugging lines
show_debugging_lines = True


# choose to send things to wave, like requesting frequency of streaming etc
game_server_cl_args = ["--smoothframes", "5"]  # none while testing pre-recorded data   #[ '--headcorrect', '-print', '-wav',] # off whilst testing playing video
game_server_prerecorded_args = ['-bpcs', './temp/biteplate_in_refspace.p', '-rscs', './temp/refspace_in_global.p']
# head-correction parameters
head_correction_time = None
head_correction_exclude_first_ms = 0


# new tongue top stuff
tongue_armature_name = 'MSArmature'
tongue_intervals = 9

# cameras to give viewports to
display_cameras = ['FCamera', 'MSCamera']  # missing CircularCamera #  ]#] # TODO: DrawLine does not respond to this, so cannot use debuggin with 2 cams.

development_mode = True

global_coordinate_transform = {'flip_xyz': (False, True, True),
                               'axis_order': ('X', 'Z', 'Y'),
                               }
# note : correct global_coordinate_transform for Martijn's VENI data is:
# {'flip_xyz': (False, True, True), 'axis_order': ('X', 'Z', 'Y'), }


game_background_color = (0.07, 0.07, 0.07) # light grey, best visibility
game_contrast_color = (0.5, 0.5, 0.5) # medium grey, pleasant contrast
