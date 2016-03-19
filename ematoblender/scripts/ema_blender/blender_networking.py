__author__ = 'Kristy'

"""
This module describes a protocol for querying the gameserver.
All of the basic commands have functions for them.
Note that before they are executed, the game server must be running.
All the bite-plate recordings etc must have also already been completed, else they will fail.
"""

# functions for communicating with servers in the ema_io module.
import socket
import pickle
import os
import sys
import time

import xml.etree.ElementTree as ET
from collections import deque
from subprocess import Popen

from . import blender_shared_objects as bsh
from ..ema_shared import properties as pps


def setup_socket_to_gameserver(port=0, blocking=False):
    """Setup a persistent socket to the gameserver.
    Assigned to a random port number.
    if not blocking, sets timeout to 0.2 seconds.
    """
    BLENDERHOST, BLENDERPORT = pps.gameserver_host, pps.gameserver_port if port == 0 else port

    # Create a socket (SOCK_DGRAM is a UDP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0 if not blocking else 0.2)
    sock.bind((BLENDERHOST, BLENDERPORT))  # picks a random port if 0
    return sock


def close_socket(s):
    """Close the socket"""
    if type(s) == socket:
        s.close()


def run_game_server(s, user_args=None):
    """Check the connection controlled by the run_client script. This may already be available from BPY in edit mode.
    user_arguments are appended to the standard command line arguments."""
    # open the run_client script, does its thing independently (if connection existing from bpy then leave open)

    send_to_gameserver(s, mode='TEST_ALIVE')
    reply = recv_from_gameserver(s)
    print('game servers reply is', reply)

    if not reply:  # server does not respond to this simple query, is obviously not running
        print('\nWARNING: GAME SERVER IS NOT INITIALISED ALTHOUGH IT IS REQUIRED BY BLENDER; ABORTING THIS SCRIPT.\n\n')
        raise ConnectionRefusedError

    if False:  # old
        if bsh.gameserver is None:  #if connection is not None and replies is not None:
            print("Initialising the game server!")

            if type(user_args) is not list:
                user_args = []

            scriptpath = os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__), '../ema_io/ema_gameserver/gameserver.py')))
            maindir = os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__), '../../')))

            # runs the client intermediary in the ematoblender directory, transfers current pythonpath
            gameserver = Popen(['python', scriptpath] + pps.game_server_cl_args + user_args, cwd=maindir, env=dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path)))  # start the script
            bsh.gameserver = gameserver
            print('Gameserver initialised.')
            return gameserver

        else:
            print('Game server is already running.')


# unused function (deprecated)
def prenetworking_run_gameserver(func):
    """Make sure there is a bsh.gameserver process running before attempting networking."""
    def prenetworking_wrapper(*args, **kwargs):
        print('CHECKING GAMESERVER IS ALIVE BEFORE DOING:', func)
        #if bsh.gameserver is None:
            #run_game_server(bsh.gs_soc, user_args=pps.game_server_prerecorded_args)
            #time.sleep(2)  # give the server 2 seconds to initialise before sending the request
        return func(*args, **kwargs)
    return prenetworking_wrapper


# unused function (deprecated)
def prenetworking_run_gameserver_make_bp_rec(func):
    """Make sure there is a bsh.gameserver process running before attempting networking.
    Record a new biteplate recording in this."""
    def prenetworking_wrapper(*args, **kwargs):
        print('Initialising the gameserver with Popen before doing', func)
        if bsh.gameserver is not None:
            bsh.gameserver.kill()
            bsh.gameserver = None
        run_game_server(bsh.gs_soc_blocking)
        return func(*args, **kwargs)
    return prenetworking_wrapper


def postnetworking_kill_gameserver(func):
    """Kill the bsh.gameserver process after this function."""
    def postnetworking_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print('About to kill networking!')
        if bsh.gameserver is not None:
            bsh.gameserver.kill()
            bsh.gameserver = None
        return result
    return postnetworking_wrapper


def wait_til_recv(s):
    """Wait for a response from a socket s."""
    temp_socket = False
    if type(s) != socket.socket:
        # create a socket to receive from if one doesn't exist
        print('Socket does not yet exist')
        raise TypeError
        #s = setup_socket_to_gameserver(blocking=True)
        #temp_socket = True

    received = b''
    while len(received) < 1:
        try:
            data, addr = s.recvfrom(32768)
            received += data
        except socket.timeout:
            print('Timeout error occurred, sleeping')
            time.sleep(0.1)
        except BlockingIOError:
            print('Non-blocking socket failed initially.')
            time.sleep(0.1)
            # no sleep, as should pass on immediately.

    print('Reply to Blender socket is:', received)

    try:
        data = pickle.loads(received)
    except TypeError:
        return

    except pickle.UnpicklingError as e:
        print('Received data could not be unpickled', e)
        data = False

    #if temp_socket:
    #    s.close()

    # return the data sent, else False if no data
    return data


def recv_from_gameserver(s):
    """
    With a static large buffer, receive data from the gameserver over the nominated socket.
    Presumed to be run on a non-blocking socket, no built-in waiting mechanism.
    Returns the message if received,
    If there is an unpickling error than an empty string,
    If there is nothing received then nothing.
    """

    #temp_socket = False
    print('Performing a large-buffer receive on socket', s)

    if type(s) is not socket.socket:  # create a socket to receive from if one doesn't exist
        print('Problem: socket doesn\'t exit!')
        raise TypeError

    received = b''
    try:
        received = s.recv(32768)
        # if temp_socket:
        #     s.close()

    except socket.timeout:
        print('Socket timed out, skipping the rest.')
        return

    except BlockingIOError as e:
        print('BlockingIOError - no reply in this loop from gameserver.', e)
        return

    except TimeoutError as e:
        print('Receiver timed out!')
        return

    print('Blender UDP socket received:', received)

    if len(received) == 0:
        return

    try:
        data = pickle.loads(received)
    except TypeError as e:
        print('INVALID DATA RECEIVED FOR UNPICKLING', e)
        return b''

    except pickle.UnpicklingError as e:
        print('Received data could not be unpickled', e)
        return b''
    # return the data sent, else False if no data

    return data


def recv_to_deque(s):
    """
    Routine to check if there's anything waiting from the gameserver on socket s.
    Add to the deque to handle these later.
    """
    if bsh.gs_answers is None:
        bsh.gs_answers = deque()
    bsh.gs_answers.append(recv_from_gameserver(s))
    return bsh.gs_answers

def send_to_gameserver(s, mode='SINGLE_DF'):
    """Send a message to the gameserver using socket s.
    Use mode as either:
    SINGLE_DF: Move input forward one dataframe, return the latest df.
    START_STREAM: Tell the data server to start streaming.
    STOP_STREAM: Tell the data server to stop streaming.
    STREAM_DF: Return the latest df whilst streaming.
    STREAM_STOP: Tell the data server to stop the streaming, return the last available df.
    PARAMETERS: Get the parameters as an XML element. [These may not be updated to reflect accurate stats, but is essential to check if the streaming source has changed.
    STATUS: Get any OK messages or error messages, simply the last one received from data server.
    KILL_CLIENT: Close the game server"""

    # check the input requested
    if mode not in ['SINGLE_DF', 'STREAM_DF', 'START_STREAM', 'STREAM_STOP', 'PARAMETERS', 'TEST', 'TEST_ALIVE','KILL_CLIENT', 'STATUS', 'CAM_TRANS']:
        print('Mode "{}" cannot be received from the server.'.format(mode))
        return None
    try:
        s.sendto(bytes(mode, encoding='ASCII'), (pps.gameserver_host, pps.gameserver_port))

    except AttributeError as e:
        # make the socket if it doesn't exist
        t = setup_socket_to_gameserver()
        t.sendto(bytes(mode, encoding='ASCII'), (pps.gameserver_host, pps.gameserver_port))
        close_socket(t)

    # return False if fails
    except socket.error as e:
        print('MESSAGE "{}" COULD NOT BE SENT:'.format(mode), e)
        return False

    else:
        return True


#@prenetworking_run_gameserver
def get_n_seconds_streaming(n=5, skip_seconds=0.1):
    """Get streaming frames for n seconds. Return them as a list of dataframes."""
    output = []
    if bsh.gs_soc_blocking is None: bsh.gs_soc_blocking = setup_socket_to_gameserver(blocking=True)
    send_to_gameserver(bsh.gs_soc_blocking, mode='START_STREAM')
    starttime = time.time()
    while time.time() < starttime + n:
        send_to_gameserver(bsh.gs_soc_blocking, mode='STREAM_DF')
        df = recv_from_gameserver(bsh.gs_soc_blocking)
        output.append(df)
        time.sleep(skip_seconds)
    send_to_gameserver(bsh.gs_soc_blocking,mode='STREAM_STOP')
    return output


#@prenetworking_run_gameserver
def get_parameters_and_one_df():
    if bsh.gs_soc_blocking is None: bsh.gs_soc_blocking = setup_socket_to_gameserver(blocking=True)
    # get the parameter string
    from .blender_shared_objects import streaming_xml
    send_to_gameserver(bsh.gs_soc_blocking, mode='PARAMETERS')
    param_result = wait_til_recv(bsh.gs_soc_blocking)
    streaming_xml = ET.fromstring(param_result)
    extract_from_xml(streaming_xml)
    print('CURRENT PARAMETERS ARE:', streaming_xml)
    # get a single dataframe
    send_to_gameserver(bsh.gs_soc_blocking, mode='SINGLE_DF')
    df = wait_til_recv(bsh.gs_soc_blocking)
    return streaming_xml, df


#@postnetworking_kill_gameserver
#@prenetworking_run_gameserver_make_bp_rec
def get_live_setup_data():
    if bsh.gs_soc_blocking is None: bsh.gs_soc_blocking = setup_socket_to_gameserver(blocking=True)
    send_to_gameserver(bsh.gs_soc_blocking, mode='TEST')
    testresult = wait_til_recv(bsh.gs_soc_blocking)
    print('SETUP TEST RESULT WAS:', testresult)
    params, df = get_parameters_and_one_df()
    return params, df


#@postnetworking_kill_gameserver
#@prenetworking_run_gameserver
def get_test_response(sock):
    send_to_gameserver(sock, mode='TEST')
    testresult = wait_til_recv(sock)
    print('TEST RESULT WAS:', testresult)
    return testresult


#@postnetworking_kill_gameserver
#@prenetworking_run_gameserver
def get_one_df():
    send_to_gameserver(bsh.gs_soc_nonblocking, mode='SINGLE_DF')
    df = recv_from_gameserver(bsh.gs_soc_nonblocking)
    return df

#unused
def bge_only_start_stream():
    from ematoblender.scripts.ema_blender.ema_bge.bge_menus_overlays import bge_display_status_text
    send_to_gameserver(bsh.gs_soc_nonblocking, mode='START_STREAM')
    reply1 = recv_from_gameserver(bsh.gs_soc_nonblocking)
    send_to_gameserver(bsh.gs_soc_nonblocking, mode='STATUS')
    reply2 = recv_from_gameserver(bsh.gs_soc_nonblocking)
    bge_display_status_text(newtext=reply2)

#unused
def bge_only_stop_stream():
    from .ema_bge.bge_menus_overlays import bge_display_status_text
    send_to_gameserver(bsh.gs_soc_nonblocking, mode='STREAM_STOP')
    reply1 = recv_from_gameserver(bsh.gs_soc_nonblocking)
    send_to_gameserver(bsh.gs_soc_nonblocking, mode='STATUS')
    reply2 = recv_from_gameserver(bsh.gs_soc_nonblocking)
    bge_display_status_text(newtext=reply2)

#unused
def get_cam_inversion():
    print('doing bn.getcaminversion')
    send_to_gameserver(bsh.gs_soc_blocking, mode='CAM_TRANS')
    matrix_as_list, coords = recv_from_gameserver(bsh.gs_soc_blocking)
    return matrix_as_list, coords


def extract_from_xml(xmltree):
    """Extract the absolute paths for mocap file, sound file and video file from XML is available."""
    if type(xmltree) == str:
        try:
            xmltree = ET.fromstring(xmltree)
        except:
            print('item {} of type {} could not be parsed as XML'.format(xmltree,  type(xmltree)))
    bsh.mocappath = xmltree.find("General").find("Multimodal").find("MocapFileAbsLoc").text
    bsh.soundpath = xmltree.find("General").find("Multimodal").find("AudioFileAbsLoc").text
    bsh.vidpath = xmltree.find("General").find("Multimodal").find("VideoFileAbsLoc").text
    return bsh.mocappath, bsh.soundpath, bsh.vidpath


if __name__=="__main__":
    #run_game_server(user_args=pps.game_server_cl_args) # does head-correction, prepares gameserver
    s = setup_socket_to_gameserver()
    send_to_gameserver(s, mode='SINGLE_DF') # get one dataframe
    mydf = recv_from_gameserver(s)
    send_to_gameserver(s, mode="START_STREAM")
    mydf = recv_from_gameserver(s)
    time.sleep(5)
    send_to_gameserver(s, mode="STREAM_STOP")
    mydf = recv_from_gameserver(s)
    print('TEST SINGLE DF RETURNS:', mydf)
    print(mydf.give_coils()[0].__dir__())
    print(mydf.give_coils()[0].ref_loc, mydf.give_coils()[0].bp_corr_loc)
    send_to_gameserver(s) # get one dataframe
    mydf = recv_from_gameserver(s)
    print(mydf.give_coils()[0].ref_loc, mydf.give_coils()[0].bp_corr_loc)