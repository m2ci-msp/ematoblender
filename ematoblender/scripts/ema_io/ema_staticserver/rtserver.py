# -*- coding: utf-8 -*-
__author__ = 'Kristy'

"""
This module defines how the static server works.
This is a TCP server with threading, that creates a separate thread for each request.
It has functions that handle changing which data-file the server streams from and the looping behaviour,
so that these can be passed on to the parsing function.
However, the handle function passes the commands to a further module, rtserver_emulate_func.py,
which determines how to respond to these incoming requests.

The main function takes command line arguments for starting the server, and runs it in the command line.
"""
# TODO: Future developments should continue the current streaming status when a new file is loaded.

# server functionality
import socketserver

from ..client_server_comms import ServerConnection, RTC3DPacketParser
from .rtserver_emulate_func import RTServer_Static
from ...ema_shared import properties as pps

# for debugging
import sys
import traceback
import time

# for threading
import threading

# for command line
import argparse


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """ ThreadedTCPServer uses Python's inbuilt socketserver behaviour to create a server. """

    def __init__(self, address, requesthandler, datafile, loop=True):
        """
        Initialise the TCP threaded server.
        :param address: (HOST, PORT) tuple
        :param requesthandler: RTServer_Static class, determines the response from the self.handle() fn
        :param datafile: The path to the datafile that the server streams from initially.
        :param loop: true/false, if true the server begins again at the start of the data file when it ends.
        """
        super().__init__(address, requesthandler)
        print('Server address is:', self.server_address)
        self.allow_reuse_address = True

        self.datafile = datafile
        self.server_loop = loop
        self.server_conn = None

        self.rt_fns = RTServer_Static(self.datafile, self.server_conn, loopfile=self.server_loop)

        self.active_threads = []

    def change_datafile(self, new_datafile):
        """ Change the datafile that self reads information from. """
        self.rt_fns.static_data.file.close()
        self.datafile = new_datafile
        self.rt_fns = RTServer_Static(self.datafile, self.server_conn, loopfile=self.server_loop)
        pps.streaming_source = new_datafile  # TODO: This line is probably ineffective

    def change_loop(self, new_loop=None):
        """
        Change the file looping behaviour of the server.
        :param new_loop: True to loop the data file, False to fail after data lines are exceeded.
        """
        if new_loop is not None:
            self.rt_fns.emulator_loop = new_loop
            self.server_loop = new_loop
        else:
            self.rt_fns.emulator_loop = not self.rt_fns.emulator_loop
            self.server_loop = not self.server_loop
        return self.rt_fns.emulator_loop

    def server_close(self):
        """Shut down the server, with pausing behaviour for any continuing threaded tasks."""
        print('Checking status of threads')
        for t in self.active_threads:
            print(t.name, 'alive?', t.is_alive())
            t.join(timeout=0.05)  # explicitly close all the threads created, waiting 0.05 secs if needed
            print(t.name, 'alive?', t.is_alive(), '\n')
        print('Closing the open data file.')
        self.rt_fns.static_data.file.close()
        print('Performing server\'s shutdown method')
        self.shutdown()
        print('Performing server\'s close method')
        super().server_close()


class FakeRTRequestHandler(socketserver.BaseRequestHandler):
    """
    FakeRTRequestHandler shadows the handle function of the SocketServer.
    self.request is the TCP socket connected to the client, to which send/receive fns are linked.
    """
    # as per NDI WAVE RTC3D instructions
    disable_nagle_algorithm = True

    # flag to indicate changing behaviour
    new_datafile_flag = False
    new_loop_flag = False

    # placeholders, filled on __init__
    datafile = None
    loop = None
    rt_fns = None

    def handle(self):
        """
        Reply based on the client's request, which per socketserver is self.request.
        A peristent connection is established, so continue replying until connection is broken.
        Command functionality as rt_fns; pass on the request to this further module.
        """

        # firstly parse request by ServerConnection class (unpacks the packet according to the RTC3D RTC3DPacketParser)
        conn = ServerConnection(self.request, RTC3DPacketParser)
        # make this request an attribute of the ThreadedTCPServer and FakeRTRequestHandler for access
        self.server.server_conn = conn
        self.server.rt_fns.conn = conn

        print("Functionality initialised, ready to respond to client")

        while True:  # Persistent connection

            #receive and unwrap the data
            data = conn.receive_verbatim()
            #print("\n\nRequest received: ", data, file=sys.stderr)

            # disconnect messages
            if data == b'' or data is None:
                #reply = "Disconnecting."
                #conn.send_packed(reply, 1)
                #print("Blank message received.", file=sys.stderr)
                self.server.rt_fns.bye()
                break #prev. break  # no data received (possible timeout), disconnect socket

            # server decodes request method
            size, atype, text, *otherargs = conn.protocol.unpack_wrapper(data)
            #print("Message received: ", size, atype, text, file=sys.stderr)
            text = text.decode('UTF-8').rstrip(' \t\n\r\0').lstrip('_')

            # text is a command string, now sever responds
            command = text.lower().split(' ')
            fn_name, *commargs = command
            #print("Command issued is: ", fn_name, commargs, file=sys.stderr)

            ############ handle messages of wrong type ##########
            if not self.server.rt_fns.validate_message_type(atype):
                continue  # skip to next command if msg type is not 1

            ########### handle all commands  #########
            try:  # check if the command is described for the modality being queried
                method = getattr(self.server.rt_fns, fn_name)
            except Exception as e:  # command not defined
                conn.send_packed("Error-Unknown command: {}".format(str(text)), status=0)
                continue

            # command is defined
            #print("Using method:", str(method), 'commargs:', commargs, file=sys.stderr)

            try:
                # start a thread to handle the command
                command_thread = threading.Thread(target=method, args=commargs)
                command_thread.daemon = True
                command_thread.start()  # as threaded server, these are now executed in thread. rt_fns sends reply.
                #print('command {} executed on thread {}'.format(command, command_thread.name), file=sys.stderr)
                conn.send_packed('OK-'+text, 1)  # should follow method response

            except Exception as e:
                print("Problem: ", e)
                print(sys.exc_info()[0], file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                self.server.rt_fns._err_command_execution(text)

            else:
                conn.send_packed('OK-'+text, 1)  # should follow method response
            finally:
                self.server.active_threads.append(command_thread)  # this clogs memory somewhat, but allows explicit join


def initialise_server(datafile='', loop=True):
    """
    Initialise the server running in a thread.
    :param datafile: path to the datafile to be streamed initially
    :param loop: whether to loop the datafile
    """
    # initialise the server
    server = ThreadedTCPServer((pps.waveserver_host, pps.waveserver_port), FakeRTRequestHandler, datafile, loop=loop)

    # start a thread with the server
    # thread starts another thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # set to exit the server thread when main thread terminates
    server_thread.daemon = True
    return server_thread, server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Server, emulating NDI Wave, taking info from a static EMA data file.')
    parser.add_argument('Datafile', help='Load an EMA data file, .tsv and .bvh formats available.')
    parser.add_argument('-loop', help='Include to continue looping over data.', action='store_true')
    cl_args = parser.parse_args()

    st, so = initialise_server(datafile=cl_args.Datafile, loop=cl_args.loop)

    print('Starting first server thread.')
    st.start()

    # let the server keep serving, verbosely
    while st.is_alive():
        print("Server still alive; emulating file '{}' with looping set to {}."
              .format(FakeRTRequestHandler.datafile, FakeRTRequestHandler.loop))
        time.sleep(30)
