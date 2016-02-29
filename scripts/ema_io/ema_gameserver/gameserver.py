#!/usr/bin/env python3
__author__ = 'Kristy'

"""
Intermediate server script. This acts as a client (using rtclient.py methods) to communicate with the data server,
but also is initialised as a socketserver so that it can respond to queries by Blender.
This is motivated by the fact that Blender can't handle threading.
It's Blender responses are generally pickled objects, or pickled strings.

This script is generally run independently from the command line,
 though it may be started using Popen, and persists in the background.
 There are plans to later include a GUI for this module instead. #TODO
Because the BlenderGE script will only display the raw data it is given, filtering, headcorr need to happen here.
- filtering: currently just an average over the last n frames
- head correction: based on an initial stream conducted upon startup.
"""

import time
import argparse
import os

# used for serialising and sending
import socketserver
import pickle

# used for saving and manipulating incoming data
import scripts.ema_io.ema_gameserver.wave_recording as wr
import scripts.ema_io.ema_gameserver.data_manipulation as dm
from scripts.ema_io.ema_gameserver.biteplate_headcorr import BitePlane, ReferencePlane

# global properties, coil definitions
from scripts.ema_shared import properties as pps
import scripts.ema_blender.coil_info as ci

# connection objects (this server essentially wraps rtc behaviour)
import scripts.ema_io.ema_gameserver.rtclient as rtc
from scripts.ema_io.rtc3d_parser import DataFrame


def main():
    """
    Initialise the gameserver, getting the TSV and WAV locations to print from from CL arguments,
    or if they are not present from the properties file.
    Start the gameserver, run the biteplate-recording routine.
    Run gameserver.serve_forever()
    """
    # determine the amount of smoothing on streaming dataframes
    # nf = n_frames_smoothed(p_conn, ms=cl_args.smoothms, frames=cl_args.smoothframes)

    # create the file that the streamed data will be printed to
    global printfile_location, wavfile_location
    printfile_location = os.path.normpath(os.path.split(__file__)[0]+cl_args.printdir+os.path.sep+'EMA_')
    wavfile_location = os.path.normpath(os.path.split(__file__)[0]+cl_args.wavdir + os.path.sep+'EMA_')

    print('the printfile location is', printfile_location, 'the wavfile location is', wavfile_location)

    global server
    server = GameServer(pps.gameserver_host, pps.gameserver_port)

    ############### BITEPLANE AND HEAD-CORRECTION HYPOTHESIS ############

    # biteplate recording performed earlier and pickled
    if cl_args.bpcs is not None or cl_args.rscs is not None:
        server.bp_in_rs, server.rp_in_gs = server.gs_load_biteplate_from_file(cl_args.bpcs, cl_args.rscs)

    # perform a biteplate recording and pickle the values
    if cl_args.headcorrect and (server.bp_in_rs is None or server.rp_in_gs is None): # unfulfilled by attempt at loading
        #first_stream=False
        # use the headcorrection static file to determine a rotation matrix that should be applied to all measurements
        server.bp_in_rs, server.rp_in_gs = server.gs_record_biteplate_now()
        print('now values are set', server.bp_in_rs, server.rp_in_gs)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
    print("Server was shutdown")


class GameServer(socketserver.UDPServer):
    """
    Used for smoothing measurements, performing other corrections before coordinates are sent to game loop.
    Game server, inherits from socketserver, handling is defined in MyUDPHandler.
    """

    def __init__(self, HOST, PORT):
        # Create the server, binding to localhost on port 9999
        print('Now creating the gameserver with command line arguments:', cl_args)
        super().__init__((HOST, PORT), MyUDPHandler)

        self.last_cam_trans = None  # storage needed for handler
        self.cam_pos = None

        self.bp_in_rs = None
        self.rp_in_gs = None

        # import or start the client connection
        if rtc.connection is None and rtc.replies is None:
            p_conn, p_repl = rtc.init_connection()  # TODO: retain_last to be given in ms here, change further down.
        else:
            p_conn, p_repl = rtc.connection, rtc.replies
        self.conn, self.repl = p_conn, p_repl

    def gs_start_streaming(self, block_print=False, block_wav=False):
        """Use rtclient functions to initialise streaming, start printing/wave recording too if needed."""
        newest_df = rtc.start_streaming(self.conn, self.repl)

        timestring = time.strftime('%Y%m%d-%H.%M.%S')
        if cl_args.wav and not block_wav:
            self.wave_name = wavfile_location+timestring+'.wav'
            # get the latest audio sample number to this value:
            self.repl.wave_sampnum_deque = wr.start_sound_recording(self.wave_name) # give the wave sample id deque to the client

        if cl_args.print and not block_print:
            self.tsv_name = printfile_location+timestring + '.tsv'
            print('tsv goes here:', self.tsv_name)
            self.repl.starting_timestamp=None
            self.repl.print_fo = open(self.tsv_name, 'w')  # open the print file in stream-reader
            self.repl.print_tsv = True  # set the flag to write streamed frames

        return newest_df

    def gs_stop_streaming(self):
        print('STOPPING STREAMING FROM THE GAMESERVER')
        newest_x = rtc.stop_streaming(self.conn, self.repl)
        wr.stop_sound_recording()
        print('sound recording flag is set:', wr.stop_recording.is_set())
        self.repl.print_tsv = False
        self.tsv_name = None
        self.repl.starting_timestamp = None
        try:
            self.repl.print_fo.close()
        except Exception as e:
            print('Couldn\'t close streaming file because', e)
            pass
        return newest_x

    def gs_load_biteplate_from_file(self, bp_fn, rs_fn):
        """If available, unpickle biteplate reps from these locations."""
        bp, rf = None, None
        if os.path.isfile(bp_fn):
            print('loading the biteplate from', cl_args.bpcs)
            bp = pickle.load(open(bp_fn, 'rb'))
        if os.path.isfile(rs_fn):
            print('loading ref file from ', cl_args.rscs)
            rf =  pickle.load(open(rs_fn, 'rb'))
        # no biteplate recording perfomed earlier, none desired
        return bp, rf

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

    def gs_record_biteplate_now(self):
        print("Performing a biteplate recording, current values:", self.bp_in_rs, self.rp_in_gs)

        """read the biteplate into BitePlane class - create mapping from global space to biteplate space"""

        response = self.inform_recording_start()
        # if streaming ready, stream biteplate recording for 5 seconds
        if response == 1:
            print('NOW DOING HEAD-CORRECTION')

            # get information about which sensors are head-correction and which are biteplate
            active, biteplate, reference = ci.get_sensor_roles_no_blender()
            print('these are sensor roles', active, biteplate, reference)

            server.repl._stop_b = True  # stop the normal behaviour of the data queue
            print('replies queue lives', server.repl._b.is_alive())

            # start streaming, get either 1 or (in properties) defined seconds of streaming data
            server.gs_start_streaming()
            print('started streaming')
            time.sleep(2 if pps.head_correction_time is None else pps.head_correction_time)

            # stop streaming
            server.gs_stop_streaming()
            print('stopped streaming')
            time.sleep(1)

            # access all the streamed data, empty the queue, saved elements in replies
            print('qsize is ',server.repl._q34.qsize())
            all_streamed = []
            while not server.repl._q34.empty():
                streamed_df = DataFrame(rawdf=server.repl._q34.get()[2])
                print('streamed df was', streamed_df)
                all_streamed.append(streamed_df)
            server.repl.latest_df = None
            server.repl.last_x_dfs.clear()

            print('\n\nstreamed data looks like', all_streamed[:1])

            server.repl._stop_b = False  # restart the normal behaviour of streamed data

            last_frames = dm.remove_first_ms_of_list(all_streamed,
                                                     ms=1 if pps.head_correction_exclude_first_ms is None
                                                     else pps.head_correction_exclude_first_ms)
            no_outliers= dm.remove_outliers(last_frames)
            average_bp = DataFrame(fromlist=no_outliers)
            print(average_bp)

            # prepare the transformations

            # isolate the coil objects
            refcoils = [average_bp.give_coils()[reference[x][0]] for x in range(len(reference))]
            bpcoils = [average_bp.give_coils()[biteplate[x][0]] for x in range(len(biteplate))]
            lind, rind, find = [ci.find_sensor_index(n) for n in ['BP1', 'BP2', 'BP3']]  #todo: check order

            # create a coordinate-system based on reference sensors (fully-defined here)
            rp_in_gs = ReferencePlane(*[x.abs_loc for x in refcoils[:3]])

            for c in bpcoils:
                c.ref_loc = rp_in_gs.project_to_lcs(c.abs_loc)

            # create the bp_in_rs (origin still to be determined)
            print('biteplate coils are:', lind, rind, find,*[average_bp.give_coils()[x] for x in [lind, rind, find]])
            bp_in_rs = BitePlane(*[average_bp.give_coils()[x].ref_loc for x in [lind, rind, find]])
            pickle.dump(bp_in_rs, open(os.path.normpath(os.getcwd() + os.path.sep + pps.biteplate_cs_storage), 'wb'))
            pickle.dump(rp_in_gs, open(os.path.normpath(os.getcwd() + os.path.sep + pps.refspace_cs_storage), 'wb'))
            # now rp_in_gs and bp_in_gs can be used to add attributes to the dataframes

            server.repl.print_tsv = cl_args.print
            print('correcting matrices are:', rp_in_gs.give_local_to_global_mat(), bp_in_rs.give_global_to_local_mat())
            if os.name == 'nt':
                import ctypes
                notification = ctypes.windll.user32.MessageBoxA(0,
                                                                b"Set up your wave/server for streaming of active sensor data",
                                                                b"Biteplate recording finished",
                                                                0)
            else:  # no popup yet for linux/mac
                print('NOW PREPARE FOR NORMAL STREAMING')
            return bp_in_rs, rp_in_gs

        else:  # presses cancel recording biteplate do nothing.
            return None, None


# create the request handler
class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    Python standard UDP socket server. UDP used because  of speed reasons.
    """
    tsv_name = None
    wave_name = None
    recording = wr.recording
    stop_recording = wr.stop_recording

    def shutdown_server_threads(self):
        """Shut down this particular socketserver, as well as the conn and replies connections from rtclient"""
        rtc.close_connection(rtc.connection)
        os._exit(1)  #exit() works

    def handle(self):
        """Handle requests sent to the gameserver from Blender."""
        if pps.development_mode:
            from scripts.ema_shared.miscellanous import reload_modules_for_testing
            reload_modules_for_testing(dm)

        ### self.request is the TCP socket connected to the client
        ###self.data = self.request.recv(1024).strip()  # no questions asked, just give the latest_dfs object
        self.data = self.request[0].strip()
        self.socket = self.request[1]

        print("UDP Gameserver received the request:", self.data)
        kill_server = False

        # catch the data to be sent
        # quantitative data - return rolling average
        if self.data == b'SINGLE_DF':
            newest_df = rtc.get_one_df(self.server.conn)
            data_to_send = newest_df  # returns unsmoothed data

        elif self.data == b'START_STREAM':
            self.server.gs_start_streaming()
            data_to_send = 'streaming started'  # returns nothing, just issues command

        elif self.data == b'STREAM_DF':
            newest_x = rtc.get_last_streamed_dfs()
            #data_to_send = newest_x[-1] # simplest output for debugging
            data_to_send = DataFrame(fromlist=newest_x)  # returns averaged data from the latest x dfs

        elif self.data == b'STREAM_STOP':
            newest_x = self.server.gs_stop_streaming()
            data_to_send = DataFrame(fromlist=newest_x)  # returns averaged data from the latest x dfs

        # qualitative data, no manipulation
        elif self.data == b'PARAMETERS':
            data_to_send = rtc.get_parameters(self.server.conn)
        elif self.data == b'TEST':
            data_to_send = rtc.test_communication(self.server.conn)
        elif self.data == b'TEST_ALIVE':
            data_to_send = b'YES, GAMESERVER IS RUNNING'
        elif self.data == b'STATUS':
            data_to_send = rtc.get_status()
        elif self.data == b'KILL_CLIENT':
            print('\n\nKILLING CLIENT SERVER\n')
            kill_server = True
            data_to_send = b'KILLINGSERVER'
        elif self.data == b'CAM_TRANS':
            print('choosing data', self.server.last_cam_trans, server.cam_pos)
            data_to_send = [self.server.last_cam_trans, self.server.cam_pos]
        else:
            data_to_send = b'NO DATA REQUESTED.'

        # head-correct the data to be sent
        if type(data_to_send) == DataFrame and cl_args.headcorrect:
            print('performing head-correction on this dataframe with', self.server.bp_in_rs)
            print('performing head correction on this df', data_to_send)
            data_to_send, self.server.last_cam_trans, self.server.cam_pos = dm.head_corr_bp_correct(data_to_send,
                                                                                                    self.server.bp_in_rs if self.server.bp_in_rs is not None else pickle.load(open(cl_args.bpcs), 'rb'),
                                                                                                    self.server.rp_in_gs if self.server.rp_in_gs is not None else pickle.load(open(cl_args.rscs), 'rb'))

        # serialise the data to be sent
        pd = pickle.dumps(data_to_send)
        print("Game server is replying to Blender:", pd[:100])

        self.socket.sendto(pd, self.client_address)

        #### below in comments is likely the old method using TCP
        # communicate using socket.makefile, dump into serverfile
        #sf = self.request.makefile(mode='wb', buffering=0)
        #sf.write(pd)

        # send file
        #sf.flush()
        #sf.close()

        if kill_server:
            server.conn.s.close()

            self.shutdown_server_threads()
            self.server.shutdown()


#TODO: Needs attention - can this exist in gameserver and get parameters on __init__?
def n_frames_smoothed(conn, ms=None, frames=None):
    """
    Smoothing takes the form of a rolling average over the last n frames to filter rnadom error.
    The number of frames is either defined directly (frames)
    or by the number of ms over which the frames are retained for smoothing.
    :return int: the number of frames that are retained for smoothing.
    """
    # average over a number of milliseconds based on average streaming rate
    if ms is not None:
        xmlelem = rtc.get_parameters(conn)
        freqelem = xmlelem.find('//Frequency')
        frequency = float(freqelem.text)
        return (frequency * 1/1000 * ms) // 1   # frequency in seconds/1000 * ms desired, lower bound
    # average over a number of measurements
    elif frames is not None:
        return int(frames)
    else:
        return 1


# command line arguments given when gameserver is initialised (from Blender usually)
parser = argparse.ArgumentParser(description='EMA client running as intermediate server, responds to requests from BGE')

# smoothing the streamed dataframes
parser.add_argument('--smoothms',
                    help='Give the number of milliseconds that the location signals should be averaged over.',
                    default='100')
parser.add_argument('--smoothframes',
                    help='Give the number of frames that location signals should be smoothed over, if ms not given.')

# saving the dataframes as TSV files and recordings as WAV files
parser.add_argument('-print',
                    help='Include if raw coil locations should be stored in tsv file.', action='store_true')
parser.add_argument('--printdir',
                    help='Specify where the tsv file should be stored. Be sure to give absolute path.',
                    default=os.path.normpath('../../../../'+pps.tsv_output_dir)) # todo: ../s should not be necessary from subprocess/testing
parser.add_argument('-wav',
                    help='Record a wave file from the default microphone when streaming.',
                    action='store_true')
parser.add_argument('--wavdir',
                    help='specify where recorded wave files should be saved.',
                    default=os.path.normpath('../../../../'+pps.wav_output_dir)) # todo: ../s should not be necessary from subprocess/testing

# whether head-correction should be performed, and if so, potentially the location of a pickled biteplate object
parser.add_argument('--headcorrect',
                    help='Perform head-correction, making a biteplate recording if needed.',
                    action='store_true', default=False)
parser.add_argument('-bpcs',
                    help='filename of the picked biteplate CS to be used if already recorded.',)
parser.add_argument('-rscs',
                    help='filename of the reference CS to be used if already recorded.')


# default CL arguments if not run as subprocess
cl_args = parser.parse_args(pps.game_server_cl_args)

if __name__ == "__main__":
    cl_args = parser.parse_args()
    print('command line arguments for the gameserver are', cl_args)

    main()

