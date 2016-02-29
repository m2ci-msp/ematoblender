__author__ = 'Kristy'


######### methods used for unwrapping server comms in order

# def receive_all_data(reqhandler):
#     '''Read from the header how much data is being communicated, return this as bytes.'''
#     header = reqhandler.request.recv(8)
#     size, atype = ClassicPacket.get_size_type(header)
#     body = reqhandler.request.recv(size)
#     return header+body
# #
# def unwrap_gp_packet(packeddata):
#     '''Unwrap communications from the RT server protocol
#     Return tuple with size, type, ASCII general_message'''
#     print("The packed data looks so", packeddata)
#     commlen = len(packeddata)
#     if commlen > 0:
#         #size, atype = get_size_type(packeddata)
#         size, atype = struct.unpack('>I I', packeddata[:8])
#         body = packeddata[8:]
#
#         # Handle the message differently based on the message content (deduced from type)
#         if atype == 3: # rest of message is a data frame
#             compcount, components = unwrap_df_packet(body)
#
#             # TODO: Make these into objects that we can query
#             # componentsize, componenttype, framenumber, timestamp,
#             expanded_cdf = [[c[0], c[1], c[2], c[3], unwrap_cdf_packet(c[2],c[4])] for c in components]
#
#             return size, atype, compcount, expanded_cdf
#
#         elif atype==4: # There is no message
#             return size, atype, ''
#
#         elif atype==5: # return a complete c3d file
#             raise NotImplementedError
#
#         else: # Type is 0, 1 or 2, message is in ascii (error or xml)
#             return int(size), int(atype), struct.unpack('> {}s'.format(len(body)), body)
#             # previously: return int(size), int(atype), str(body.decode('ascii'))
#
#
# def unwrap_df_packet(packeddf):
#     '''Unwrap one data frame from the Wave data frame format (described in documentation chapter 7'''
#     compcount = struct.unpack('> I', packeddf[:4])[0] #number of data components in data packet
#     pos = 4
#     # for each component in the general data frame
#     components = []
#     for x in range(compcount):
#         # get component size
#         compsize = struct.unpack_from('>I', packeddf, pos)[0]
#         pos +=4
#         # get component type (4), frame number (4), TimeStamp (8), ComponentData (size-20)
#         ctype, fn, ts, compdata = struct.unpack_from('> I I Q {}s'.format(compsize - 20), packeddf, offset=pos)
#         pos += compsize
#         components.append([compsize, ctype, ts, unwrap_cdf_packet(ctype, compdata)])
#     return compcount, components

###### methods to unpack specific kinds of component data frames
#
# def unpack_integers(num, data):
#     '''Unpack 3d/analog/force component data frames
#     Num describes the number of fields (integers) to be unpacked'''
#     return struct.unpack('> {}I'.format(str(num)), data)
#
# def unpack_integers_per_6d_header(num, data):
#     '''Read the first integer (i) then unpack num integers i times.
#     Used for the 6d data component.'''
#     output = [] #7 floats expected
#     iters = struct.unpack('>I', data[:4]) #toolcount
#     output.append(iters)
#     s = struct.Struct('> {}f I'.format(str(num)))
#     for i in iters:
#         output.append(s.unpack_from(data, offset = 4 + i*s.calcsize))
#        # output.append(struct.unpack_from('> {}f I'.format(str(num)), data, offset = 4+i*num) # deprecated, maybe offset is wrong
#     return output
#
# def unpack_integers_per_event_header(num, data):
#     '''Read first integer for number of events, iterate from there.'''
#     output = []
#     iters = struct.unpack('>I', data[:4])
#     output.append(iters)
#     for i in iters:
#         output.append(struct.unpack_from('> {}I'.format(str(num)), data, offset = 4 + i*num))
# #
# # component data frame format string dictionary
# cfs_dict ={1: (unpack_integers, 4),        # 3D values
#            2: (unpack_integers, 2),              # Analog values
#            3: (unpack_integers, 7),    # Force values (7 x float and an integer per event)
#            4: (unpack_integers_per_6d_header, 7), # 6D values
#            5: (unpack_integers_per_event_header, 4), # Event values (4 x int per event)
#            }
#         #TODO: handle Event component types
#
#
# def unwrap_cdf_packet(componenttype, packeddata):
#     '''Unwrap the Wave component data frame types.'''
#     # based on the component type specified\
#     print("Object decoded is of len", len(packeddata))
#     fn, arg = cfs_dict[componenttype]
#     print(fn, arg)
#     return fn(arg, packeddata)



##### Methods used to wrap server commands
#
#
# def wrap_cdf_packet(somedata):
#     '''Wrap the component data packet (different for each component data type)'''
#     raise NotImplementedError
#
# def wrap_df_packet(somedata):
#     '''Wrap a message of a data frame into the wave format, differs for error vs command vs xml etc'''
#     raise NotImplementedError
#
#
# def wrap_gp_packet(command, atype=1):
#     '''Wrap data with the header for general-purpose data packets
#     Returns the byte-packed packet'''
#     size = len(command) + 8
#     command = bytes(command, 'ascii')
#     #construct the struct, big endian, 4 byte size field, 4 byte type field, rest of packet
#     s = struct.Struct('> I I {}s'.format(str(len(command))))
#     #pack the value into the struct)
#     return s.pack(size, atype, command) # make command type(bytes)


    # return int.from_bytes(mybytes[:4], byteorder='big'), \
    #                int.from_bytes(mybytes[4:8], byteorder='big')




        # Make a dictionary of parameters - information about the server that can be queried and returned XML-like.

        Server = {'Name': '',
               # 'Port': server_object.server_address[1],
              #  'IPadd': server_object.server_address[0],
                'Stats': {
                'FramesSent':0,
                'FramesPerSec':0
                        }
                 }
        self.RT_Parameters = {'Version': 0,
                              'General': { 'Server': Server },
                              'The_3D': {}, # Information about the 3D markers
                              'The_6D': {}, # Information about 6D markers
                              'Analog': {},
                              'Force' : {},
                              'Events': {},

                             } #TODO: Make an attempt at populating these parameters
