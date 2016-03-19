# -*- coding: utf-8 -*-
"""
SCRIPT THAT QUERIES THE WAVE REALTIME SERVER USING THE NDIWAVE RTC3D PROTOCOL.
ALSO QUERIES OUR PERSONAL SERVER ACTING USING THE SAME COMMANDS (EMULATING REAL-TIME DATA).
Depends on the rtc3d_parser module to unwrap the binary packages.
"""

# communication with the server, parsing the objects to and from Coil/DataFrame etc
from ematoblender.scripts.ema_io.rtc3d_parser import RTC3DPacketParser, DataFrame
from ematoblender.scripts.ema_io.client_server_comms import ClientConnection

# threading of replies
from threading import Thread
from queue import Queue, Empty
from collections import deque

# debugging
import time
import copy

# global variables
connection = None
replies = None


class NonBlockingStreamReader():

    def __init__(self, stream, last_x=5,):
        """Stream: The stream to read from, here received from the server.
        Stream is a Clientconnection object, so NBSR make use of the methods.

        self.latest_df contains a DataFrame object, wiht the latest coil coordinates.
        Coils are accessed as self.latest_df.components[n].coils[m],
        Each coil has self.abs_loc, self.abs_rot (quaternions)
        """

        # Connection-related objects
        self.alive = True
        self._s = stream  # This should be a connection object
        self.protocol = self._s.protocol

        # Dataframe related objects
        self.no_data = False  # begin presuming there is data to be read
        self.latest_df = None
        self.last_x_dfs = deque(maxlen=last_x)

        # Queues for different types of sever responses
        self._q01 = Queue()  # status
        self._q2 = Queue()  # parameter data
        self._q34 = Queue()  # data frame
        self._q5 = Queue()  # c3d file and other

        # file for writing the streamed data
        self.print_tsv = False
        self.print_fo = None
        self.starting_timestamp = None
        self.wave_sampnum_deque = None

        # the heart of this class. Must run for client functionality
        self._t = Thread(target=self._populateQueue, )
        self._t.daemon = True
        self._t.start()  # start listening

        # for use in Blender - keep a obj that is the most-recent df, for display
        self._stop_b = False
        self._b = Thread(target=self._updateCurrentDataFrame, )
        self._b.daemon = True  # End if script ends
        self._b.start()  # start listening

        # for testing purposes, just show all output immediately
        self._pr = Thread(target=self._printReplies, )
        self._pr.daemon = True
        #self._pr.start()    # turn on/off this line for debugging what is received from server,
        # will ruin other queue-based functionality

        self.threads = [self._b, self._pr, self._t]

    def _populateQueue(self):
        """Collect lines from stream and put in queue.
        Thread is always receiving."""
        while self.alive:
            #print('!!!!!!!!!!!\n\n\n\n unpacking wrapper')
            # TIME IS DEPENDENT ON RECEIVE VERBATIM TIME
            line = self._s.protocol.unpack_wrapper(self._s.receive_verbatim())
            if line is not None:
                #print("Line is not none")
                rsize, rtype, rmsg = line

                if rtype == 0 or rtype == 1:
                    self._q01.put(line)
                elif rtype == 2:
                    self._q2.put(line)
                elif rtype == 3 or rtype == 4:
                    self._q34.put(line)
                    if rtype == 3 and self.print_tsv:
                        if self.starting_timestamp is None:
                            self.starting_timestamp = DataFrame(rawdf=rmsg).components[0].timestamp
                        if self.print_fo is not None and not self.print_fo.closed:
                            # write a dataframe, with an audio sample number included
                            self.print_fo.write(DataFrame(rawdf=rmsg)
                                                .to_tsv(relative_timestamp_to=self.starting_timestamp,
                                                        closest_sound_sample=self.wave_sampnum_deque
                                                        if self.wave_sampnum_deque is not None else [0]))
                else:
                    self._q5.put(line)
            else:
                print(time.strftime('%x %X %Z'), "\t\tSocket timeout, remains open. \r")
                time.sleep(0.5)
                # Previously closed script here, but rather it may be due to not starting streaming
        print("Queue-populating thread closing.")

    def _printReplies(self):
        """If there is something in a queue, print it."""
        while self.alive:
            for q in [self._q01, self._q2, self._q34, self._q5]:
                thing = self.readq(q)
                if thing is not None:
                    print(thing)
        print("Thread closing")

    def _updateCurrentDataFrame(self):
        while self.alive:
            if not self._stop_b:
                #print('!!!!!!!!!!!! pulsing to update current dataframe')
                msg = self.readdata()
                #print(type(msg))
                if type(msg) == DataFrame:
                    #print('!!!!!!!!!!!! updating current dataframe')
                    self.no_data = False
                    self.latest_df = msg
                    self.last_x_dfs.append(self.latest_df)
                else:
                    #print('No data at this point.')
                    continue
            else:
                time.sleep(0.1)
                # updating is turned off
        print("Thread closing")

    def readq(self, q, timeout=0.1):
        """Waits 0.1 seconds if the queue is empty, else returns None"""
        try:
            return q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None

    # ###### Methods to decode the replies #######
    def readline(self):
        """Return the content of the next ASCII message in utf-8, discarding size and type info."""
        line = self.readq(self._q01)
        if line is not None:  # queue has contents
            rsize, rtype, rmsg = line
            return str(rmsg, 'ascii')
        else:
            return None

    def readparams(self):
        """Return the next XML string as a string, discarding size and type info"""
        params = self.readq(self._q2)
        if params is not None:
            xmlstring = params[2].decode('utf-8').replace('\x00', '')
            return xmlstring
        else:
            return None

    def readdata(self):
        """Return the next data frame as either ascii (no data) or coil object """
        #print('!!!!!!!!!!\n\n\n\n doing readdata')
        data = self.readq(self._q34)
        if data is None:
            return data
        else:
            rsize, rtype, rmsg = data

        if rtype == 4:  # no data, return message
            self.no_data = True
            return str(rmsg, 'ascii')

        else:  # data frame, return coils object
            #print("###################\nTHIS IS THE RAW DATAFRAME MESSAGE", rmsg)
            return DataFrame(rawdf=rmsg)

    def readrubbish(self):
        """Return the raw message from the type=5 object (C3D object)"""
        rubbish = self.readq(self._q5)
        return rubbish


class UnexpectedEndOfStream(Exception):
    pass


def init_connection(retain_last=5, print_to=None, wave_to=None, wavehost=None, waveport=None):
    """Start the connection, set up objects to handle the soon-to-be-incoming data."""
    # create the connection object to handle communication
    global connection, replies
    connection = ClientConnection(RTC3DPacketParser)
    # replies object listens for replies and places in queues based on type
    replies = NonBlockingStreamReader(connection, last_x=retain_last)
    print(replies._b)
    # return the connection object, Non-BlockingStreamReader with NBSR.latest_df as the latest DF object
    return connection, replies


def init_connection_no_threads():
    """Start a basic connection, return the object."""
    return ClientConnection(RTC3DPacketParser)


def close_connection_no_threads(conn):
    """Close the basic connection."""
    conn.s.close()


def close_connection(conn, restart=False):
    """Close the socket, hopefully close the threads too."""
    if restart:
        conn.send_packed('BYE', 1)
        # TODO: Implement BYE as making server restart data again/close it too
    replies.alive = False  # should close threads when they complete a loop
    time.sleep(2)  # make sure all the threads could close
    conn.s.close()
    #exit()


def get_status(*args):
    return replies.readline()


def test_communication(conn, replies, *args):
    # set the version to ensure correct protocol used, test connection
    conn.send_packed("Version 1.0", 1)
    time.sleep(0.1)
    reply = replies.readline()
    return reply


def get_parameters(conn, *args):
    """Return ElementTree Element item with XML"""
    conn.send_packed("sendparameters", 1)
    reply = replies.readparams()
    while reply is None:
        reply = replies.readparams()
        time.sleep(0.1)
    return reply


def get_one_df(conn, replies, *args):
    """Wait until a df is queued and return it. Return None if the end of the data file was reached."""
    prev_df = copy.copy(replies.latest_df)
    conn.send_packed("sendcurrentframe", 1)
    # wait while the data is received from the server
    while replies.latest_df is None or (prev_df is not None and replies.latest_df == prev_df):
        #print('!!!!!!!!!!!!replies.no_data is', replies.no_data)
        if replies.no_data:
            return None
        time.sleep(0.1)
    return replies.latest_df


def get_streamed_df():
    return replies.latest_df


def get_last_streamed_dfs():
    """Wait until the last_x_dfs is populated to return this list."""
    while not len(replies.last_x_dfs) > 0:
        time.sleep(0.1)
    return replies.last_x_dfs


def start_streaming(conn, repl, *args):
    """Give the df object.
    """
    repl.last_x_dfs.clear()
    conn.send_packed("streamframes frequency:100", 1)
    print('just started streaming')


def stop_streaming(conn, repl, *args):
    conn.send_packed("streamframes stop", 1)
    return repl.last_x_dfs


def test_making_smooth_df(conn, replies):
    newest_x = get_last_streamed_dfs()
    new_df = DataFrame(fromlist=newest_x)
    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
    #print(newest_x[-1])
    print(new_df)
    print('&&&&&&&&&&&&&&&&&&&')
    print('got newest x')
    print('type of newest_x',type(newest_x))
    print('last thing in newestx',newest_x[-1])
    print('type of the averagedf',type(new_df))
    print('newcomponent', new_df.components)
    print('the actual averaged df', new_df)

def test_all_commands(conn, replies):
    conn.send_packed("Version 1.0", 1)
    for i in range(10):
        a = get_one_df(conn)
        print("This is a timestamp", a.components[0].timestamp,
              'and a location', a.components[0].coils[0].abs_loc)
        time.sleep(0.01)
    start_streaming(conn, replies)
    time.sleep(3)
    for i in range(10):
        a = replies.latest_df
        print("This is a streaming timestamp", a.components[0].timestamp,
              'and a location', a.components[0].coils[0].abs_loc)
        time.sleep(0.01)



# ########### MAIN FNS #########
def main():
    print("Running rtclient main")

    # initialise and  test connection
    # c is the connection object, r is the reply-reader
    #c, r = init_connection(print_to='../../output/testprinting.tsv', wave_to='../../output/')
    c, r = init_connection()
    print(test_communication(c, r))


    ########### NDI Wave testing ##############
    test_all_commands(c, r)
    test_making_smooth_df(c, r) # TODO: Use http://www.blender.org/api/blender_python_api_2_74_5/mathutils.html?highlight=mathutils#mathutils.Quaternion.to_exponential_map to average quaternions better!

    ############ Blender-specific testing ##########
    # get the XML parameters for inspection
   #  myxml = get_parameters(c, r)
   #  print(myxml)
   #  time.sleep(5)
   #  #b.b_make_controllers(myxml)
   #
   #  #global mydf
   #  mydf = get_one_df(c, r)
   #
   # # b.b_update_locations(df=mydf)

    c.s.close()
    return

if __name__ == "__main__":
    main()
