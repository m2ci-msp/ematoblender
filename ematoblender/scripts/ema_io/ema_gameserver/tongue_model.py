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
    a.set_vertex_indices(100,200,300,400)
    a.set_position_names('TT', 'TB', 'TM', 'TL')
    a.set_tongue_coil_indices(3,4,5,6)
    print(a)
    print(a.tongue_coils[0])
    print(a.tongue_coils[3])

if __name__ == "__main__":
    main()



