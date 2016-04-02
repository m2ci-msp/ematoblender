# -*- coding: utf-8 -*-
__author__ = 'Kristy'

"""
Script that runs at high-frequency during game execution (uses BGE).
Controls:
 - get coil location; display them there
 - update any armatures that use IK to coils
 - update any inferred coil locations based on actual coil locations
 - draw any necessary lines
 - play any accompanying sounds
 - update camera positions
 - respond to keypresses.

This script is run based on an 'Always' sensor at a high frequency,
and does not use threading due to Blender requirements
"""

# Blender modules
import bge         # game engine functionality
import mathutils
import time
import sys, os

# For I/O with the server

# My scripts for networking with the EMA (file)
# client script that connects to EMA server
from .. import blender_networking as bn
from ..blender_networking import send_to_gameserver

# external modules relevant to bge, stored separately for convenience
# below illustrates absolute and relative imports of same directory
from . import bge_standard_gamefns as gf
from . import bge_camera_control as cc
from . import bge_menus_overlays as mo
from . import bge_update_armature as ua
from . import bge_move_objects as mv
from . import bge_play_audio as pa
from . import bge_splines_lines as sl
from . import bge_static_video as vid

from .. import coil_info as ci
from .. import blender_shared_objects as bsh
from .. import coord_transforms as ct
from ...ema_shared import properties as pps

from scripts.ema_io.rtc3d_parser import DataFrame
from ...ema_shared.miscellanous import reload_modules_for_testing
import xml.etree.ElementTree as ET

##### global variables #####

first_exec = True  # whether setting up objects or editing them
streaming = False
prev_streaming_state = False

head_movement = False
show_webcam = False  # TODO: Does not work due to specific settings on my system.
show_ultrasound = False

menu_overlaying = False
ticks_since_stream_toggle = 5  # streaming repetitions if looping, starting value
key_pace = 20  # number of logic ticks before registering a second keypress

from queue import deque
bsh.gs_answers = deque()  # store responses from gameserver (deque to can restrict length if req'd)
# persistent socket that connects to the gameserver


gs_soc_blocking = bn.setup_socket_to_gameserver(blocking=True)
# create and make a test call to the game server socket
print('Confirming connection to gameserver...')
bn.send_to_gameserver(gs_soc_blocking, mode='TEST_ALIVE')

# setup the non-blocking socket
gs_soc_nonblocking = bn.setup_socket_to_gameserver()
gs_soc_nonblocking.settimeout(0)
print('NB socket created', gs_soc_nonblocking)
bn.send_to_gameserver(gs_soc_nonblocking, mode='PARAMETERS')
time.sleep(0.2)
paramstring = bn.recv_from_gameserver(gs_soc_nonblocking)
parameters = ET.fromstring(paramstring)


def main():
    """"
    Modal game function, executes frequently, every nth logic tick.
    """
    print('Running bge_emareadin.')
    global first_exec
    if first_exec:
        first_exec = False
        setup()
    else:
        update()


def setup():
    """The first execution of the game script.
     - Reloads the game engine modules for changes to code if development_mode True
     - Divides the viewport if several cameras configured
     - Connect to the game server with a UDP socket and make a test call
     - Collect the parameter string for the data being streamed
    """
    sys.stdout = open(os.devnull, "w")
    print('Executing initial game setup.')

    # whilst in development, reload cached modules that may change
    if pps.development_mode:
        reload_modules_for_testing(pps, pa, cc, bn, vid, ci, mv, ct)

    # set up the display parameters to divide the viewport if needed
    try:
        cc.use_viewports()
    except TypeError:
        print('One or more cameras ignored due to non-matching name.')
    print('Camera setup completed.')
    global parameters
    param_result = wait_til_recv(sock)
    parameters = ET.fromstring(param_result)
    bn.send_to_gameserver(gs_soc_blocking, mode='TEST_ALIVE')
    time.sleep(0.2)  # wait for game server to reply before making a query
    reply = bn.simple_recv(gs_soc_blocking)


    bn.send_to_gameserver(gs_soc_nonblocking, mode='TEST_ALIVE')
    time.sleep(0.2)  # wait for game server to reply before making a query
    reply = bn.recv_to_deque(gs_soc_nonblocking)

    # close the game if gameserver not available
    if not len(reply) > 0:
        print('Gameserver cannot be accessed. Closing game.')
        shutdown(stopgame=True)

    print('Game server started.')

    # Collect the parameter string from the data being streamed
    bn.send_to_gameserver(gs_soc_blocking, mode='PARAMETERS')
    time.sleep(0.3)  # wait for a server response
    params = bn.recv_from_gameserver(gs_soc_blocking)
    print('\n\nData parameters received from GS are:', params)
    bn.extract_from_xml(params) # used to update the video and sound file locations in bsh

    # setup video if necessary

    print('Initial game setup completed.')


def update():
    """
    Update method in the game loop.
    Executed once every nth logic tick, check for key/button events.
    Firstly update rigid body locations, then armatures, then meshes.
    """
    print(gs_soc_nonblocking, 'is the NB socket')

    global streaming, prev_streaming_state, ticks_since_stream_toggle, \
        menu_overlaying, head_movement,  \
        gs_soc_blocking, gs_soc_nonblocking
    print("\n\n Executing modal - streaming is {}".format(str(streaming)))

    scn, objs, cont, own, acts = gf.get_scene_info()  # get info about the current state of the scene
    keys = gf.catch_keypresses()   # check keyboard interactions

    ################## MAKE REQUESTS TO UDP SERVER #############

    if streaming:
        print('Game loop sending','STREAM_DF')
        send_to_gameserver(gs_soc_nonblocking, mode='STREAM_DF')

    if keys['dkey'] and not streaming:  # d key for moving one-frame at a time
        print('Game loop sending','SINGLE_DF')
        send_to_gameserver(gs_soc_nonblocking, mode='SINGLE_DF')

    if head_movement:
        print('Game loop sending','CAM_TRANS')
        send_to_gameserver(gs_soc_nonblocking, mode='CAM_TRANS')

    ##################### OTHER ACTIONS RESPONDING TO KEYS/BUTTONS ######

    if keys['esckey']:  # quit
        shutdown()

    if keys['rkey']:  # re-perform the scene setup, for changing static file
        global first_exec
        first_exec = True
        shutdown(stopgame=False)
        return

    if keys['spacekey']:  # suspend scene and show menu
        toggle_popup_menu()

    # s key to toggle streaming: toggle flag, tell server to send/stop data
    if keys['skey']:
        print("You pushed S, toggling streaming")
        if ticks_since_stream_toggle > key_pace:  # only toggle if more than 5 logic ticks, preventing toggling too quickly
            ticks_since_stream_toggle = 0
            streaming = not streaming
            if streaming:
                send_to_gameserver(gs_soc_nonblocking, mode='START_STREAM')
                pa.sound_setup()

            else:
                send_to_gameserver(gs_soc_nonblocking, mode='STREAM_STOP')
                pa.pause_sound()
    ticks_since_stream_toggle += 1

    ################# UPDATE VIDEOS BY CHANGING MATERIALS ######################

    if show_webcam:
        mo.bge_update_webcam()

    if show_ultrasound:
        # TODO: Get video location like sound location, not hard-coded in properties file
        vid.bge_update_videoplane(0, pps.video_override)

    ################ COLLECT AND PARSE NEW DATA FROM UDP SOCKET ####################

    print('Attempting to collect responses from gameserver into deque.')
    bn.recv_to_deque(gs_soc_nonblocking)  # update the bsh.gs_answers deque
    print('Response deque has length ', len(bsh.gs_answers))
    for m in bsh.gs_answers:      # parse out the deque, clear it
        if type(m) == DataFrame:
            # choose if multiple DataFrames, choose that with greatest timestamp
            if bsh.latest_df is None or m.give_timestamp_secs() >= bsh.latest_df.give_timestamp_secs():
                bsh.latest_df = m
            print(m.give_coils()[0].__dict__)
        elif type(m) == tuple:
            bsh.head_inversion = m
        elif type(m) == str:
            bsh.latest_status = m
    bsh.gs_answers.clear()


    ############ UPDATE FROM THE LATEST DATA ###########

    # camera position
    print('camera controls '+'up: {}, down:{}, left:{}, right:{}'.format(keys['upkey'], keys['downkey'],
                                                                         keys['leftkey'], keys['rightkey']))
    cc.bge_circular_camera_control(keys)  # includes head movement correction

    # coil position
    if bsh.latest_df is not None:
        mv.bge_update_from_df(objs, bsh.latest_df, showall=True)
        mv.bge_show_inferred_coils_in_position()

        timestamp = bsh.latest_df.give_timestamp_secs()
        mo.bge_display_status_text(newtext="Streaming time:"+str(round(float(timestamp), 2)))
        bsh.latest_df = None

        if streaming:
            pa.sound_update(timestamp=timestamp)

    elif bsh.latest_status is not None:
        mo.bge_display_status_text(newtext=bsh.latest_status)
        bsh.latest_status = None

    ############ UPDATE OBJECTS MANUALLY ##############
    # move the tongue armature based on the new coil position
    if scn.objects.get(pps.tongue_armature_name, False):
        ct.bge_move_tongue_to_coils()

    ############ UPDATE ARMATURES ##########

    print('pre-updating bones')
    ua.update_all_bones()  # ensure armatures listed in properties are moved to new locations based on their IK/changed positions (so child mesh deforms)
    #ua.update_tongue_surface()
    #ua.update_these_bones(armature_name='LipArmature')


    ############ UPDATE MESHES #############
    pass  # to be used if vertices are manually updated.

    # ############ UPDATE LINES ############
    if pps.show_debugging_lines and len(pps.display_cameras) <= 1:
        sl.draw_spline_between_names("TB", "TM", "TT")
        sl.draw_lines_through_names_locs_inds("LL", "SL", "UL", color=(1, 0, 0))  # red
        sl.draw_lines_through_names_locs_inds("LL", "UL", color=(1, 0, 1))  # magenta?
        sl.draw_lines_through_names_locs_inds("TT", "TB", color=(0, 0, 1))  # blue
        #sl.draw_lines_through_names_locs_inds(2, 3, color=(0, 1, 1))
        #sl.draw_lines_through_names_locs_inds(4, 5, color=(1, 0, 1))
        sl.draw_lines_through_names_locs_inds("MR", "FT", "ML", "MR", color=(0, 1, 0))  # green

    return None


def shutdown(stopgame=True):
    """
    End the game.
    If stopgame is False, then the game is reinitialised, re-reading parameters for a new datafile.
    """

    global streaming
    if streaming:
        send_to_gameserver(gs_soc_nonblocking, mode='STREAM_STOP')
        streaming = False

    # end sound/video
    pa.sound_shutdown()

    # close the client server
    if bsh.gameserver is not None:
        print('Game loop sending to game server', "KILL_CLIENT")
        bn.send_to_gameserver(gs_soc_blocking, mode="KILL_CLIENT")
        bsh.gameserver.kill()
        bsh.gameserver = None
    # TODO: Contact the gameserver and clear the queue of streamed frames

    # close the socket to the gameserver
    bn.close_socket(gs_soc_nonblocking)
    bn.close_socket(gs_soc_blocking)

    if stopgame:
        print("Now shutting down the game module")
        bge.logic.endGame()


def toggle_popup_menu():
    """
    Toggle the appearance of the popup menu.
    """
    global menu_overlaying
    global streaming
    print('TOGGLING POPUP MENU')
    menu_overlaying = not menu_overlaying
    old_ss = streaming

    # show the menu
    if not menu_overlaying:
        # stop streaming
        if old_ss:
            streaming = False
            bn.bge_only_stop_stream()
            pa.pause_sound()
        mo.show_menu_overlay()
        print('game loop menu added')

    # hide the menu, restart streaming if needed
    else:
        streaming = old_ss
        if streaming:
            bn.bge_only_start_stream()
            pa.sound_setup()
        mo.hide_menu_overlay()
        print('game loop menu hidden')
