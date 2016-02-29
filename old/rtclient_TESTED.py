# query the RTServer protocol to get realtime data packets from NDI Wave
#using Python 2.7 because this is supported in Blender

import time
import socket
import sys

from scripts.startup import rtc3d_parser as rtp


print("Simple client script operating on {}".format(sys.version))

class ClientConnection:
    def __init__(self):
        '''Create a socket, save server params'''
            #create an AF_INET, STREAM socket (TCP) #TODO: Check this is the right socket type
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print("Socket creation failed")
            sys.exit()
        print("Standard socket created")

        #set the port
        self.HOST = '145.97.132.29'
        self.PORT = 3030 # TODO: Change to 3030, 8080 for offline testing
        #connect to  server
        self.s.connect((self.HOST, self.PORT))
        print("Client socket connected to "+self.HOST)



        ######## SIMPLE SEND AND RECEIVE #############

    def send_exact(self, message):
        '''Send exactly the message string, presumes small sized message'''
        try:
            self.s.sendall(message)
        except socket.error:
            print("Send failed")
            sys.exit()

    # def receive_exact(self):
    #     return self.s.recv()

    def receive_packet(self):
        '''Ask about the length of the packet, receive the whole packet'''
        chunks = []
        # receive the message header
        try:
            reply = self.s.recv(8)
            print("Initially received {}:\t{}".format(type(reply), reply))
            chunks.append(reply)
            rsize, rtype = rtp.get_size_type(reply)

        except:
            print("Something went wrong with receiving the message header.")
            self.close_socket()
            return

        # receive the message body
        bytesreceived = 8
        while bytesreceived < rsize:
            chunk = self.s.recv(min(int(rsize-bytesreceived), 2048)) #get either 2048 bytes or what is waiting
            if chunk==b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytesreceived += len(chunk)

        return b''.join(chunks)

        ######### FUNCTIONS TO HANDLE DIALOG (and encoding/decoding the messages) #######

    def send_rcv_plain(self, message):

        ######### SEND MESSAGE (PRESUME SMALL SIZE) ###########
        self.send_exact(message)
        #print("Message '{}' sent successfully.".format(message))
        ######### RECEIVE MESSAGE (CALCULATING SIZE) ###########
        return self.receive_packet()

    def send_rcv_packet(self, message, msgtype=1):
        '''Wrap the message in the RT packet format and recv (and unwrap) reply.'''
        #translate message into packet format
        packet = rtp.wrap_gp_packet(message, atype=msgtype)
        #print("I'm sending: "+ message)
        packet_reply = self.send_rcv_plain(packet)
        ascii_reply = rtp.unwrap_gp_packet(packet_reply)
        return ascii_reply

    def send_packet_rcv_plain(self, message):
        packet = rtp.wrap_gp_packet(message)
        #print("I'm sending: "+ message)
        self.s.sendall(packet)
        return self.receive_packet() #guess at how long the message is
        #ascii_reply = rtp.unwrap_gp_packet(packet_reply)


    def close_socket(self):
        '''close the socket'''
        self.s.close()

    def stream_data_frames(self):
        '''Append to array until keyboard interrupt, no threading.
        Output not yet parsed, just binary'''
        packet = rtp.wrap_gp_packet("streamframes", atype=1)
        self.s.sendall(packet)
        output = []
        try:
            while True:
                reply = self.receive_packet()
                print("Received: ", reply)
                output.append(reply)
        except KeyboardInterrupt:
            print("Process interrupted")
            self.send_rcv_packet("streamframes stop", msgtype=1)
            return output

if __name__=="__main__":
    c = ClientConnection()

    commandlist = [
        "version 1.0",
        "version 2.9",
        "version 1.0",
        "sendcurrentframe",
        "sendcurrentframe",
        "sendcurrentframe",
        "sendca",
        "sendparameters",
        "sendparameters all",
        "sendparameters 3d",
        "sendparameters analog",
        "sendparameters force",
        "sendparameters 6d",
        "sendparameters force 6d",

        "sendcurrentframe all",
        "sendcurrentframe 3d",
        "sendcurrentframe analog",
        "sendcurrentframe force",
        "sendcurrentframe 6d",
        "sendcurrentframe 6d analog",
        "bye"]
    streamingcommands = [
        "streamframes",
        "streamframes frequencydivisor:4 all", #25 Hz
        "streamframes frequencydivisor:4 3d",
        "streamframes frequencydivisor:4 analog",
        "streamframes frequencydivisor:10 force",
        "streamframes frequencydivisor:50 6d",
        "streamframes frequencydivisor:1 6d analog",
        "streamframes stop",

        "streamframes frequency:4 all", #25 Hz
        "streamframes frequency:4 3d",
        "streamframes frequency:4 3d analog",
        "streamframes frequency:10000 force",
        "streamframes frequency:500 6d",
        "streamframes frequency:100 6d analog",


        "bye",
    ]

    for command in commandlist:
        print("sending command:\t{}".format(command))
        bmessage = rtp.wrap_gp_packet(command)
        reply = c.send_rcv_plain(bmessage)

        print("reply:\t{}".format(reply))
        time.sleep(5)

    # reply = c.send_rcv_packet("sendcurrentframe")
    # print(reply)
    # reply = c.send_rcv_packet("sendcurrentfrae")
    # print(reply)
    # # reply = c.send_rcv_packet("sendcurrentframe")
    # # print(reply)
    # reply = c.send_rcv_packet("sendparameters")
    # print(reply)
    # reply = c.send_rcv_packet("bye")
    # print(reply)
    c.close_socket()








