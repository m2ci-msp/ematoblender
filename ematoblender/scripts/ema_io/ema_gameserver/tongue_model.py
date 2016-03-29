__author__ = "Kristy"

"""
This is a stub script, that represents the tongue model module.
It keeps track of data relevant for the tongue fitting - 
eg which coils are on the tongue,
eg which Vertex indices on the mesh represent the coil location.

"""

import json
import ematoblender.scripts.ema_shared.properties as pps

class TongueModel():
    """
    Ema indices can be found from the datafile / some external json
        -> Use introspection to find these
    Vertex indices can be found from Blender or an external tool
        -> Set based on server communication
    """

    cpp_address = (pps.cpp_host, pps.cpp_port)
    tongue_names = ['TT', 'TM', 'TB', 'TL', 'TR']

    def __init__(self, ncoils=5):
        """Construct a tongue-model instance"""

        self.tongue_coils = []

        for i in range(ncoils):
            self.tongue_coils.append(TongueCoil())

    def parse_vertex_message(self, transmission):
        """Upon receiving a communication about how the positions
        correspond to the vertex positions, set these."""
        headerlen = transmission.find(':') + 1
        d = json.load(transmission[headerlen:])

        # TODO: decide how the JSON should be structured for this purpose
        # TODO: parse and break out into these items.
        pass

    def parse_coil_positions(self, jsonlocation):
        """Read the JSON indicating the index and the name.
        For each sensor that has a tongue-related name (see class attr)
        save this index.
        """
    # TODO: reuse fns to parse the json file
    # check against tonguenames list
    # break out into items


    def set_vertex_indices(self, *ilist):
        """Receives a set of indices, labelled 'sourceIndices' if in JSON"""
        for c, i in zip(self.tongue_coils, ilist):
            c.set_vertex_index(i)

    def set_position_names(self, *namelist):
        for c, i in zip(self.tongue_coils, namelist):
            c.set_position(i)

    def set_tongue_coil_indices(self, *ilist):
        for c, i in zip(self.tongue_coils, ilist):
            c.set_ema_index(i)

    def get_vertex_indices(self):
        """Return a list of the vertices that the coils move."""
        return [c.vertex_index for c in self.tongue_coils]

    def get_tongue_coil_indices(self):
        """Return a list of each coil's index in the ema data."""
        return [c.ema_index for c in self.tongue_coils]

    def get_tongue_coil_names(self):
        """Return a list of the place names"""
        return [c.position for c in self.tongue_coils]

    def __str__(self):
        return "TongueModel object with coil objects: {}".format(self.tongue_coils)



class TongueCoil():

    def __init__(self):
        """Construct a tongue-coil instance."""
        self.ema_index = None
        self.position = None
        self.vertex_index = None

    def set_ema_index(self, i):
        self.ema_index = i

    def set_position(self, pl):
        self.position = pl

    def set_vertex_index(self, i):
        self.vertex_index = i

    def __str__(self):
        return "TongueCoil obj at index {}, position {}, corr to vertex {}" \
        .format(self.ema_index, self.position, self.vertex_index)


def main():
    """Test the TongueModel class"""
    a = TongueModel()
    a.set_vertex_indices(100,200,300,400, 500)
    a.set_position_names('TT', 'TB', 'TM', 'TL', 'TR')
    a.set_tongue_coil_indices(3,4,5,6, 7)
    print(a)
    print(a.tongue_coils[0])
    print(a.tongue_coils[3])

    from ematoblender.scripts.ema_io.rtc3d_parser import JSONBuilder, DataFrame
    rawbytes = b = b'\x00\x00\x00\x01\x00\x00\x02\x18\x00\x00\x00\x04\x00\x00e\t\x00\x00\x00\x00\x03\xda\xab\xe4\x00\x00\x00\x10\x95\x90\x90>\xb5k`\xbfch\xfc\x00\x00\x00\x00B\xdb\x90\xbd\xc3\x12\x96\xa4\xc3\'\x19\xdb\x00\x00\x00\x00>>]\xdc?\\\xe1c>\xf4\x94\xce\x00\x00\x00\x00B\xe8\xee\x03\xc3\x11\xb4y\xc3(\x0eY\x00\x00\x00\x00?\\l\xe7>\x8cj\xa6>\xdbD6\xb2\x80\x00\x00B\xa5\x8e\xfe\xc2\xb5\xde\x02\xc3\x06\xb8\x83\x00\x00\x00\x00>\xccm\x89?i\xf3\xa2=\x96\xb7\xd02\x00\x00\x00A$\x9c\x95\x95\xc2\x1bz\x8d\xc3\x03\xdaz\x00\x00\x00\x00?q8\x9b\xbda\xbb\x90\xbe\xa9\x1b\x823\x00\x00\x00B\xafw\x08\xc1\xe6\x11\xe8\xc2\xd1k\x07\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff?"\xcf\x94\xbb>"\x80\xbfE\x8e$\xb3\x00\x00B\xb4\xb1\xe2\xc2\x99\xd1>\xc2\xf7\x91\xac\x00\x00\x00\x00??zR>\xfc\xac\xc0>\xe3A\x0c2\x80\x00\x00\xc2\xef\x1f\xdd\xc2:M\xe1\xc3\x8e\x7f\xe1\x00\x00\x00\x00?RQ\x02\xbe\x98\xc9\x9c\x9c\xbe\xf8\xbb\x94\x00\x00\x00\x00@\x91\xc2V\xc2\x9a\x90c\xc2\xf8\xc5L\x00\x00\x00\x00>\xed\xc4\xac\xbf\x0019\xbf:\xef\xc02\x80\x00\x00@\x8072\xc1\x8b\xb0f\xc3,\xfc#\x00\x00\x00\x00?1\x96n\xbf\x004\xd4\xbf\x004\xd4\xbf\x04\x85U3\x00\x00\x00\xc2\x91\x81~\xc2\xa7\xa7\xf7\x87\xc3\x93\x94Q\x00\x00\x00\x00?\x1d\x13\x1d\xbe\xa0\x8e\xce\xbf9\x85\xef\x00\x00\x00\x00\xc2\xc25\xcc\xc2\xa5\xe5\x0e\xc3\x8f{\x03\x00\x00\x00\x00?K\x90\xf5\xbeiI\x18?\x0f\xdb\xe5\x00\x00\x00\x00B\x80y&\xc2D\xfc\xda\xc2\xcd\x13\xbb\x00\x00\x00\x00?\x1a\x8c\xae>\x1f\xd9\x0c\xbfH"8\x00\x00\x00\x00\xc2\xe1\xb2\xc6\xc0~\x98A\xc3\r\xce\xa1\x00\x00\x00\x00?>\xc8t<\xac\xea\x90\xbf?\x85\x88\xb3\x00\x00\x00\xc2\xce\x01\xe8\xc25\xa3q\xc3"\x11T\x00\x00\x00\x00?\x1e\x94I=\xb6\xea\x88\xbfG\xaa\x11\x00\x00\x00\x00\xc2\xde\x95\xee\xc2\x12B\x03\xc3\x04\xef+\x00\x00\x00\x00'
    df = DataFrame(rawdf=rawbytes)

    packet = JSONBuilder.pack_wrapper(df, a.get_vertex_indices(), a.get_tongue_coil_indices())
    print(packet)

if __name__ == "__main__":
    main()



