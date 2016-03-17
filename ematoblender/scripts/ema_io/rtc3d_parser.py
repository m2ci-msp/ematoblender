# -*- coding: utf-8 -*-
__author__ = 'Kristy'

"""
Functions to read and write the binary data packets received and sent by the RT server.
Currently only supports using the RTC3D Protocol,
in these structs > denotes Big Endian, I is a standard 4-byte integer, ns is n characters of string,
calc'd from len of message - 8

Wave messages are as follows:
- general purpose data packet (type 0 = error, 1 = command/success, 2 = xml, 3 = dataframe, 4 = no data, 5 = c3d file)
|  - (general) data frame (contains n components)
   |___- component data frame (3D, Analog, Force, 6D, Event)
        |_________________ Coils (3D or 6D are of interest)


Functions to handle the RT server protocol are described in the PDF and coded in rtserver_emulate_func.py.
    Contain size, type and perhaps commands, have the following restrictions:
    *    Commands contain no space characters
    *    Parameters are space-separated
    *    Commands and parameters are case insensitive
"""

# decode bytes -> ascii -> unicode
import copy
from ematoblender.scripts.ema_shared.general_maths import average_quaternions


import struct


class BasePacketParser(object):
    """Unused. Of potential use in future as a base class if communicating with Carstens machines."""
    pass


class RTC3DPacketParser(BasePacketParser):
    """
    The Basic Protocol for the wrapping of messages, according to Version 1.0 of the RTC3D Protocol.
    This class contains static methods to pack and unpack the outermost wrapper
    for header (which contains the size and and type(integer) of the message).
    The remainder is the message body.
    """

    PACKET_STRUCT = '> I I {}s'
    HEADER_STRUCT = '> I I'
    HEADER_LEN = struct.calcsize(HEADER_STRUCT)

    GET_INNER_BUILDER = lambda: MessageBuilder

    @classmethod
    def get_size_type(cls, mybytes):
        """ Take the first 8 bytes of the message, return integers of size and type."""
        if mybytes is None or len(mybytes) == 0:
            return 0, 0
        else:
            return struct.unpack(cls.HEADER_STRUCT, mybytes[:cls.HEADER_LEN])

    @classmethod
    def unpack_outer(cls, message):
        """ Gives size, type, message of the packet."""
        if message is None or len(message) == 0:
            return None
        else:
            #print("input message was {}".format(message))
            print('unpackign with string', cls.PACKET_STRUCT.format(
                str(len(message)-cls.HEADER_LEN)))
            return struct.unpack(cls.PACKET_STRUCT.format(
                str(len(message)-cls.HEADER_LEN)), message)

    @classmethod
    def unpack_all(cls, mbytes):
        """Unpack the entire bytestring, returning the relevant object"""
        size, atype, msgbytes = cls.unpack_outer(mbytes)
        print('s, t, m', size, atype, msgbytes)
        print(cls.GET_INNER_BUILDER())
        return cls.GET_INNER_BUILDER().unpack_all(msgbytes, atype)

    @classmethod
    def pack_outer(cls, command, atype):
        """ Wrap data with the header for general-purpose data packets with ASCII message,
        Returns the byte-packed packet.
        """
        if type(command) != bytes:
            command = bytes(command, 'ascii')
        print('headerlen, commandlen', cls.HEADER_LEN, len(command))
        print('packing with string', cls.PACKET_STRUCT.format(str(len(command))))
        return struct.pack(cls.PACKET_STRUCT.format(str(len(command))),
                           len(command)+cls.HEADER_LEN, atype, command)

    @classmethod
    def pack_all(cls, messageobj):
        """Recursively pack the object to a bytestring"""
        return cls.pack_outer(messageobj.pack_all(), messageobj.message_type)

    @classmethod
    def unpack_wrapper(cls, *args, **kwargs):
        return cls.unpack_outer(*args, **kwargs)

    @classmethod
    def pack_wrapper(cls, *args, **kwargs):
        return cls.pack_outer(*args, **kwargs)


class MessageBuilder(object):
    """Give a bytestring to build the relevant message object (either DataFrame or AsciiMessage)"""

    ASCII_CODES = [0, 1, 2, 4]
    DATAFRAME_CODES = [3]
    BINARY_CODE = [5]
    GET_RESULT_CLASS = lambda: Message

    @classmethod
    def unpack_all(cls, mbytes, mtype):
        """Return a message instance for the given bytestring"""
        if mtype in cls.ASCII_CODES:
            return AsciiMessage(mbytes, mtype)

        elif mtype in cls.DATAFRAME_CODES:
            return DataFrame(rawdf=mbytes)

        else:
            print('Application does not support message type {}'.format(mtype))
            return None

    @staticmethod
    def pack_all(messageobj):
        """Return a bytestring for the given message"""
        raise NotImplementedError

    @staticmethod
    def average_dataframes(dflist):
        """Average all of the floating point values in the input dataframes, return a dataframe"""
        # check if all of the dataframes have the same attribute structure
        n = len(dflist)
        if n > 1 and all(dflist[0].check_same_structure(dflist[n]) for n in range(1, n)):

            meanobj = DataFrame()
            meanobj.__dict__ = copy.deepcopy(dflist[-1].__dict__)
            meanobj.smoothed = True

            # update the components' coils, keep them the same
            newcoils = meanobj.give_coils()

            smoothedcoils = [CoilBuilder.average(cs) for cs in zip(*[d.give_coils() for d in dflist])]

            for n, s in zip(newcoils, smoothedcoils):
                n = s  # use list mutability to set new values to soothed
            return meanobj
        else:
            raise KeyError("The DataFrame objects you are trying to average have a different structure")


class JSONBuilder(MessageBuilder):

    @staticmethod
    def unpack_wrapper(mbytes):
        """dataframe from the JSON string"""
        pass

    @staticmethod
    def pack_wrapper(dataframe):
        """Return a JSON string for the dataframe"""
        pass


class Message(object):
    """
    Data Frame base class.
    """
    GET_BUILDER_CLASS = lambda: MessageBuilder
    pass


class DataFrame(Message):
    """Class representing dataframe objects.
    Has attributes:
    - components
    """
    message_type = 3
    GET_INNER_BUILDER = lambda: ComponentBuilder

    def __init__(self, rawdf=None, components=None, fromlist=None):
        """Initialise Data Frame object from bytestring.
        Make some empty object if no string given.
        """
        self.smoothed = None


        if rawdf is not None and len(rawdf) > 0:
            self.smoothed = False
            self.components = self.__class__.GET_INNER_BUILDER().unpack(rawdf)

        if components is not None:
            self.components = components

        if fromlist is not None:
            self = self.__class__.GET_BUILDER_CLASS().average_dataframes(fromlist)


    def pack_all(self):
        """Return (in bytes) component count, then each component's bytestring"""
        return self.__class__.GET_INNER_BUILDER().pack(self.components)

    def give_coils(self):
        """Return a list of the coil objects in a dataframe."""
        print('returning ALL coils')
        return [coil for comp in self.components for coil in comp.coils]

    def __str__(self):
        return "Data frame with {} components;".format(len(self.components))+str(self.components[0])

    def __eq__(self, other):
        if self.pack_all() == other.pack_all() and self.components[0].coils == other.components[0].coils:
            return True
        else:
            return False

    def check_same_structure(self, other):
        """Check that there is the same number of coils and they have the same attributes"""
        if len(self.components) == len(other.components) \
                and all(c.__dict__.keys() == oc.__dict__.keys() \
                for n in range(len(self.components)) \
                for (c, oc) in zip(self.components[n].give_coils(), other.components[n].give_coils())
                ):
            print('Objects are the same')
            return True
        else:
            print('Objects are not the same')
            return False

    def to_tsv(self, relative_timestamp_to=0, closest_sound_sample=[0]):
        """Return a tab-separated string with the coil data in the wave tsv order"""
        outstring = ''
        if len(self.components)== 0 or len(self.give_coils()) == 0:
            print('No content in the data frame to write.')
            return ''
        else:
            # fields time (based on wave frames), measid, wavid
            outstring+='{}\t{}\t{}\t'.format(str(int(self.components[0].timestamp)-relative_timestamp_to),
                                             str(self.components[0].frame_number), str(closest_sound_sample[0]))
            for i, c in enumerate(self.give_coils()):
                outstring+='{}\t{}\t'.format('Sensor'+str(i), '55')
                outstring+='{}\t{}\t{}\t{}\t'\
                    .format(c.abs_rot[0], c.abs_rot[1], c.abs_rot[2], c.abs_rot[3]) # rotational info
                outstring+='{}\t{}\t{}\t'\
                    .format(c.abs_loc[0], c.abs_loc[1], c.abs_loc[2],)
            outstring+='\n'
        return outstring

    def give_timestamp_secs(self):
        """Return the df timestamp in seconds.
        RTC3D protocol timestamps are in microseconds by default.
        """
        try:
             micro_ts = self.components[0].timestamp
             ts = micro_ts * 0.000001
        except AttributeError:
            ts = None
        return ts


class AsciiMessage(Message):
    """Class representing ASCII message objects"""

    def __init__(self, mtype, mbytes):
        self.message_type = mtype
        self.string = str(mbytes, 'ascii')

    def __str__(self):
        return self.string

    def pack_all(self):
        return bytes(self.string, 'ascii'), self.message_type


class ComponentBuilder(object):
    """Given a bytestring, this class identifies which component it represents,
    and unpacks it to the relevant object type.
    """
    HEADER = '> I'
    HEADER_LEN = struct.calcsize(HEADER)
    EACH_HEADER = '> 3I Q'
    EACH_HEADER_LEN = struct.calcsize(EACH_HEADER)

    COMPONENT_CLASS_MAP = {1: lambda a, b, c: Component3D(a, b, c),
                           2: lambda: ComponentAnalog,
                           3: lambda: ComponentForce,
                           4: lambda a, b, c: Component6D(framenum=a, timestamp=b, mbytes=c),
                           5: lambda: ComponentEvent,
                           0: lambda a, b, c: Component6D(framenum=a, timestamp=b, mbytes=c)}  # 0 is a catchall

    @classmethod
    def unpack(cls, mbytes):
        """Return a Component6D object for the bytestring"""
        components = []
        n, *_ = struct.unpack(cls.HEADER, mbytes[:cls.HEADER_LEN])
        bytesleft = mbytes[cls.HEADER_LEN:]
        for i in range(n):
            compsize, comptype, framenumber, timestamp = struct.unpack(cls.EACH_HEADER, bytesleft[:cls.EACH_HEADER_LEN])
            compcontent = bytesleft[cls.EACH_HEADER_LEN: compsize]
            bytesleft = bytesleft[compsize:]  # remove bytes read into variables

            print('component type is', comptype, 'fn is', cls.COMPONENT_CLASS_MAP[comptype])
            # append the relevant component object to list
            components.append(cls.COMPONENT_CLASS_MAP[comptype](framenumber, timestamp, compcontent))

        return components

    @classmethod
    def pack(cls, components):
        """Return a bytestring for the component"""
        return struct.pack(cls.HEADER, len(components)) \
               + b''.join([struct.pack(cls.EACH_HEADER, c.get_sizeb(), c.COMPONENT_TYPE, c.frame_number, c.timestamp)
               + c.pack_data()
               for c in components])

    def __init__(self, coils):
        self.coils = coils


class ComponentBase(object):
    """Base class for component objects"""
    GET_BUILDER_CLASS = lambda: ComponentBuilder

    def __init__(self, framenum=None, timestamp=None, fileparser=None):
        self.coils = NotImplemented
        self.frame_number = framenum
        self.timestamp = timestamp
        if fileparser is not None:
            self.extract_attrs_from_fileparser(fileparser)


    def __str__(self):
        if type(self.coils) == list:
            return "Component6D with {} coils;".format(len(self.coils))+str(self.coils[0])
        else:
            return "Not yet filled Component object"

    def extract_attrs_from_fileparser(self, fp):
        self.frame_number = fp.motion_lines_read
        if self.timestamp is None:
            if hasattr(fp, 'latest_timestamp'):  # if timestamp can be directly read from tsv, use this
                self.timestamp = fp.latest_timestamp
            else:  # else calculate this from the number of frames read and the time they are streamed at
                self.timestamp = int(self.frame_number * fp.frame_time)

        self.coils = CoilBuilder.create_coils(n=fp.min_channels, dimensions=fp.min_dimensions)


class ComponentXD(ComponentBase):
    """Base class for component objects with location"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.coils = NotImplemented

    def get_sizeb(self):
        return len(self.pack_data())+ struct.calcsize(self.__class__.GET_BUILDER_CLASS().EACH_HEADER)

    def pack_data(self):
        """Pack the component header, and the bytestring for each marker/coil"""
        print('struct header', self.__class__.GET_BUILDER_CLASS().HEADER)
        print('len coils', len(self.coils))
        print('each header', self.coils[0].__class__.GET_BUILDER_CLASS().EACH_STRUCT)
        return struct.pack(self.__class__.GET_BUILDER_CLASS().HEADER, len(self.coils)) + \
               b''.join([struct.pack(c.__class__.GET_BUILDER_CLASS().EACH_STRUCT, *c.in_packing_order()) for c in self.coils])

    def give_coils(self):
        return self.coils


class Component3D(ComponentXD):
    GET_INNER_BUILDER = lambda: CoilBuilder3D
    COMPONENT_TYPE = 1

    def __init__(self, framenum=None, timestamp=None, mbytes=None, fileparser=None):
        super().__init__(framenum=framenum, timestamp=timestamp, fileparser=fileparser)
        self.coils = self.__class__.GET_INNER_BUILDER().unpack(mbytes)


class Component6D(ComponentXD):
    GET_INNER_BUILDER = lambda: CoilBuilder6D
    COMPONENT_TYPE = 4

    def __init__(self, framenum=None, timestamp=None, mbytes=None, fileparser=None):
        super().__init__(framenum=framenum, timestamp=timestamp, fileparser=fileparser)
        if mbytes is not None:
            self.coils = self.__class__.GET_INNER_BUILDER().unpack(mbytes)


class ComponentAnalog(ComponentBase):
    COMPONENT_TYPE = 2


class ComponentForce(ComponentBase):
    COMPONENT_TYPE = 3


class ComponentEvent(ComponentBase):
    COMPONENT_TYPE = 5


class CoilBuilder(object):
    """Given a bytestring representing a coil/marker, make a relevant coil objects."""
    HEADER = '> I'
    HEADER_LEN = struct.calcsize(HEADER)
    GET_RESULT_CLASS = NotImplementedError
    EACH_STRUCT = NotImplementedError

    @classmethod
    def unpack(cls, bytestring):
        n, *_ = struct.unpack(cls.HEADER, bytestring[:cls.HEADER_LEN])
        bytestring = bytestring[cls.HEADER_LEN:]
        return [cls.GET_RESULT_CLASS(struct.unpack(cls.EACH_STRUCT, bytestring[i*cls.EACH_LEN: (i+1)*cls.EACH_LEN]))
                for i in range(n)]

    @staticmethod
    def average(coilobjs):
        thiscoil = CoilBase(0, 0, 0)
        n = len(coilobjs)
        print('averaging {} objects'.format(n))
        print('averaging objecs', coilobjs )
        thiscoil.abs_loc = [sum([o.abs_loc[i]/n for o in coilobjs ] ) for i in range(3) ]

        if thiscoil.abs_rot is not None:
            thiscoil.abs_rot = average_quaternions(o.abs_rot for o in coilobjs)

        return thiscoil

    @staticmethod
    def create_coils(n=1, dimensions=6, reordering=None, marker_channels=None):
        coils = []
        for i in range(n):
            coils.append(Coil6D(*[0 for i in range(8)]))
        return coils

    @staticmethod
    def to_floats(strings):
        """Convert all the things to strings"""
        def convert(item):
            if type(item) == str:
                try:
                    return float(item)
                except ValueError:
                    return 0
            elif type(item) == int:
                return float(item)
            elif type(item) == float:
                return item
            elif type(item) == list or type(item) == tuple:
                return [convert(s) for s in item]
            else:
                raise TypeError('Item type unknown')

        return convert(strings)


class CoilBuilder3D(CoilBuilder):
    EACH_STRUCT = '> 3f I'
    EACH_LEN = struct.calcsize(EACH_STRUCT)
    GET_RESULT_CLASS = lambda x: Coil3D(*x)


class CoilBuilder6D(CoilBuilder):
    EACH_STRUCT = '> 7f I'
    EACH_LEN = struct.calcsize(EACH_STRUCT)
    GET_RESULT_CLASS = lambda x: Coil6D(*x)

    @staticmethod
    def build_from_mapping(mapping, measurements):
        """From a list of mapping to wave order and list of measurements,
        create a coil obj.
        """
        print('Building 6D coil from mapping')
        x = measurements[mapping.xind]
        y = measurements[mapping.yind]
        z = measurements[mapping.yind]

        q0, qx, qy, qz = mapping.convert_to_quat(measurements)
        return Coil6D(q0, qx, qy, qz, x, y, z, None)



class CoilBase(object):
    """
    abs_loc is (x,y,z),
    abs_rot is (Q0, Qx, Qy, Qz)
    """
    GET_BUILDER_CLASS = lambda: CoilBuilder
    def __init__(self, x, y, z):
        self.abs_loc = self.__class__.GET_BUILDER_CLASS().to_floats((x, y, z))
        self.abs_rot = None

    def __str__(self):
        return "Coil with location {}".format(str(self.abs_loc))

    def __eq__(self, other):
        if self.__dict__ == other.__dict__:
            return True
        else:
            return False


class Coil3D(CoilBase):
    GET_BUILDER_CLASS = lambda: CoilBuilder3D

    def __init__(self, x, y, z, reliability):
        super().__init__(x, y, z)
        self.abs_loc = self.__class__.GET_BUILDER_CLASS().to_floats((x, y, z))
        self.reliability = self.__class__.GET_BUILDER_CLASS().to_floats(reliability)

    def in_packing_order(self):
        return self.abs_loc + tuple(self.reliability)


class Coil6D(CoilBase):
    GET_BUILDER_CLASS = lambda: CoilBuilder6D

    def __init__(self, q0, qx, qy, qz, x, y, z, error):
        super().__init__(x, y, z)
        self.abs_rot = self.__class__.GET_BUILDER_CLASS().to_floats((q0, qx, qy, qz))
        self.error = error if error is not None else 0

    def in_packing_order(self):
        return self.abs_rot + self.abs_loc + [self.error]

def main():
    # some unit tests
    streamdf = b'\x00\x00\x00\x01\x00\x00\x01\xf8\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0b\xe3\xc0\x00\x00\x00\x0f?\x047\x82\xbf<\xa5z\xbeJd\xc3>\xc7\x11\x94A\xb1(9\xc3\t|\x8e\xc2\x8b%\xd0\x00\x00\x00\x00?DL8\xbf#i\xdb=\x8ab$\x00\x00\x00\x00@\x88\xee\x0c\xc1m\x10_\xc2M\x8d\x19\x00\x00\x00\x00?\x0b[\xb4\xbfEb\xe1>\xa9)\x89\x00\x00\x00\x00@\xc1lS\xc0\xa5)\x8c\xc2/H\x85\x00\x00\x00\x00?\x089\x04\xbfW\xf9\xa5=\x92<\xc9\x00\x00\x00\x00@@e\x95\xc0\x15\x05\x8e\xc2\x0c\xa0\xd8\x00\x00\x00\x00?!\xf4\xb2>\xb4(\x91\xbf0\x9c\xd4\x00\x00\x00\x00@6 \xbd\xc1nuK\xc1\x82\x9d5\x00\x00\x00\x00?^\x1cz>\xfe\x93\x9f;\x0b\x97x\x00\x00\x00\x00\xc1\xc9/~?\x91\x82\x1c\xc2\tw)\x00\x00\x00\x00?F\x93)?\x0bO\xa5>\xa3\xa9\xd2\x00\x00\x00\x00?\x8b\xd1\xabA\x13hx\xc1^\xde\'\x00\x00\x00\x00?4"\xcd?"\x03\xf7\xbe\xa5b\x9e\x00\x00\x00\x00\xc1e\x95|\xc3\r\xb5#\xc2\x8eL\xd0\x00\x00\x00\x00>\x97z\xf6>\x87\xd7\xe4?j\xea\xc8\x00\x00\x00\x00B\x83\xc1@\xc1E\x91\xdf\xc3\x17I\xdb\x00\x00\x00\x00?qV\\\xbe\x0c\xc1\x87>\x9b\x9d\x80\x00\x00\x00\x00\xc2m\xa7}\xc0\xff\xfdv\xc3\x10\x86\x88\x00\x00\x00\x00??\x1b\xac?"N\x9c>N\xb1>\x00\x00\x00\x00?\xebw\xa5\xc0\x80\xbe\x12\xc1\xbe\xe9\xee\x00\x00\x00\x00?\x1e\xdd\x8b?GgM=\xb98\x15\x00\x00\x00\x00>\xe6`5@\xca>\x97\xc1\xcd{I\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    streamdf2 = b'\x00\x00\x00\x01\x00\x00\x01\xf8\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0b\xbd\x14\x00\x00\x00\x0f?\x04\x0bx\xbf<\xb7=\xbeJ\xc8\xe7>\xc7)oA\xb1(9\xc3\t|\x8e\xc2\x8b%\xd0\x00\x00\x00\x00?D`\x89\xbf#Q\x16=\x8a~\xfa\x00\x00\x00\x00@\x90{-\xc1m\x97\xc9\xc2L\xb2*\x00\x00\x00\x00?\x0bK\xf9\xbfEs2>\xa9\x11I\x00\x00\x00\x00@\xc2\xd4+\xc0\xa5\xf9j\xc2.\xdf\x94\x00\x00\x00\x00?\x08)\xbf\xbfX\x04\xda=\x91\xa5D\x00\x00\x00\x00@E\x19\x0b\xc0\x18>\x91\xc2\x0c5\x19\x00\x00\x00\x00?!\xc8\xfc>\xb4+R\xbf0\xc47\x00\x00\x00\x00@GSE\xc1q\xcf\x80\xc1\x83L\x8f\x00\x00\x00\x00?^!\x96>\xfe\x82\x0e:\xd2\x80k\x00\x00\x00\x00\xc1\xc9e\xa4?\x81;#\xc2\x08\xe7\n\x00\x00\x00\x00?F\x8a\xd7?\x0b\x83\xbe>\xa3 S\x00\x00\x00\x00?\xa1\x19\x07A\x11\xf0\xb5\xc1]\xe2\x1f\x00\x00\x00\x00?3\xe8\xde?"O\xb9\xbe\xa55\xa8\x00\x00\x00\x00\xc1d\x17`\xc3\r\xc2.\xc2\x8e!\xc0\x00\x00\x00\x00>\x97\x9a\x07>\x87v\x1d?j\xf3\xe4\x00\x00\x00\x00B\x83\xb2\x8c\xc1E\x0f\xdb\xc3\x17C\xd5\x00\x00\x00\x00?qO\xce\xbe\r<\xbc>\x9b\xaa\x15\x00\x00\x00\x00\xc2m\x8c6\xc0\xfb\xe7\x99\xc3\x10h\x01\x00\x00\x00\x00??\x10\x02?"gQ>N\'[\x00\x00\x00\x00@\x07C~\xc0\x886\xe5\xc1\xbf4/\x00\x00\x00\x00?\x1e\xbff?G\x804=\xb8\xfb\xca\x00\x00\x00\x00>\xfb\xbdt@\xc8B\xa9\xc1\xcd)u\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    ok = b'\x00\x00\x00\x18\x00\x00\x00\x01sendcurrentframe'
    df = b"\x00\x00\x01\xf8\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00MX\x00\x00\x00\x0f?\x00\xe3\xac\xbf<\xcb\\\xbea\x84<>\xc9\x03dA\xb1(9\xc3\t|\x8e\xc2\x8b%\xd0\x00\x00\x00\x00?D\x7f\xaa\xbf#\xaa7=<\x06\xe2\x00\x00\x00\x00@\x9bG\xed\xc1k\x19\xbb\xc2J\xc6\xb6\x00\x00\x00\x00?\n\x08l\xbfI_F>\x9a\n\xb7\x00\x00\x00\x00@\xd1\x02c\xc0\xa2\xfb9\xc21\xc9\x91\x00\x00\x00\x00?\x06V\xde\xbfY\xcb\x04<\xed\xbbZ\x00\x00\x00\x00@w\x19Y\xc0\x0c,\x96\xc2\x0e.^\x00\x00\x00\x00?!\xb39>\xc3\x13\x16\xbf,\xd8w\x00\x00\x00\x00@'\x18\xe9\xc1u\xda\x94\xc1\x80\xff9\x00\x00\x00\x00?_\xe5\xeb>\xf7\x95\xb3=\x10\x14\xb6\x00\x00\x00\x00\xc1\xc5\xf6E?\xcf\x8c\x80\xc2\x0c\xafi\x00\x00\x00\x00?G|\xdd?\x07\xaf\x10>\xab<\xe6\x00\x00\x00\x00?\x81<9A\x17\x14\x87\xc1^\x13i\x00\x00\x00\x00?3\xef\xbf?%Y\xf7\xbe\x98\x8c\x82\x00\x00\x00\x00\xc1a\xf2\xf0\xc3\r\x0e\xe1\xc2\x8f\x7fE\x00\x00\x00\x00>\x9bh\xad>\x8aE\xd4?i\xebS\x00\x00\x00\x00B\x85\xcd\xe8\xc1F\xa0\x00\xc3\x17\x83g\x00\x00\x00\x00?r6L\xbe\x1a\xfar>\x92\x88\xce\x00\x00\x00\x00\xc2jWb\xc0\xe1S\x93\xc3\x10\x84,\x00\x00\x00\x00?@)\xd0?\x1fN\xca>cX*\x00\x00\x00\x00@\x1bI\xa9\xc0\x832@\xc1\xbf\xdc\x9a\x00\x00\x00\x00? \x03\x04?E\x8b\x93=\xf1\x16\xa9\x00\x00\x00\x00?,`\xa1@\xb1\x14c\xc1\xcd0:\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    b = b'\x00\x00\x00\x01\x00\x00\x02\x18\x00\x00\x00\x04\x00\x00e\t\x00\x00\x00\x00\x03\xda\xab\xe4\x00\x00\x00\x10\x95\x90\x90>\xb5k`\xbfch\xfc\x00\x00\x00\x00B\xdb\x90\xbd\xc3\x12\x96\xa4\xc3\'\x19\xdb\x00\x00\x00\x00>>]\xdc?\\\xe1c>\xf4\x94\xce\x00\x00\x00\x00B\xe8\xee\x03\xc3\x11\xb4y\xc3(\x0eY\x00\x00\x00\x00?\\l\xe7>\x8cj\xa6>\xdbD6\xb2\x80\x00\x00B\xa5\x8e\xfe\xc2\xb5\xde\x02\xc3\x06\xb8\x83\x00\x00\x00\x00>\xccm\x89?i\xf3\xa2=\x96\xb7\xd02\x00\x00\x00A$\x9c\x95\x95\xc2\x1bz\x8d\xc3\x03\xdaz\x00\x00\x00\x00?q8\x9b\xbda\xbb\x90\xbe\xa9\x1b\x823\x00\x00\x00B\xafw\x08\xc1\xe6\x11\xe8\xc2\xd1k\x07\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff?"\xcf\x94\xbb>"\x80\xbfE\x8e$\xb3\x00\x00B\xb4\xb1\xe2\xc2\x99\xd1>\xc2\xf7\x91\xac\x00\x00\x00\x00??zR>\xfc\xac\xc0>\xe3A\x0c2\x80\x00\x00\xc2\xef\x1f\xdd\xc2:M\xe1\xc3\x8e\x7f\xe1\x00\x00\x00\x00?RQ\x02\xbe\x98\xc9\x9c\x9c\xbe\xf8\xbb\x94\x00\x00\x00\x00@\x91\xc2V\xc2\x9a\x90c\xc2\xf8\xc5L\x00\x00\x00\x00>\xed\xc4\xac\xbf\x0019\xbf:\xef\xc02\x80\x00\x00@\x8072\xc1\x8b\xb0f\xc3,\xfc#\x00\x00\x00\x00?1\x96n\xbf\x004\xd4\xbf\x004\xd4\xbf\x04\x85U3\x00\x00\x00\xc2\x91\x81~\xc2\xa7\xa7\xf7\x87\xc3\x93\x94Q\x00\x00\x00\x00?\x1d\x13\x1d\xbe\xa0\x8e\xce\xbf9\x85\xef\x00\x00\x00\x00\xc2\xc25\xcc\xc2\xa5\xe5\x0e\xc3\x8f{\x03\x00\x00\x00\x00?K\x90\xf5\xbeiI\x18?\x0f\xdb\xe5\x00\x00\x00\x00B\x80y&\xc2D\xfc\xda\xc2\xcd\x13\xbb\x00\x00\x00\x00?\x1a\x8c\xae>\x1f\xd9\x0c\xbfH"8\x00\x00\x00\x00\xc2\xe1\xb2\xc6\xc0~\x98A\xc3\r\xce\xa1\x00\x00\x00\x00?>\xc8t<\xac\xea\x90\xbf?\x85\x88\xb3\x00\x00\x00\xc2\xce\x01\xe8\xc25\xa3q\xc3"\x11T\x00\x00\x00\x00?\x1e\x94I=\xb6\xea\x88\xbfG\xaa\x11\x00\x00\x00\x00\xc2\xde\x95\xee\xc2\x12B\x03\xc3\x04\xef+\x00\x00\x00\x00'

    print('Message length is', len(df))

    #s, t, m = RTC3DPacketParser.unpack_outer(df)
    #print('unpack_outer gives', s, t, m)

    #s2, t2 = RTC3DPacketParser.get_size_type(df)
    #print('size type gives', s2, t2)
    #assert s2 == s

    #print('sizetype own',RTC3DPacketParser.get_size_type(RTC3DPacketParser.pack_outer(m, 1)))
    #print('sizetype orig',RTC3DPacketParser.get_size_type(df))
    #assert RTC3DPacketParser.pack_outer(m, t) == streamdf
    # it seems that the old parser had some failings (message type and size switched, size 4 bytes too small

    # test the Data frame builder
    #RTC3DPacketParser.unpack_all(b)
    #RTC3DPacketParser.unpack_all(ok)

    message_bytes = streamdf
    outer_bytes1 = RTC3DPacketParser.pack_outer(message_bytes, 3)

    print('Testing MessageBuilder unpack vs. RTC3DPacketParser unpack')
    # objs1 + 2 should be the same
    object1 = MessageBuilder.unpack_all(message_bytes, 3)
    object2 = RTC3DPacketParser.unpack_all(outer_bytes1)

    print(object1)
    print(type(object1))
    print(object2)
    print(type(object2))
    assert object1 == object2

    print('Testing RTC3DPacketParsers pack outer vs. pack all')
    bytes1 = RTC3DPacketParser.pack_outer(DataFrame.pack_all(object1), 3)
    bytes2 = RTC3DPacketParser.pack_all(object1)

    print(bytes1)
    print(bytes2)
    assert bytes1 == bytes2

    print('Testing whether the original bytes are reconstructed')
    print(type(bytes1), len(bytes1), bytes1)
    print(type(outer_bytes1), len(outer_bytes1), outer_bytes1 )
    assert bytes1 == outer_bytes1

    print('Testing coil returning functions')

    assert object1.give_coils() == object1.components[0].coils

    print('Testing averaging dfs')
    av = MessageBuilder.average_dataframes([object1, object2])
    print(av)

    print(av.to_tsv())


    # print('b1 is type', type(b1))
    # o1 = RTC3DPacketParser.unpack_all(b1)
    # print('o1 is type', type(o1))
    # b2 = o1.pack_all() # Packs to Dataframe level
    # b3 = RTC3DPacketParser.pack_all(o1)
    # print('b2 is type', type(b2))
    #
    # print('original bytes and reconstructed bytes should be the same')
    # print(b1)
    # print(b2)
    # assert b2 == b3[8:]
    #
    # assert b3 == b1
    #
    # print('test at message level?')
    #
    #
    # print('\na pulled')
    # a_pulled = DataFrame(b)
    # print(a_pulled)
    # print(a_pulled.components[0])
    # coils = a_pulled.give_coils()
    # print(coils[3])
    #
    # print('\na pulled and pushed')
    # a_pushed = RTC3DPacketParser.pack_all(a_pulled)
    # a_pp = RTC3DPacketParser.unpack_all(a_pushed)
    #
    # print(a_pp)
    # print(a_pp.components[0])
    # coils = a_pp.give_coils()
    # print(coils[3])
    #
    # print(b)
    # print(a_pushed)
    #
    #
    # b2 = RTC3DPacketParser.pack_outer(b, 3)
    # assert b2 == a_pushed

if __name__ == "__main__":
    main()




