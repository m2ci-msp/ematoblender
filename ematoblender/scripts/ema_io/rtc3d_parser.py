# -*- coding: utf-8 -*-
__author__ = 'Kristy'

"""
Functions to read and write the data packets received and sent by the RT server, using the RTC3D Protocol.
> denotes Big Endian, I is a standard 4-byte integer, ns is n characters of string,  calc'd from len of message - 8

Wave messages are as follows:
- general purpose data packet (type 0 = error, 1 = command/success, 2 = xml, 3 = dataframe, 4 = no data, 5 = c3d file)
|  - (general) data frame (contains n components)
|  |___- component data frame (3D, Analog, Force, 6D, Event)
|______________________________________________________________________________________________________________________

Functions to handle the RT server protocol are described in the PDF and coded in rtserver_emulate_func.py.
    Contain size, type and perhaps commands, have the following restrictions:
    *    Commands contain no space characters
    *    Parameters are space-separated
    *    Commands and parameters are case insensitive
"""

# decode bytes -> ascii -> unicode
import struct
import copy
from ematoblender.scripts.ema_shared.general_maths import average_quaternions


class BasicProtocol(object):
    """
    The Basic Protocol for the wrapping of messages, according to Version 1.0 of the RTC3D Protocol.
    This class contains static methods to pack and unpack the outermost wrapper
    for header (which contains the size and and type(integer) of the message).
    The remainder is the message body.
    Instances have the attributes:
     - rtype (reply type, as defined in RTC3D protocol,
        0=error, 1=success string, 2=XML, 3=dataframe, 4=no data, 5=C3D file)
    - df (data frame object (bytes if C3D file, DataFrame class if body is packed bytes)
    - size (integer, length of the message body)
    """

    HEADER_LEN = 8

    @staticmethod
    def unpack_wrapper(message):
        """ Gives size, type, message of the packet."""
        if message is None or len(message) == 0:
            return None
        else:
            #print("input message was {}".format(message))
            return struct.unpack('> I I {}s'.format(str(len(message)-BasicProtocol.HEADER_LEN)), message)

    @classmethod
    def pack_wrapper(cls, command, atype=1):
        """ Wrap data with the header for general-purpose data packets with ASCII message,
        Returns the byte-packed packet."""
        if type(command) != bytes:
            command = bytes(command, 'ascii')
        return struct.pack('> I I {}s'.format(str(len(command))), len(command)+BasicProtocol.HEADER_LEN, atype, command)

    @classmethod
    def get_size_type(cls, mybytes):
        """ Take the first 8 bytes of the message, return integers of size and type."""
        if mybytes is None or len(mybytes) == 0:
            return 0, 0
        else:
            return struct.unpack('> I I', mybytes[:BasicProtocol.HEADER_LEN])

    def __init__(self, rawdf=None):
        """
        Initialise a data packet according to the RTC3D protocol.
        If rawdf is a bytestring, then it is handled according to the message type.
        Else hold an empty BasicProtocol instance.
        """
        self.packet_type = 0  # begin as error type before filling
        self.df = ''
        self.body_size = 0

        if rawdf is not None:
            self.body_size, self.packet_type, rmsg = self.unpack_wrapper(rawdf)
            if self.packet_type in [0, 1, 2, 4]:
                self.df = str(rmsg, 'ascii')
            elif self.packet_type == 5:
                self.df = rmsg
            elif self.packet_type == 3:
                self.df = DataFrame(rawdf=rmsg)
            else:
                pass

    def __str__(self):
        return "{}".format(self.df)


class DataFrame(BasicProtocol):
    """Contains one data frame transmission.
    """
    # TODO: Frameid not being added to streaming data

    def __init__(self, rawdf=None, components=None, fromlist=None):
        #print('***** Making df')
        self.smoothed = False
        if components is not None: # initialised to write
            self.components = components

        elif rawdf is not None: # initialised to read
            self.components = self.unpack_df_to_components(rawdf)

        elif fromlist is not None:  # initialise from a list of other dataframes, averaging them
            self.smoothed = True
            self.components = [Component()]
            allcoils = zip(*[f.give_coils() for f in fromlist])
            for coil_over_alldfs in allcoils:
                #print('coil_oer alldfs', coil_over_alldfs)
                new_loc = []
                # iterate over x, y, z for the coil
                for i in range(3): # average the location readings over the dfs
                    val = sum(thiscoil.abs_loc[i] for thiscoil in coil_over_alldfs)/len(coil_over_alldfs)
                    new_loc.append(val)
                new_rot = []
                quaternion_list = [thiscoil.abs_rot for thiscoil in coil_over_alldfs]
                new_rot  = average_quaternions(quaternion_list)

                # old quaternion averaging procedure: average each individual value
                #old for i in range(4): # average the quaternion values over the dfs
                #old    val = sum(thiscoil.abs_rot[i] for thiscoil in coil_over_alldfs)/len(coil_over_alldfs)
                # old    new_rot.append(val)
                self.components[0].coils.append(Coil(loc_dict=list(new_rot)+new_loc))
                self.components[0].timestamp = fromlist[-1].components[0].timestamp

        else:
            pass # just make a really rudimentary frame with nothing
            #raise ValueError
    def __str__(self):
        return " dataframe with components: \n{}".format([[y.__dict__ for y in x.coils] for x in self.components])

    @staticmethod
    def unpack_df_to_components(mybytes):
       # print("first four bytes are", bytes[:4])
        n_data_components = struct.unpack('>I', mybytes[:4])[0]
       # print("there are x components", n_data_components)
        components = []
        pos = 4
        for i in range(n_data_components):  # for each component
            this_size = struct.unpack_from('>I', mybytes, offset = pos)[0]  # get component size
            components.append(Component(componentbytes=mybytes[pos:pos+this_size]))
            pos += this_size
        return components # list of Component objects

    def pack_components_to_df(self):
        """Pack up to the second-to-top level."""
      #  print("packing {} components".format(len(self.components)))
        body = struct.pack('>I', len(self.components)) # componentcount
      #  print("packing {} components".format(len(self.components)))
        for component in self.components:
      #      print('adding component', component.pack_component())
            body += component.pack_component()
        return body

    def give_coils(self):
        """Return a list of the coil objects in a dataframe."""
        output = []
       # print('this is df.componentsn', self.components)
        for component in self.components:
            #print('this is a component', component)
            for coil in component.coils:
                output.append(coil)
        return output

    def to_tsv(self, relative_timestamp_to=0, closest_sound_sample=(0)):
        """Return a tab-separated string with the coil data in the wave tsv order"""
        outstring = ''
        if len(self.components)== 0 or self.give_coils() is None:
            print('nothing in df')
            return ''  # no response when no data present
        else:
            # fields time (based on wave frames), measid, wavid
            outstring+='{}\t{}\t{}\t'.format(str(self.components[0].timestamp-relative_timestamp_to), str(self.components[0].frame_number), str(closest_sound_sample[0]))
            for i, c in enumerate(self.give_coils()):
                outstring+='{}\t{}\t'.format('Sensor'+str(i), '55')
                outstring+='{}\t{}\t{}\t{}\t'.format(c.abs_rot[0], c.abs_rot[1], c.abs_rot[2], c.abs_rot[3]) # rotational info
                outstring+='{}\t{}\t{}\t'.format(c.abs_loc[0], c.abs_loc[1], c.abs_loc[2],)
            outstring+='\n'
        #print('testing outstring', outstring)
        return outstring

    def give_timestamp_secs(self):
        """Return the df timestamp in seconds.
        RTC3D protocol timestamps are in microseconds by default."""
        try:
             micro_ts = self.components[0].timestamp
             ts = micro_ts * 0.000001  # old/ 1000000
        except AttributeError:
            ts = None
        return ts

        #old: return hasattr(self.components[0], 'timestamp', None)


class Component(DataFrame):
    """ A component on the wave machine. Child objects are Coils.
    Rawcomponentbytes must follow the WAVE RTC3D protocol.
   """
    COMPONENT_HEADER = '> 3I Q'
    HEADER_LEN = struct.calcsize(COMPONENT_HEADER)
    # struct that encodes coil data (dependent upon component type)
    struct_for_componenttype = {1:'> 3f I', # 3d
                                2:'> I',    # Analog
                                3:'> 6f',   # Force
                                4:'> 7f I', # 6D
                                5:'> 4I',}  # Events

    def __init__(self,  componentbytes=None, fileparser=None,):
        """Make an object representing a component of the Wave (eg the Wave sensors)"""

        if componentbytes is not None:  # initialised from bytes
            size, self.comp_type, self.frame_number, self.timestamp = struct.unpack(self.COMPONENT_HEADER, componentbytes[:20])
            self.coils = self.unpack_coils(componentbytes[20:])

        elif fileparser is not None:      # initialised from marker information (name and channel)
            # 3d or 6d, depends on the number of channels
            #  self.comp_type =
            self.frame_number = fileparser.motion_lines_read
            if hasattr(fileparser, 'latest_timestamp'):  # if timestamp can be directly read from tsv, use this
                self.timestamp = fileparser.latest_timestamp
            else:  # else calculate this from the number of frames read and the time they are streamed at
                self.timestamp = int(self.frame_number * fileparser.frame_time)
            print("timestamp:", self.timestamp)

            self.coils = self.create_coils(n=fileparser.min_channels, dimensions=fileparser.min_dimensions,
                                           mappings=fileparser.mappings, marker_channels=fileparser.marker_channels)

        else:
            self.coils = []
            #raise ValueError            # No values given

    def create_coils(self, dimensions=3, mappings=None, marker_channels=None, n=1):
        """Build coil objects (called within Component init).
        Return a list of coil objects with the appropriate mappings."""
        from ematoblender.scripts.ema_io.ema_staticserver.mocap_file_parser import MocapParent

        # data frame component type is 3d or 6d, based on the minimum number of channels sent
        self.comp_type = 1 if dimensions < 5 else 4 # dfct, 3D or 6D

        # parse the channels into location/rotation (quaternion vals) in the Wave order
        if mappings is not None:
            return [Coil(dfct=self.comp_type, mapping=mappings) for x in range(n)]
        else:
            mappings = [MocapParent.order_measurements_as_wave(c, nchannels=dimensions) for c in marker_channels]
            return [Coil(dfct=self.comp_type, mapping=mappings) for x in range(n)]

    def __str__(self):
        return "Component object with timestamp {} and coils: {}".format(str(self.give_timestamp_secs()), str(self.coils))

    def unpack_coils(self, coilbytes):
        """Make n coil objects, based on the coil data given with this component."""
        coils = []
        toolcount = int(struct.unpack('>I', coilbytes[:4])[0])
        coilstruct = Coil.struct_for_componenttype[self.comp_type]

        toolsforeseen = (len(coilbytes)-4) / struct.calcsize(coilstruct)
        for vals in struct.iter_unpack(coilstruct, coilbytes[4:]):
            # interpret the values according to the component type
            coils.append(Coil(loc_dict=vals, dfct=self.comp_type))
        return coils

    def pack_component(self):
        """Pack the component for the data frame type"""
        body = struct.pack('>I', len(self.coils))
        for coil in self.coils:
       #     print("The component type is", self.comp_type)
       #     print("Packing into struct like ", self.struct_for_componenttype[self.comp_type])
       #     print("Packing content", *coil.pack_coil(comptype=self.comp_type))
            body += struct.pack(self.struct_for_componenttype[self.comp_type], *coil.pack_coil(comptype=self.comp_type))
        size = len(body)+self.HEADER_LEN
        header = size, self.comp_type, self.frame_number, self.timestamp
      #  print("struct is", self.COMPONENT_HEADER)
        #print("content is", *header)
        return struct.pack(self.COMPONENT_HEADER, *header) + body


class Coil(Component):
    '''Contains the measurement data for a component'''
    def __init__(self, loc_dict=None, dfct=4, mapping=None):
        """dfct is the 'data frame component type' as defined by the RTC3D protocol."""
        #print("initialising a coil")
        self.mapping = mapping
        self.dfct = dfct
        if loc_dict is not None:
           # print("I am going to set not None location values", len(loc_list))
            self.set_args_to_vars(loc_dict, mapping=self.mapping)
        self.error = 0
        self.reliability = 0

        # define attributes for the head- and bite-plate-corrected locations
        self.ref_loc = None
        self.bp_corr_loc = None

    def __str__(self):
        return "Coil object with attrs: {}".format(str(self.__dir__()))

    def set_args_to_vars(self, loclist, mapping=None):
        """Set arguments to variables, using mapping to rearrange the list so it fits q0, qx, qy, qz, x, y, z"""
        #print("setting variables for coils", loclist)
        #reorder arguments to wave order
        if mapping is not None:
            loclist = [loclist[x] if x is not None and x < len(loclist) else None
                       for x in mapping] + [None for y in range(5)] # add 5 extra nones in case values too few
        # elif self.mappings is not None:
        #     loclist = [loclist[x] if x is not None and x < len(loclist) else None
        #                for x in self.mappings] + [None for y in range(5)] # add 5 extra nones in case values too few
        else:
            # make no changes to the ordering
            pass

        #print('now my locllist is', loclist)
        q0, qx, qy, qz, x, y, z, *_ = loclist

        if self.dfct == 1:  # 3D values
            self.reliability = 0
            self.abs_loc = (x, y, z)

        elif self.dfct == 4: # 6D values # TODO: Catching quaternions because q0 is none
            import math
            if q0 is None or q0 < 0: # Euler angles are given, convert to quaternion:
                if qx is None:  # Actually no angles available
                    q0, qx, qy, qz = 0.0, 0.0, 0.0, 0.0

                else:

                    # TODO: This presumes the angle application order XYZ # TODO: Check source
                    # TODO: Source is http://www.euclideanspace.com/maths/geometry/rotations/conversions/eulerToQuaternion/

                    c1, c2, c3 = [math.cos(math.radians(i)/2) for i in [z, y, x]] # z is yaw, y is pitch, x is roll
                    s1, s2, s3 = [math.sin(math.radians(i)/2) for i in [z, y, x]] # z is yaw, y is pitch, x is roll

                    # convert euler rotation angles to quaternion
                    q0 = c1*c2*c3 - s1*s2*s3
                    qx = s1*s2*c3 + c1*c2*s3
                    qy = s1*c2*c3 + c1*s2*s3
                    qz = c1*s2*c3 - s1*c2*s3

            # pack the values
            self.abs_rot = (q0, qx, qy, qz)
            self.abs_loc = (x, y, z)
            if self.abs_loc == (None, None, None):
                self.abs_loc = (0.0, 0.0, 0.0)
            self.error = 0
            #print(self.abs_loc, self.abs_rot)

        else:   # elif dfct == 2 or dfct == 3 or dfct == 5:
            print("Analog, Force and Event data frame component types not implemented.")
            raise NotImplementedError

    def pack_coil(self, comptype=None):
        """Return values in order"""
        comptype = self.dfct if comptype is None else comptype
        #print('abs_loc is', self.abs_loc)
        x,y,z = self.abs_loc
        if comptype == 1: # 3D
            return x, y, z, self.reliability
        elif comptype == 4: # 6D
            q0, qx, qy, qz= self.abs_rot
            return q0, qx, qy, qz, x, y, z, self.error


if __name__ == "__main__":
    pass


