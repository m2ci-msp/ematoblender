#!/usr/bin/env python3
__author__ = "Kristy James, Alexander Hewer"

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
import math

# used for serialising and sending
import socketserver
import pickle
import xml.etree.ElementTree as et

# used for saving and manipulating incoming data
from . import wave_recording as wr
from . import data_manipulation as dm
from .biteplate_headcorr import HeadCorrector
from .tongue_model import TongueModel
from .ExternalFittingServer import ExternalFittingServer
from .GameServerSettings import GameServerSettings as settings

# global properties, coil definitions
from ...ema_shared import properties as pps
from ...ema_blender import coil_info as ci

# connection objects (this server essentially wraps rtc behaviour)
from . import rtclient as rtc
from ..rtc3d_parser import DataFrame, JSONBuilder

def main(argv):
    """
    Initialise the gameserver, getting the TSV and WAV locations to print from from CL arguments,
    or if they are not present from the properties file.
    Start the gameserver, run the biteplate-recording routine.
    Run gameserver.serve_forever()
    """
    cl_args = parser.parse_args(argv if argv is not None else pps.game_server_cl_args)

    # create the file that the streamed data will be printed to
    global printfile_location, wavfile_location
    printfile_location = GameServer.output_prefix(cl_args.printdir)
    wavfile_location = GameServer.output_prefix(cl_args.wavdir)
    print('the printfile location is', printfile_location, 'the wavfile location is', wavfile_location)

    global server
    server = GameServer(cl_args)

    # set an initial printing value
    server.repl.print_tsv = server.cla.print

    ############### BITEPLANE AND HEAD-CORRECTION HYPOTHESIS ############

    server.headcorrection = HeadCorrector()

    # biteplate recording performed earlier and pickled
    if server.cla.prepickled is not None:
        server.headcorrection.load_picked_from_file(self.cla.prepickled)

    # perform a biteplate recording and pickle the values
    elif server.cla.headcorrect: # unfulfilled by attempt at loading

        if server.cla.live is not None: # do a live recording
            server.headcorrection.load_live(server.cla.live)
        elif server.cla.fromtsv is not None: # get from TSV
            server.headcorrection.load_from_tsv_file(server.cla.fromtsv)


    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    print('About to serve forever')
    server.serve_forever()
    print("Server was shutdown")



class GameServer(socketserver.UDPServer):

    """
    Used for smoothing measurements, performing other corrections before coordinates are sent to game loop.
    Game server, inherits from socketserver, handling is defined in MyUDPHandler.
    """
    @staticmethod
    def output_prefix(relloc):
        """Based on the given option generate a file prefix to write TSV or WAV to"""
        if not os.path.isabs(relloc):
            return os.path.normpath(os.getcwd()+ os.sep + relloc + os.sep + 'EMA_')
        else:
            return relloc + os.sep + 'EMA_'

    def __init__(self, serve_in_thread=False):


#        print('Now creating the gameserver with settings:', settings)

        # get HOST and PORT from shared properties
#        HOST = pps.gameserver_host
#        PORT = pps.gameserver_port

        super().__init__((settings.host, settings.port), MyUDPHandler)

        print('Game server is', self)

        # external fitting server
        self.externalServer = ExternalFittingServer()

        # store headcorrection matrices
        self.headcorrection = HeadCorrector()
        print('Initial headcorrection status is', settings.useHeadCorrection)

        self.last_cam_trans = None  # storage needed for handler
        self.cam_pos = None

        # import or start the client connection
        if rtc.connection is None or rtc.replies is None:
            p_conn, p_repl = rtc.init_connection(
                wavehost=settings.rtcHost, waveport=settings.rtcPort)
        else:
            p_conn, p_repl = rtc.connection, rtc.replies
        self.conn, self.repl = p_conn, p_repl

        # determine the amount of smoothing on streaming dataframes
        self.set_smoothing_n()

        self.last_status = 'INITIALISED'

        # start the serve_forever method (used when shown with GUI)
        if serve_in_thread:
            import threading
            self.serve_thread = threading.Thread(target=self.serve_forever)
            self.serve_thread.start()


    def set_smoothing_n(self, n=None):
        """sets the smoothing from the most recent cla values"""
        if n is None:
            n = self.n_frames_smoothed(ms=settings.smoothMs, frames=settings.smoothFrames)
        self.smooth_n = n
        self.repl.change_smoothing_length(self.smooth_n)


    def n_frames_smoothed(self, ms=None, frames=None):
        """
        Smoothing takes the form of a rolling average over the last n frames to filter random error.
        The number of frames is either defined directly (frames)
        or by the number of ms over which the frames are retained for smoothing.
        :return int: the number of frames that are retained for smoothing.
        """
        # average over a number of milliseconds based on average streaming rate
        if ms is not None:
            xmlelem = et.fromstring(rtc.get_parameters(self.conn))
            print(type(xmlelem))
            freqelem = xmlelem.find('.//Frequency')
            print(freqelem)
            frequency = float(freqelem.text)
            return int(math.floor((frequency * 1/1000 * ms)))   # frequency in seconds/1000 * ms desired, lower bound
        # average over a number of measurements
        elif frames is not None:
            return int(frames)
        else:
            return 1

    def gs_start_streaming(self, block_print=False, block_wav=False):
        """Use rtclient functions to initialise streaming, start printing/wave recording too if needed."""
        newest_df = rtc.start_streaming(self.conn, self.repl)

#        print('starting streaming with arguments', self.settings["waveFile"], self.cla.print)
        timestring = time.strftime('%Y%m%d-%H.%M.%S')

        if settings.outputWave:
            self.wave_name = self.output_prefix(settings.waveDir) + timestring +'.wav'
            # get the latest audio sample number to this value:
            self.repl.wave_sampnum_deque = wr.start_sound_recording(self.wave_name) # give the wave sample id deque to the client

        if settings.saveReceivedData:
            self.tsv_name = self.output_prefix(settings.receivedDataOutputDir + timestring + '.tsv')
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

    def shutdown_server_threads(self):
        """Shut down this particular socketserver,
        as well as the conn and replies connections from rtclient,
        and the request handler if running in a thread.
        """
        print('Closing the connection to the dataserver (CLIENT ROLE)')
        rtc.close_connection(self.conn)

        print('Closing the request handler accessed by Blender (REQUEST HANDLER)')
        if hasattr(self, 'server_thread'):
            self.serve_thread.join(0.1)

        self.shutdown()

# create the request handler
class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    Python standard UDP socket server. UDP used because  of speed reasons.
    """

    # tsv_name = None
    # wave_name = None
    recording = wr.recording
    stop_recording = wr.stop_recording

    def handle(self):
        """Handle requests sent to the gameserver from Blender."""

        self.data = self.request[0].strip()
        self.server.last_status = self.data
        self.socket = self.request[1]

        print("UDP Gameserver received the request:", self.data)
        print('Headcorrection is', settings.useHeadCorrection)
        kill_server = False

        # catch the data to be sent
        # quantitative data - return rolling average
        if self.data == b'SINGLE_DF':
            newest_df = rtc.get_one_df(self.server.conn, self.server.repl)
            data_to_send = newest_df  # returns unsmoothed data

        elif self.data == b'START_STREAM':
            self.server.gs_start_streaming()
            data_to_send = 'streaming started'  # returns nothing, just issues command

        elif self.data == b'STREAM_DF':
            newest_x = rtc.get_last_streamed_dfs()
            #data_to_send = newest_x[-1] # simplest output for debugging
            """
            This step represents the live filtering
            - input must be a list of some DataFrame objects
            - output must be a single DataFrame
            This currently uses the default fromlist construction
            which is simply the average of the values in each dimension,
            and average rotation values using the average_quaternions fn.
            """
            data_to_send = DataFrame(fromlist=newest_x)  # returns averaged data from the latest x dfs

        elif self.data == b'STREAM_STOP':
            newest_x = self.server.gs_stop_streaming()
            data_to_send = DataFrame(fromlist=newest_x)  # returns averaged data from the latest x dfs

        # qualitative data, no manipulation
        elif self.data == b'PARAMETERS':
            data_to_send = rtc.get_parameters(self.server.conn)

        elif self.data == b'TEST':
            data_to_send = rtc.test_communication(self.server.conn, self.server.repl)

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

        elif self.data == b'SET_MODEL_VERTEX_INDICES':
            self.server.externalFittingServer.set_model_vertex_indices()
            data_to_send = b'SET MODEL VERTEX INDICES.'

        elif self.data == b'RESET':
            self.server.externalFittingServer.reset()

        else:
            data_to_send = b'NO DATA REQUESTED.'

        # head-correct the data to be sent
        if type(data_to_send) == DataFrame and settings.useHeadcorrection:
            print('performing head-correction on this dataframe with', self.server.headcorrection.biteplane)
            print('performing head correction on this df', data_to_send)
            data_to_send, self.server.last_cam_trans, self.server.cam_pos = dm.head_corr_bp_correct(data_to_send,
             self.server.headcorrection.biteplane,
            self.server.headcorrection.refplane)
            print('Applying head-correction')

        # fit data frame in external fitting server
        if type(data_to_send) == DataFrame:
            self.server.externalServer.fit(data_to_send)

        # serialise the data to be sent
        pd = pickle.dumps(data_to_send)
        print("Game server is replying to Blender:", pd[:100])

        self.socket.sendto(pd, self.client_address)

        if kill_server:
            server.conn.s.close()
            self.shutdown_server_threads()
            self.server.shutdown()


# command line arguments given when gameserver is initialised (from Blender usually)
parser = argparse.ArgumentParser(description='EMA client running as intermediate server, responds to requests from BGE')

# smoothing the streamed dataframes
smoothgroup = parser.add_mutually_exclusive_group()
smoothgroup.add_argument('-ms', '--smoothms',
                         type=int,
                         help='Give the number of milliseconds that the location signals should be averaged over.',
                         default='100')
smoothgroup.add_argument('-fr','--smoothframes',
                         type=int,
                         help='Give the number of frames that location signals should be smoothed over, if ms not given.')

# saving the dataframes as TSV files and recordings as WAV files
savegroup = parser.add_argument_group("Saving options", "Determine whether and where to saved streamed data/audio")
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
parser.add_argument('-hc', '--headcorrect',
                    help='Perform head-correction, making a biteplate recording if needed.',
                    action='store_true')
hcgroup = parser.add_mutually_exclusive_group()
hcgroup.add_argument('--prepickled',
                     help="filename of the pickled head-correction recording if already made.")
hcgroup.add_argument('--fromtsv',
                     help="filename of the TSV recording of the head-correction session.")
hcgroup.add_argument('--live',type=int,
                     help="number of seconds live streaming to record for head-correction.")

netgroup = parser.add_argument_group('dataserver_addr', 'Network location of the articulograph/dataserver')
netgroup.add_argument('--host', help='HOST of the articulograph/dataserver')
netgroup.add_argument('--port', help='PORT of the articulograph/dataserver', type=int)

parser.add_argument('-g', '--gui', help='Use the GUI', action='store_true')

parser.print_help()

if __name__ == "__main__":

    # default CL arguments outside of main in case this is not specified
    main(argv=sys.argv)
