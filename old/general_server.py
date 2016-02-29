__author__ = 'Kristy'
import socket
import sys
from thread import *
print("Simple server script operating on {}".format(sys.version))


#set port (Wave Front listens at 3030, First Principles listens at 3020)
HOST = 'localhost'
PORT = 80 # TODO: Change to 3030

#create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TODO: Get real socket params
print("Socket created")

#bind socket to port
try:
    s.bind((HOST, PORT))
except socket.error, msg:
    print("Bind failed. Error code: {}, Message: {}".format(str(msg[0]), str(msg[1])))
    sys.exit()
print("Socket bind complete")

#listen for and accept connections
s.listen(10) #10 connections accepted
print("Socket now listening")

def clientthread(conn):
    '''Function for handling connections'''

    #infinite loop so that server does not stop listening
    while True:
        #talk with the client
        data = conn.recv(1024) #receive n characters
        reply = data.upper()
        if not data:
            break
        print("I received: "+ data)
        conn.sendall(reply)
    #close the connection
    conn.close()

#loop to keep listening for connections
while True:
    conn, addr = s.accept()
    print("Connected with " + addr[0] + ":" + str(addr[1]))

    #start new thread to handle the client that connected
    clientthread(conn)
    #start_new_thread(clientthread, (conn,))

s.close()

