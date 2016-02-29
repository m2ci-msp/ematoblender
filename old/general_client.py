# query the RTServer protocol to get realtime data packets from NDI Wave
#using Python 2.7 because this is supported in Blender

import socket, sys
print("Simple client script operating on {}".format(sys.version))

def send_to_rt_server(message):
    '''Connect to the RT server port, send the message and return the reply.'''
    #create an AF_INET, STREAM socket (TCP) #TODO: Check this is the right socket type
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
        print("Socket creation failed, error code: {} , message:  {}".format(msg[0], msg[1]))
        sys.exit()
    print("Standard socket created")

    #set the port
    HOST = 'localhost'
    PORT = 80 # TODO: Change to 3030

    #connect to  server
    s.connect((HOST, PORT))
    print("Client socket connected to ", HOST,)

    #send message and receive reply
    try:
        s.sendall(message)
    except socket.error:
        print("Send failed")
        sys.exit()
    print("Message sent successfully.")
    reply = s.recv(4096) #receive maximum bytes

    #close socket and return answer
    s.close()
    return reply


def main():
    recv = send_to_rt_server("hello world")
    print("I received:" + recv)




if __name__=="__main__":
    main()




