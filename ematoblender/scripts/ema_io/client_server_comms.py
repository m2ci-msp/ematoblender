__author__ = 'Kristy'

############## PROTOCOL FOR COMMUNICATION (SETTING UP, SENDING/RECEIVING) BETWEEN CLIENT AND SERVER #############
import socket
import sys

from .rtc3d_parser import BasicProtocol


class BasicConnection(object):
    """ Abstract super class for the connection between client and server.
     Handles sending and receiving data, calling on the protocol for decoding from bytes."""

    def __init__(self, *args):
        # ONLY COMMUNICATIONS PROTOCOL SUPPORTED IS RTC3D
        self.protocol = BasicProtocol

    ############ SIMPLE SEND AND RECEIVE ###########
    def send_verbatim(self, message):
        """ Send exactly the message string, presumes small sized message. """
        try:
            self.s.sendall(message)
        except socket.error:
            print("Sending {} failed".format(message))
            return None

    def send_packed(self, message, status):
        outbound_packet = self.protocol.pack_wrapper(message, atype=status)
        print("I'm sending: {}".format(str(message[:60])+'...'))
        self.send_verbatim(outbound_packet)

    def receive_verbatim(self):
        '''Ask about the length of the packet, receive the whole packet.
        Allow extra 8 bytes to check for another packet header.'''
        h = self.protocol.HEADER_LEN
        chunks = []; bytesreceived = 0; reply = None
        # receive the message header
        try:
            reply = self.s.recv(h); chunks.append(reply)
        except socket.timeout:
            return None
        except BlockingIOError:
            return None
        except Exception as e:
            print("Some non-timeout exception occurred: on object {}".format(type(self)), e)
            #import traceback
            #print(traceback.print_tb())
            self.s.close()
            return None
        finally:
            rsize, rtype = self.protocol.get_size_type(reply)
            bytesreceived = h
        # receive the message body
        while bytesreceived < rsize:
            chunk = self.s.recv(min(int(rsize-bytesreceived), 2048))  # get either 2048 bytes or what is waiting+8
            if chunk==b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytesreceived += len(chunk)
        return b''.join(chunks[:rsize])

    ######### FUNCTIONS TO HANDLE DIALOG (and encoding/decoding the messages) #######

    def send_rcv_verbatim(self, message, maxreplies=1):

        ######### SEND MESSAGE (PRESUME SMALL SIZE) ###########
        print("Now sending message: {}".format(message), file=sys.stderr)
        self.send_verbatim(message)
        ######### RECEIVE MESSAGE (CALCULATING SIZE) ###########
        responses = []
        for reply in range(maxreplies):
            response = self.receive_verbatim()
            print("Verbatim reply received: {}".format(response), file=sys.stderr)
            if response is not None:
                responses.append(response)
        return responses

    def send_rcv_packet(self, message, msgtype=1, maxreplies=1):
        """ Wrap the message in the RT packet format and recv (and unwrap) reply. """
        #translate message into packet format
        outbound_packet = self.protocol.pack_wrapper(message, atype=msgtype)
        print("I'm sending: {}".format(message[:50]))
        inbound_packets = self.send_rcv_verbatim(outbound_packet, maxreplies=maxreplies)
        ascii_replies = [self.protocol.unpack_wrapper(inbound_packet) for inbound_packet in inbound_packets]
        print("ASCII reply received: {}\n\n".format(str(ascii_replies)), file=sys.stderr)
        return ascii_replies


class ServerConnection(BasicConnection):

    def __init__(self,  mysocket, protocol):
        """Allow the self.funct access to the server-internal functions"""
        super().__init__(protocol)
        self.s = mysocket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


class ClientConnection(BasicConnection):
    """ Connection object through which commands are sent.
    Inherit methods from BasicConnection"""

    def __init__(self, myprotocol):
        """ Create a socket, save server params, using AF_INET SOCK_STREAM socket. """
        # set the protocol and basic communication behaviour
        super().__init__(myprotocol)
        try:  # create the socket
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print("Socket creation failed")
            sys.exit()
        print("Standard socket created", self.s)

        #set the port
        from scripts.ema_shared.properties import waveserver_host, waveserver_port
        self.HOST = waveserver_host
        self.PORT = waveserver_port

        # set the TIME_WAIT so that the socket can be reused
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #connect to server
        print('Connecting socket to address:', (self.HOST, self.PORT))
        self.s.connect((self.HOST, self.PORT))
        self.s.settimeout(5)  # presume no delay sending message
        print("Client socket connected to "+self.HOST)
