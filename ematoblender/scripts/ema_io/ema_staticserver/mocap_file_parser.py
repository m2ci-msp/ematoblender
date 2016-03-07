# -*- coding: utf-8 -*-
__author__ = 'Kristy'

"""
Module that reads motion capture files of TSV, BVH or POS format.
File-reader interface reads and parses header, then line-by-line.
Responses are encoded according to the RTC3D protocol.
"""

import xml.etree.ElementTree as ET
import math
import struct
import os
from ematoblender.scripts.ema_io.rtc3d_parser import DataFrame, Component, Coil

xml_skeleton_location = './scripts/ema_io/ema_staticserver/parameter_skeleton.xml'


class MakeMocapParser():
    """Factory Class to make parser objects based on the file extension."""
    def factory(filename):
        """Open a  filename (type read from extension), create parser class."""
        extension = filename.lower().split('.')[-1]
        if extension == 'bvh':
            return BVHParser(filename)
        if extension == 'tsv':
            return TSVParser(filename)
        if extension == 'pos':
            return POSParser(filename)
        assert 0, "Bad mocap file type " + extension
    factory = staticmethod(factory)


class MocapParent(object):
    """Parent class to Mocap objects."""

    def __init__(self, filename):
        print('initialising a mocap parent')

        # open the file
        filename = filename if os.path.isabs(filename) else os.path.normpath(os.getcwd()+os.path.sep + filename)
        self.file = open(filename, 'r')
        self.file_name = self.file.name
        self.format = filename.split('.')[-1]

        # capture the position within the file
        self.motion_lines_read = 0
        self.pre_motion_position = 0  # positioned to readline() and give motion line

        # populated in subclasses from the header/pre-reading
        self.sampling_rate = 0      # frames per second sampled
        self.frame_time = 0         # number of microseconds per frame
        self.frame_times = []       # list of time difference between frames in seconds
        self.max_num_frames = 0     # for static file, the number of frames that can  be read before looping

        # perhaps these could be coil objects
        self.n_coils = 0            # integer, representing number of coils to be read
        self.marker_names = []      # the labels in the static header for each coil, in order listed
        self.marker_channels = []   # TODO: Tuple?

        # arbitrary large number,
        # later represents the number of dimensions measured to decide between 6d and 3d representations
        self.min_dimensions = 100
        self.mappings = None        # list indicating how the file's values should be reordered to emulate WAVE ordering

        self.latest_timestamp = 0 # timestamp is microseconds
        self.component = Component  # an initial component attribute

        self.xml_tree = ET.parse(xml_skeleton_location)  # basic standard XML root

        self.wave_name, self.video_name = self.search_for_multimodal()

    @staticmethod
    def timestamp_to_microsecs(timestamp):
        """Get timestamp as string or int. Convert to ms."""
        # ts is a float, presume  it's in seconds
        if type(timestamp) == float or (type(timestamp) == str and timestamp.find('.')):
            timestamp = math.floor(float(timestamp) * 1000000)  #seconds to microseconds

        # ts is an integer, presumably milliseconds. keep in same format
        elif (type(timestamp) == str and timestamp.isnumeric()) or type(timestamp) == int: # presumably string of integer
            timestamp = int(timestamp)
        else:
            raise TypeError
        return timestamp

    @staticmethod
    def make_float_or_zero(listofvals):
        """Converts all items in the list to floats, or to 0.0 if not possible."""
        floatvals = []
        for v in listofvals:
            try:
                v = float(v)
            except ValueError:
                v = 0.0
            finally:
                floatvals.append(v)
        return floatvals

    def __str__(self):
        """String rep of the mocap file"""
        return "Mocap file, generic type. This should never have an instance."

    # not implemented
    def read_header(self):
        raise NotImplementedError

    # not implemented
    def give_motion_frame(self):
        raise NotImplementedError

    # maintain the XML parameters
    def update_xml_initial(self, component='3D'):
        """
        Put the existing object information into the XML using the RTC3D XML template.
        Updates self.xml_root.
        """

        # give the information about motion capture, wave, ultrasound/video locations
        self.xml_tree.find("General").find("Multimodal").find("MocapFileAbsLoc").text = self.file_name
        self.xml_tree.find("General").find("Multimodal").find("AudioFileAbsLoc").text = self.wave_name
        self.xml_tree.find("General").find("Multimodal").find("VideoFileAbsLoc").text = self.video_name

        # set the Frequency (whether 3D or 6d the frequency is set for both
        self.xml_tree.find("./The_3D/Frequency").text = str(self.sampling_rate)
        self.xml_tree.find("./The_6D/Frequency").text = str(self.sampling_rate)

        # # TODO: Optional improvement: Show marker name information in XML based on header? As yet unused.
        # # set the marker names from the header
        # marker_parent = self.xml_root.find("./The_6D//Markers")
        # for i, name in enumerate(self.marker_names):
        # m = ET.SubElement(marker_parent,  "Marker", {'id': str(i+1)}); l = ET.SubElement(m, "Label"); l.text = str(name)

    def update_xml_stats(self):
        """
        Increment the General/Server/Stats/FramesSent  integer, FramesPerSec float.
        For now only counts how many frames have been sent.
        """
        self.xml_tree.find("General").find("Server").find("Stats").find("FramesSent").text = \
            str(self.motion_lines_read)
        return self.xml_tree

    def reset_motion_section(self):
        """Put self.file to a position where it is not at EOF."""
        self.file.seek(self.pre_motion_position, 0)
        self.motion_lines_read = 0

    def search_for_multimodal(self):
        """
        Search based on filename for corresponding WAV or ultrasound videos.
        :return:  abspath to both, None if not found.
        """
        wave_name, video_name = None, None

        audtypes=['.wav', '.ogg', 'mp3']
        vidtypes = ['.avi', '.mpeg', '.mp4', ]

        # returns absolute path to audio file
        dirname, tail = os.path.split(self.file_name)
        streamfilename, streamext = os.path.splitext(tail)

        # search in same directory, then sister directory
        current_search_dir = os.path.normpath(dirname+os.path.sep)
        sister_search_dir = os.path.normpath(dirname+os.path.sep+'..'+os.path.sep)

        wavefound, vidfound = False, False

        for search_dir in [current_search_dir, sister_search_dir]:  # search in current folder first
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    fn, ext = os.path.splitext(file)
                    if fn.startswith(streamfilename):
                        print('candidate found!', os.path.join(root, file))
                        if ext in audtypes:
                            wave_name = os.path.join(root, file)
                            wavefound = True
                        if ext in vidtypes:
                            video_name = os.path.join(root, file)
                            vidfound = True

                        # break once both are populated
                        if wavefound and vidfound:
                            return wave_name, video_name

        return wave_name, video_name

    @staticmethod
    def order_measurements_as_wave(labels, nchannels=3):
        """
        Takes a list of labels that describe the output from the datafile.
        That is, a list based on the wave protocol, with for each position, the index of the element in the input it should access.
        Label order is: q0, qx, qy, qz, x, y, z
        :return: List of indices that should be applied to the labels to re-order them for the WAVE protocol.
        None for labels that aren't included in the final object.
        """

        origlen = len(labels)
        attributes = [(i, MocapParent.channel_label_to_attrs(l)) for i, l in enumerate(labels)]

        # get lists for which channels are (guessed to be) location/rotation, x/y/z etc.
        locs = [i for i, attrs in attributes if attrs[0]]
        rots = [i for i, attrs in attributes if attrs[1]]

        x = [i for i, attrs in attributes if attrs[2]]
        y = [i for i, attrs in attributes if attrs[3]]
        z = [i for i, attrs in attributes if attrs[4]]
        q = [i for i, attrs in attributes if attrs[5]]
        zero = [i for i, attrs in attributes if attrs[6]]

        if nchannels >= 6:  # rotation available
            # x, y, z, by intersection of loc/rots and xyz
            labelindices = [[j for j in letter if j in orientation]
                            for orientation in [rots, locs] for letter in [x,y,z] ] # first orientation is impossible as placeholder for q0
            #print("returning the correct order as:", [labels[li[0]] for li in labelindices])
            # make indices of length 1 else None, increment by one to allow place for q0

            # return the reordered label indices
            changed_indices = [li[0] if len(li)> 0  else None for li in labelindices]
            #print("ci", changed_indices)

            q0_refs = [i for i in q if i in zero]
            q_index = min(q0_refs) if len(q0_refs)>0 else -1
            #print("q index", q_index)
            changed_indices = [q_index] + changed_indices  # q0 has a Q but no X Y or Z in label
            #print("qi", changed_indices)

            #print("original labels", labels)
            #print("changed ind", changed_indices)

        else:  # only location available for all, use 3d order

            labelindices = [[j for j in letter if j in orientation] for orientation in [locs] for letter in [x,y,z] ]
            #print("returning the correct order as:", [labels[li[0]]if len(li)>0 else None for li in labelindices])
            changed_indices = [li[0] if len(li)>0 else None for li in labelindices[1:]]

        # ensure all labels receive a new index
        filling_none = [None for i in range(origlen - len(changed_indices))]
        return changed_indices + filling_none   # return the reordered label indices


    # unused in this application
    @staticmethod
    def channel_label_to_attrs(label):
        """Semantically parse label names."""
        label = label.lower()

        # rotation vs location
        if 'rot' in label or 'q' in label: # rotation label
            location = False; rotation = True
        elif 'loc' in label or 'pos' in label or 'mm' in label: # position label
            location = True
            rotation = False
        else:
            location = False
            rotation = False
        zero = False
        if '0' in label:
            zero = True

        # axis
        if label.startswith('x') or label.endswith('x'):
            x, y, z = True, False, False
        elif label.startswith('y') or label.endswith('y'):
            x, y, z = False, True, False
        elif label.startswith('z') or label.endswith('z'):
            x, y, z = False, False, True
        else:
            x, y, z = False, False, False

        # Euler vs Quaternion
        if label.startswith('q') or label.endswith('q'):
            quat = True
        else:
            quat = False # Euler angles presumed
        return location, rotation, x, y, z, quat, zero


class BVHParser(MocapParent):
    """
    Class to parse .bvh motion capture files (Biovision Hierarchical Data).
    """

    def __init__(self, filename):
        """ Initialise the BVH Parser object. """

        super().__init__(filename)
        self.read_header()
        self.update_xml_initial()

        # get the mappings between the measurements and wave orderings
        self.mappings = [self.order_measurements_as_wave(channels, nchannels=self.min_dimensions)
                         for channels in self.marker_channels]

        self.component = Component(fileparser=self)  # builds coil objects within init

    def __str__(self):
        return "bvh mocap file with these coils: {}".format(str(self.marker_names))

    def read_header(self):
        """Read the BVH header and put in neutral format."""

        f = self.file           # keep file open after execution
        line = f.readline()     # First line should be 'HIERARCHY'

        # while in the header
        while not line.startswith("MOTION"):
            strippedline = line.strip(' \t\n\r')

            # capture root/joint names sequentially
            if strippedline.startswith('ROOT') or strippedline.startswith('JOINT'): # get a marker name
                _, name = strippedline.split()
                self.marker_names.append(name)

            # capture channel information sequentially (should correspond to joint information)
            elif line.strip('\t\n ').startswith('CHANNELS'): # get the marker's channels
                channelline = strippedline.split(' ')
                num_channels = int(channelline[1])
                if num_channels != len(channelline[2:]):
                    raise ValueError
                self.min_dimensions = num_channels if num_channels < self.min_dimensions else self.min_dimensions
                self.marker_channels.append(channelline[2:])  # append a tuple of the channels for the marker

            line = f.readline()
        self.min_channels = len(self.marker_channels)

        # act based on the header data:
        # put marker names into xml

        # number of samples in file; 1/sampling rate (frame time)
        text, frames = self.file.readline().strip('\n').split(':')
        self.num_frames = int(frames)
        text, frame_time = self.file.readline().strip('\n').split(':')
        self.frame_time = float(frame_time) * 1000000

        # now up to motion frames, to be handled in another function
        self.pre_motion_position = self.file.tell()

    def give_motion_frame(self):
        """According to the RTC3D protocol, return the error code and the bytestring with the packed dataframe."""
        nextline = self.file.readline()
        if (nextline is not None) and (len(nextline.strip('\n\r\t ')) > 0):  # if there are more motion lines
            self.motion_lines_read += 1
            self.latest_timestamp += self.frame_time

            # update Component/Coil objects from file
            measurements = nextline.rstrip('\n')
            measurements = measurements.split('\t')
            #print("measurement line is", measurements)

            # break into sub-lists per tool
            measurements_by_coil = []
            for ch in self.marker_channels:
                print("new measurements", measurements[:len(ch)])
                measurements_by_coil.append([float(j) for j in measurements[:len(ch)]])
                measurements = measurements[len(ch):]

            print("about to alter component", str(self.component)[:50])

            for i, coil in enumerate(self.component.coils):
              #  print("giving a coil a measurement,", measurements_by_coil[i])
                coil.set_args_to_vars(measurements_by_coil[i])
            # wrap Component in Wave protocol to data packet level and return

            return 3, DataFrame(components=[self.component]).pack_components_to_df(), None

        # no more data available (static, give up)
        else:
            # need to set status of server_func to EOF
            print("All the frames have been read")
            return 4, "No more frames left in mocap file"


class TSVParser(MocapParent):
    """Class to parse .tsv motion capture files (NDI Wave format). """

    def __init__(self, filename):
        """ Initialise the TSV Parser object."""

        super().__init__(filename)
        self.read_header()
        self.update_xml_initial()

        print(self.marker_channels)

        # mapping of TSV is sens_id, sens_status, x, y, z, q0, qx, qy, qz
        # desired order is q0, qx, qy, qz, x, y, z
        self.mappings = [5, 6, 7, 8, 2, 3, 4]

        self.component = Component(fileparser=self)  # builds first component objects within init

    def __str__(self):
        return "tsv mocap file"

    def read_header(self):
        """Read header of the TSV file getting self.marker_names, self.marker_channels,
        self.min_channels, self.frame_time, self.num_frames"""

        # standard TSV format from WAVE, ignores field WavID
        self.extra_left_fields, self.fields_per_sensor = 3, 9
        self.timestamp_index, self.frame_id_index = 0, 1

        f = self.file
        f.seek(0, 0)

        # read the very first line with column headers
        headerline = f.readline()
        headerfields = headerline.strip('\n\r').split('\t')

        self.min_channels = (len(headerfields) - self.extra_left_fields) // self.fields_per_sensor
        self.frame_times = []

        # discard the second line - this sometimes has incorrect information like long audio timestamps (presumably WAVE internal)
        f.readline()

        # put in position to begin streaming (skip header line)
        self.pre_motion_position = self.file.tell()  # this is the beginning of the third line

        # collect a list of the timestamps, count the motion frames

        # read the first real line to get the initial timestamp
        firstline = f.readline().rstrip().split('\t')
        self.max_num_frames = 1
        last_timestamp = MocapParent.timestamp_to_microsecs(firstline[self.timestamp_index])

        # read the rest of the lines
        for line in f.readlines():
            self.max_num_frames += 1
            splitline = line.strip('\n\r').split('\t')
            timestamp = MocapParent.timestamp_to_microsecs(splitline[self.timestamp_index])  #now microseconds
            self.frame_times.append(timestamp-last_timestamp)  # list of differences in microseconds
            last_timestamp = timestamp

        self.frame_time = sum(self.frame_times)/self.max_num_frames  # now in microseconds
        # TODO: This overestimates the frame time slightly because if a measurement is missing this is unseen at this point

        print('frame time is ', self.frame_time, 'microseconds')
        print('max_num_frames is', self.max_num_frames)


        f.seek(self.pre_motion_position, 0)

        # TODO: Does not handle skipped frames in data, should rather give a frame based on the timestamp

    def give_motion_frame(self):
        """Read the next TSV line, and, skipping fields for the header and channel header, assign data to channels.
        :returns: error code, bytestring of packed data
        """
        if self.motion_lines_read < self.max_num_frames:
            self.motion_lines_read += 1

            # update Component/Coil objects from file
            # read the next line, split into meta (eg timestamp etc) and data
            if self.file.closed:
                print(self.file_name)
                print(self.file)
                print('THE FILE IS CLOSED WHY?')
                raise Exception
            measurements = self.file.readline().rstrip('\n')
            meta, all_measurements = measurements.split('\t')[:self.extra_left_fields], measurements.split('\t')[self.extra_left_fields:]
            measurements_by_coil = [all_measurements[x:x+self.fields_per_sensor] for x in range(0, len(all_measurements), self.fields_per_sensor)]

            # print('@@@', self.fields_per_sensor,len(measurements_by_coil[0]))
            # get the timestamp, convert to ms if seconds
            timestamp = meta[self.timestamp_index]
            timestamp = MocapParent.timestamp_to_microsecs(timestamp)# timestamp now in microseconds

            print("about to alter component", str(self.component)[:50])

            for coilvals, coilobj in zip(measurements_by_coil, self.component.coils):
                floatvals = MocapParent.make_float_or_zero(coilvals)
                # note that coilvals is  id, status, x, y, z, q0, qx, qy, qz
                coilobj.set_args_to_vars(floatvals, mapping=self.mappings)  # self.mapping sorts these to coil order

            self.component.timestamp = timestamp # TODO: Are there any other fields that are missing? Eg should I send WavID?
            self.latest_timestamp = timestamp
            #print(self.component)

            return 3, DataFrame(components=[self.component]).pack_components_to_df(), self.latest_timestamp

        # no more data available (static, give up)
        else:
            print("All the frames have been read")
            return 4, "No more frames left in mocap file"


class POSParser(MocapParent):
    """Parses Carstens motion capture files for AG500 and AG501 machines."""

    def __init__(self, filename):
        """ Initialise the POS parser object. """
        super().__init__(filename)
        # POS file is a binary, read header then open in bytes
        self.file.close()
        self.file = open(filename, 'rb')
        self.read_header()
        self.update_xml_initial()

        # the mapping between pos data format and WAVE order is known
        # mapping of POS is: x, y, z, phi, theta, rms, extra
        # desired order for WAVE is: q0, qx, qy, qz, x, y, z
        # based on standard Euler rotation with order XYZ, if ph
        self.mappings = [None, 3, 4, None, 0, 1, 2]
        # TODO: Check in literature that Carstens' phi and theta represent Euler X and Y rotation

        self.component = Component(fileparser=self) # build the first component within the mocap object

    def read_header(self):
        """Read the version, channel info and sampling rate from the ASCII header."""
        firstline = str(self.file.readline(), encoding='utf-8')
        if 'V002' in firstline:
            self.pos_version = 2
        elif 'V003' in firstline:
            self.pos_version = 3
        else:
            self.pos_version = 1
            self.min_channels = 12

        self.file.seek(0, 0)

        # V002 and V003 have header, read this (skip for V001)
        if self.pos_version > 1:
            signature = str(self.file.readline(), encoding='utf-8')
            self.pre_motion_position = int(self.file.readline())

            # number of channels for each frame
            self.min_channels = int(str(self.file.readline(), encoding='utf-8').split('=')[-1])
            self.bytes_in_frame = self.min_channels * 7 * 4  # channels * 4bytes * 7 readings

            self.sampling_rate = int(str(self.file.readline(), encoding='utf-8').split('=')[-1])
            self.frame_time = 1/self.sampling_rate * 1000000  # microseconds

            # extra fields in V003
            header_extra_fields = self.file.read(self.pre_motion_position-self.file.tell())
        else:
            self.bytes_in_frame = self.min_channels * 7 * 4  # this also holds for V001

        # get bytes in file by going to end, calculate how many frames available
        self.file.seek(0, 2)
        self.max_num_frames = (self.file.tell()-self.pre_motion_position) / self.bytes_in_frame

        # return to the beginning of the data section
        self.file.seek(self.pre_motion_position, 0)

    def give_motion_frame(self):
        """Read the next sample from the POS file and assign to coil objects.
        :returns: error code, packed bytestring with dataframe response
        """
        if self.motion_lines_read < self.max_num_frames:

            measurements = self.file.read(self.bytes_in_frame)

            # there appears to be no timestamp in the data
            timestamp = MocapParent.timestamp_to_microsecs(self.motion_lines_read * self.frame_time)

            # 7I is integers for: x, y, z, phi, theta, rms, extra
            measurements_by_coil = struct.iter_unpack('< 7f', measurements[:])
            #print('&&&',measurements_by_coil)
            for coilvals, coilobj in zip(measurements_by_coil, self.component.coils):
                floatvals = MocapParent.make_float_or_zero(coilvals)
                coilobj.set_args_to_vars(floatvals, mapping=self.mappings)

            self.component.timestamp = timestamp
            self.latest_timestamp = timestamp
            print('test timestamp!!', self.latest_timestamp)

            self.motion_lines_read += 1
            return 3, DataFrame(components=[self.component]).pack_components_to_df(), None

        # no more data available (static, give up)
        else:
            print("All the frames have been read")
            return 4, "No more frames left in mocap file"


if __name__ == "__main__":
    print("running main")

    if True:  # test POS parser
        p = POSParser('./data/Example4.pos')
        for i in range(10):
            mf, *_= p.give_motion_frame()
            print(mf)
        print(ET.tostring(p.xml_tree.getroot()))


    if True:  # test TSV parser
        c = TSVParser('./data/Example3.tsv')
        print('motion frame', c.give_motion_frame())
        mf, msg, *_ = c.give_motion_frame()
        print(ET.tostring(c.xml_tree.getroot()))

    if True:  # test BVH paser
        a = BVHParser('./data/Example2.bvh')
        print(len(a.marker_names), a.marker_names)
        print(len(a.marker_channels), a.marker_channels)
        print(ET.tostring(a.xml_tree.getroot()))

        print(a.num_frames)
        print(a.frame_time)
        print(a.file.closed)
        print(a.file.tell())

        mylabels = ['position', 'Yposition' ,'Zposition' ,'Zrotation', 'Xrotation', 'Yrotation']
        b = MocapParent.order_measurements_as_wave(mylabels, nchannels=7)
        print(a.xml_tree.getroot())


        a = BVHParser('./data/Example2.bvh')
        print(len(a.marker_names), a.marker_names)
        print(len(a.marker_channels), a.marker_channels)
        print(a.xml_tree.getroot())

        mappings = [MocapParent.order_measurements_as_wave(c,nchannels=7) for c in a.marker_channels]
        print(mappings)