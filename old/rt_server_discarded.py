__author__ = 'Kristy'


# class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
#     pass



 ############ COMMAND THREAD ############

        # define the send/receive functions and link to this socket



        # while True:
        #     # poll for single command
        #     command = queries.read_single_command()
        #     if command is not None: fn_name, *args = command
        #     # poll for streaming command
        #     else:
        #         command = queries.read_stream_commmand()
        #         if command is not None: fn_name, *args = command
        #         else:  continue

            # when command is found
        #
        # fn_name, *args = request
        #
        # try:
        #     method = getattr(myserver_functionality, fn_name)
        # except AttributeError:
        #     print("The invalid command: `{}` was issued.".format(command))
        #     reply = "Error-Unknown command: {}".format(str(text))
        #     conn.send_packed(reply, status=0)







            # # TODO: Implement a queue here that will be polled to return any other streaming data
            # #receive and unwrap the data; prev. self.data = self.request.recv(2048); self.data = rtp.receive_all_data(self) # get all data based on header
            # self.data =  conn.receive_verbatim()
            # print("Got a request: ", self.data)
            #
            # ############ disconnect messages ##########
            # if self.data == b'' or self.data is None:
            #     reply = "Disconnecting."; print(reply)
            #     conn.send_packed(reply, 1)
            #     myserver_functionality.bye()
            #     break # no data received, disconnect socket
            #
            # # server takes all data (hopefully, small buffer, decodes)
            # size, atype, text, *otherargs = conn.protocol.unpack_wrapper(self.data)
            # print("Message received:", size, atype, text)
            # text = text.decode('UTF-8').rstrip(' \t\n\r\0')
            #
            #
            # ############ handle messages of wrong type ##########
            # if atype != 1:
            #     reply = "Error-Wrong command status: {}".format(str(atype))
            #     conn.send_packed(reply, 0)
            #     continue
            #
            # # text is a command string, now sever responds
            # command = text.lower().split(' ')
            # fn_name, commargs = command[0], command[1:]
            # print("Command issued is: ", fn_name, commargs)
            #
            # # handle streaming at server level because of constant comms
            # if fn_name.startswith("streamframes"):
            #     conn.handle_streaming(commargs)
            #
            # else:
            # # handle all discrete commands
            #     try:
            #         # check if the command is described for the modality being queried
            #         method = getattr(myserver_functionality, fn_name)
            #     except Exception as e:
            #     ########## command is not defined #########
            #         print("Problem:", e)
            #         print("An invalid command was issued.")
            #         reply = "Error-Unknown command: {}".format(str(text))
            #         conn.send_packed(reply, status=0)
            #         continue
            #     #print('method', method)

                # command is defined
        # try:
        #     ######### reply (if available), success string ########
        #     status_reply, method_reply = method(*commargs, handler=self)
        #     print("The emulated response is: {},{}".format(status_reply, method_reply))
        #
        #     # reply with the information requested
        #     if status_reply == 2 or status_reply==3: # reply with data
        #         conn.send_packed(method_reply, status_reply)
        #         conn.send_packed('OK-'+text, 1) # new addition based on real server behaviour
        #     elif status_reply== 0: # error, do not send success code
        #         conn.send_packed(method_reply, status_reply)
        #     else: # Nothing happened or weird data returned. Send success string anyway.
        #         conn.send_packed('OK-'+text, 1) # new addition based on real server behaviour
        #
        # except Exception as e:
        #     ######## error string ###########
        #     print("Problem: ",e)
        #     print(sys.exc_info()[0])
        #     print(traceback.format_exc())
        #     print("There was an error executing the desired function")
        #     status_reply, method_reply = 0, "Error - Execution error"
        #     conn.send_packed(method_reply, status_reply)

