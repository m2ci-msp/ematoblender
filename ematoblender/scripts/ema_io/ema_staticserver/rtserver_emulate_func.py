# -*- coding: utf-8 -*-
__author__ = 'Kristy James, Alexander Hewer'


"""
This module encapsulates the functionality of the RTServer.
That is, the commands sent to the server as requests are parsed as function names in this module.
The results of these functions are then sent back to the client.
"""

# extracting parameters and motion from mocap files
import xml.etree.ElementTree as ET

from .mocap_file_parser import MakeMocapParser
import os

# streaming
import time
import sys

import threading

# Base class for server-internal info
class RTServerBase():
    """
    Class taking care of the parameters of the RT server. Handles:
    - Params for returning data as described in the RTC3D Protocol
    - If static data, the file name/location
    Parameters that can be included based on Protocol are: All, General, 3D, Analog, Force, 6D, Events, Force, Stop
    """

    def __init__(self, connection, xml_template_location='./parameter_skeleton.xml'):
        """
        Initialise the server.
        :param connection: The connection object, defined in ..client_server_comms as BasicConnection object or similar.
        :param xml_template_location: Location of an initial XML string of parameters, so SendParameters can give info.
        """

        self.conn = connection                          # connection used to send responses
        # skeletal xml form, will be from data file
        self.xmltree = ET.parse(os.path.normpath(os.path.split(__file__)[0] + os.path.sep + xml_template_location))
        self.serverparams = self.xmltree.getroot()    # root of xml, this is edited and returned.

        self.static_data = None                         # no data file defined yet.
        self.status = 'READY'                           # statuses: ['READY', 'EOF', 'STREAMING']

    def validate_message_type(self, mytype):
        """Check that the message has a type=1, because the other types can only be generated by the server."""
        if mytype != 1:
            self._err_wrong_status(mytype)
            return False
        else:
            return True

    ##### Available commands as described in the RTC3D Protocol  #####
    def version(self, version_no, *otherargs, **kwargs):
        """Does nothing, this package only supports the one protocol version (1.0)."""
        pass

    def sendparameters(self, *arglist, **kwargs):
        """Return the information about the EMA machine/RT server from xml string in self.serverparams.
        Unlike in the protocol, the entire XML is always returned."""
        if 'force' in arglist or 'analog' in arglist or 'events' in arglist:
            self.conn.send_packed('Error-Requested parameters not supported in this implementation.', 0)
            return

        else:  # if len(arglist) == 0 or 'all' in arglist:
            self.conn.send_packed(ET.tostring(self.serverparams, short_empty_elements=True), 2)
            return

    def bye(self, *args, **kwargs):
        """ Stop doing things, change state. Disconnecting handled in handle() method."""
        print("Now performing connection shutown as nothing received.")
        self.status = 'READY' if self.status != 'EOF' else 'EOF' # stops streaming at poll time
        time.sleep(0.5)  # ensure file closed after queues' polling
        # XML parameters discarded

    # Unavailable command (less important because only using Big Endian)
    def setbyteorder(self, *args, **kwargs):
        """Not to be implemented. Does nothing."""
        raise NotImplementedError

    # Commands shadowed in child classes
    def sendcurrentframe(self, *args, **kwargs):
        raise NotImplementedError

    def streamframes(self, *args, **kwargs):
        raise NotImplementedError

    # Error functions
    def _err_wrong_status(self, msgtype):
        """Reply with an error for sending a command with status !=1"""
        reply = "Error-Wrong command status: {}".format(str(msgtype))
        self.conn.send_packed(reply, 0)

    def _err_command_execution(self, command):
        """Reply with an error regarding the command execution."""
        reply = "Error-Execution error: {}".format(command)
        self.conn.send_packed(reply, 0)

    def _err_parameters_unsupported(self, command):
        """Reply with an error regarding the command execution."""
        reply = "Error-Cannot support requested parameters: {}".format(command)
        self.conn.send_packed(reply, 0)


class RTServer_Static(RTServerBase):
    """Pretend to be a live RTC3D server but actually be a text document."""

    def __init__(self, filename, connection, loopfile=False):
        """
        Emulate all the server functionality from a text file.
        Begin by creating the parameter xml from the header, ready to send/stream frames.
        :param filename: Path to the file that should be streamed.
        """

        # initialise the super class, containing self.conn and XML root as self.serverparams.
        RTServerBase.__init__(self, connection)
        print('Initialising a static server emulation with filename', filename)
        # open the parser for the data file as self.static_data
        self.static_data = MakeMocapParser.factory(filename)

        # place some data from the capture file into XML
        self.serverparams = self.static_data.xml_tree.getroot()

        # set some global settings
        self.emulator_loop = loopfile

    def __str__(self):
        return "Static C3D Info object with motion data as {} ".format(str(self.static_data))

    ################ RTC3D PROTOCOL COMMANDS
    def streamframes(self, *args, **kwargs):
        """
        Based on the given frequency, stream the frames at this rate.
        self.status of READY or STREAMING results in status set to STREAMING and streams.
        self.status of EOF returns empty data.
        'stop' sets status back to READY.
        # Future TODO: Values other than location from the API are not implemented.
        """

        # Parameters requested that are not 'stop'. Simply those in data file are returned.
        if not all(arg.startswith('stop') or arg.lower().startswith('frequency') for arg in args):
            #self._err_parameters_unsupported(str('streamframes '+' '.join(args)))
            print("Error in given parameters.")
            pass  # TODO: This persists with default values even though the command asked for different parameters, added because parameters necessary for live use.

        # time aspect
        ft = self.static_data.frame_time  # frame time (inverse of frequency) in microseconds

        self._delay = 0

        streamthread = threading.Thread(group=None, target=self._stream_one_frame)

        # use the command to stop/fail to start streaming
        if 'stop' in args and (self.status == 'READY' or self.status == 'STREAMING'):  # stop streaming
            self.status = 'READY'

        elif self.status == 'EOF':
            self.conn.send_packed("No data, EOF or no measurement", 4)

        else:  # command asks to start streaming
            print("Starting the repeating timer, using only the pre-determined frequency.")
            self.status = 'STREAMING'
            streamthread.start()

    def _stream_one_frame(self, *args, **kwargs):
        """Define how one frame should be streamed using the repeating timer.
        If end reached, set status as EOF or loop."""

        # compute frame time in seconds
        ft = self.static_data.frame_time/1000000

        # prepare the first data package to be sent

        # get the motion frame as message in packed wave format
        status, message, *timestamp = self.static_data.give_motion_frame()

        # restart loop or cancel if EOF, update stats
        status, message, *timestamp = self._check_streaming_eof(status, message, timestamp)

        # try to send frames, such that betweeen two send operations ft seconds have passed
        while self.status == 'STREAMING':

            # send data
            self.conn.send_packed(message, status)

            # get starting time for measuring preparation time
            start = time.clock()

            # skip frames if delay becomes too high
            while self._delay > ft:

                self.static_data.motion_lines_read += 1
                self._delay -= ft

            # get the motion frame as message in packed wave format
            status, message, *timestamp = self.static_data.give_motion_frame()

            # restart loop or cancel if EOF, update stats
            status, message, *timestamp = self._check_streaming_eof(status, message, timestamp)

            #from scripts.ema_io.rtc3d_parser import DataFrame
            #print(DataFrame(message).give_timestamp_secs())
            # time.sleep(0.5) # debugging

            # get end time for measuring preparation time
            end = time.clock()

            # compute time we can sleep before sending the data
            sleeptime = ft - (end - start)

            # check if we have time to sleep
            if sleeptime > 0:

                # we have time
                time.sleep(sleeptime)
            else:

                # no time, we might even be late
                # measure delay
                self._delay += abs(sleeptime)


    def _check_streaming_eof(self, status, message, timestamp):
        if status == 4:  # no more data available
            # looping not available, signal EOF and let stop
            if self.emulator_loop is False:
                self.status = 'EOF'
                print('\n\n\n I AM SETTING EOF STATUS')
            # looping available, reset the static data to the beginning of the motion section and get frame again
            else:
                self.static_data.reset_motion_section()
                status, message, timestamp = self.static_data.give_motion_frame()
                print("Restarted motion frame looks like:", status, message, timestamp)
                # increment frames streamed in the XML data
                self.serverparams = self.static_data.update_xml_stats().getroot()
        else:
            # increment frames streamed in the XML data
            self.static_data.update_xml_stats()

        return status, message, timestamp

    def sendcurrentframe(self, *args, **kwargs):
        """Send back the next frame in the data file."""
         # get the motion frame as message in packed wave format
        status, message, *timestamp = self.static_data.give_motion_frame()

        # if last measurement sent, set functionality status
        if status == 4:
            if self.emulator_loop is False:
                self.status = 'EOF'
                print('location 2 setting eof')
            elif self.emulator_loop is True:
                self.static_data.reset_motion_section()
                status, message, timestamp = self.static_data.give_motion_frame()
        else:
             # increment frames streamed in the XML data
            self.serverparams = self.static_data.update_xml_stats().getroot()

        # send the frame
        print('\nSending a single df from rtserver_emulate_func.py.', file=sys.stderr)
        self.conn.send_packed(message, status)


class RTServer_Live(RTServerBase):
    """Pretend to be a live RTC3D server but actually be my something else live."""
    def __init__(self, server):
        """This class reflects the NDIWave machine RT server.
        It is not used, because the needs are filled by the machine."""
        raise NotImplementedError


if __name__ == "__main__":
    pass
