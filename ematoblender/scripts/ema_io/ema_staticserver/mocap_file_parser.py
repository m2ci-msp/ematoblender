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
import json
from ..rtc3d_parser import DataFrame, Component6D, CoilBuilder6D

xml_skeleton_location = os.path.abspath(os.path.normpath(os.path.dirname(__file__) + os.sep +'parameter_skeleton.xml'))


class Mapping():
    """Control the reordering between the mocap file and the WAVE order."""
    def __init__(self, names_as_strings=None, mapping_as_list=None, angle_type='QUATERNION'):
        self.quat_inds = []
        self.euler_xyz = []

        if names_as_strings is not None:
            mapping_as_list = self.order_measurements_as_wave(names_as_strings, nchannels=6)
        if angle_type == 'QUATERNION':  # quaternions are OK
            if mapping_as_list is not None:
                self.q0ind, self.qxind, self.qyind, self.qzind, self.xind, self.yind, self.zind = mapping_as_list
            else:
                self.q0ind, self.qxind, self.qyind, self.qzind, self.xind, self.yind, self.zind = [i for i in range(7)]
                self.otherind = 8

            self.quat_inds = [self.q0ind, self.qxind, self.qyind, self.qzind]

        if angle_type == 'ELEVATION':
            self.quat_inds = [None]
            if mapping_as_list is not None:
                _, pi, theta, d, self.xind, self.yind, self.zind = mapping_as_list
            self.euler_xyz = [theta, 0,  pi]

        if angle_type == 'EULER':
            self.quat_inds = [None]
            if mapping_as_list is not None:
                ex, ey, ez, self.xind, self.yind, self.zind = mapping_as_list
            self.euler_xyz = [ex, ey, ez]



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

    def convert_to_quat(self, measurementlist):
        """Convert the angle information in the mapping into Quaternions
        Return q0, qx, qy, qz.
        """
        print('converting {} to quats'.format(measurementlist))
        if all(x is not None for x in self.quat_inds) and all([measurementlist[x] is not None for x in self.quat_inds]):
            print(self.make_float_or_zero([measurementlist[i] for i in self.quat_inds]))
            return self.make_float_or_zero([measurementlist[i] for i in self.quat_inds])

        elif all([measurementlist[x] is not None for x in self.euler_xyz]):
            x, y, z = [measurementlist[x] is not None for x in self.euler_xyz]
            # TODO: This presumes the angle application order XYZ # TODO: Check source
            # TODO: Source is http://www.euclideanspace.com/maths/geometry/rotations/conversions/eulerToQuaternion/

            c1, c2, c3 = [math.cos(math.radians(i)/2) for i in [z, y, x]]  # z is yaw, y is pitch, x is roll
            s1, s2, s3 = [math.sin(math.radians(i)/2) for i in [z, y, x]]  # z is yaw, y is pitch, x is roll

            # convert euler rotation angles to quaternion
            q0 = c1*c2*c3 - s1*s2*s3
            qx = s1*s2*c3 + c1*c2*s3
            qy = s1*c2*c3 + c1*s2*s3
            qz = c1*s2*c3 - s1*c2*s3
            return self.make_float_or_zero((q0, qx, qy, qz))
        else:
            raise ValueError('Cannot convert None values to quaternions')

    def give_in_wave_order(self, measurementlist):
        """Given some measurement list that conforms to the mapping, return the measurements re-ordered."""
        measurementlist += [0 for j in range(7)]  # pad in case too short
        return [measurementlist[i] if i is not None else 0 for i in
                [self.q0ind, self.qxind, self.qyind, self.qzind, self.xind, self.yind, self.zind]]

    @staticmethod
    def channel_label_to_attrs(label):
        """Semantically parse label names."""
        label = label.lower()

        # rotation vs location
        if 'rot' in label or 'q' in label: # rotation label
            location = False
            rotation = True
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
        attributes = [(i, Mapping.channel_label_to_attrs(l)) for i, l in enumerate(labels)]

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
                            for orientation in [rots, locs] for letter in [x, y, z]] # first orientation is impossible as placeholder for q0
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
        if extension == 'json':
            return JSONParser(filename)
        raise ValueError("Bad mocap file type: {}".format(extension))
    factory = staticmethod(factory)


class MocapParent(object):
    """Parent class to Mocap objects.
    All Mocap file parser objects have the attributes:

    FILE ATTRIBUTES
    - file (the file object with the data)
    - file_name (filename)
    - format (extension)
    - wave_name, video_name (file names of associated audio/video files)
    - xml_tree (XML root object for parameter XML string (filled meaningfully later))

    FRAME ATTRIBUTES
    - motion_lines_read (position in reading by line)
    - pre_motion_position (position where reading starts, bytes from start, after this can use readline() to get frames)
    - max_num_frames (for static file, the number of frames that can  be read before looping)
    - latest_timestamp (the most recently read timestamp, in microseconds)

    SAMPLING RATE ATTRIBUTES
    - frame_time (number of microseconds per frame)
    - frame_times (list of time difference between frames in seconds)

    COIL ATTRIBUTES
    - n_coils (number of EMA coils represented in file)
    - marker_names (coil names as listed in file header)
    - marker_channels (names of the measurements taken for each marker/coil in order (eg [xrot,  yrot, zrot, x, y, z]))
        (note that this is presumed the same for every coil)

    CONVERSION TO STANDARD FORMAT
    - mappings (list indicating how the file's values should be reordered to emulate WAVE ordering )

    ACTUAL LOCATION DATA
    - component (component attribute as defined in rtc3d parser)

    METHODS COMMON TO ALL MOCAP FORMATS:
    - read_header (process the file header, populating attributes with the info)
    - give_motion_frame (read and process one motion frame, returning a dataframe object with the info)
    - update_xml_initial (update certain static xml attributes from the object's attributes)
    - update_xml_stats (update XML to reflect the current state of the file reading)
    - reset_motion_section (set file to position at start of the motion section)
    - search_for_multimodal (scan the file's directory for likely audio/video candidates)
    - order_measurements_as_wave (yield the mapping between the dimensions given per coil and the order
        they should be in if they were streamed from the WAVE)

    STATIC METHODS
    - timestamp_to_microsecs
    - make_float_or_zero
    - channel_label_to_attrs (do NLP to gather whether name represents loc, rot, axis, format)

    """

    file_read_mode = 'r'

    def __init__(self, filename):
        print('initialising a mocap parent')

        # open the file
        filename = filename if os.path.isabs(filename) else os.path.normpath(os.getcwd()+os.path.sep + filename)
        self.file = open(filename, self.__class__.file_read_mode)
        self.file_name = self.file.name
        self.format = os.path.splitext(filename)[-1]

        self.xml_tree = ET.parse(xml_skeleton_location)
        self.wave_name, self.video_name = self.search_for_multimodal()

        # capture the position within the file
        self.motion_lines_read = 0
        self.pre_motion_position = NotImplemented
        self.max_num_frames = NotImplemented
        self.latest_timestamp = NotImplemented

        # populated in subclasses from the header/pre-reading
        self.frame_time = NotImplemented
        self.frame_times = NotImplemented

        # perhaps these could be coil objects
        self.n_coils = NotImplemented
        self.marker_names = []
        self.marker_channels = []

        # arbitrary large number,
        # later represents the number of dimensions measured to decide between 6d and 3d representations
        self.min_dimensions = 100
        self.mappings = NotImplemented

        self.component = NotImplemented  # an initial component attribute

        #  process the file header
        self.read_header()
        self.update_xml_initial()

    def get_sampling_rate(self):
        if self.frame_time is NotImplemented:
            return None
        else:
            return 1000000/self.frame_time  # microseconds

    @staticmethod
    def timestamp_to_microsecs(timestamp):
        """
        Get timestamp as string or int. Convert to ms.
        """

        # ts is a float, presume  it's in seconds
        if type(timestamp) == float or (type(timestamp) == str and timestamp.find('.')):
            timestamp = math.floor(float(timestamp) * 1000000)  # seconds to microseconds

        # ts is an integer or string of integer, presumably milliseconds. keep in same format
        elif (type(timestamp) == str and timestamp.isnumeric()) or type(timestamp) == int:
            timestamp = int(timestamp)
        else:
            raise TypeError
        return timestamp

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
        self.xml_tree.find("./The_3D/Frequency").text = str(self.get_sampling_rate())
        self.xml_tree.find("./The_6D/Frequency").text = str(self.get_sampling_rate())

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

    def give_all_motion_frames(self):
        """Return all datafiles from start to end of file.
        File position is not reset afterwards.
        """
        self.reset_motion_section()
        dflist = []

        while True:
            status, frame, *ts = self.give_motion_frame()
            if status != 3:
                break
            dflist.append(frame)
        return dflist


class JSONParser(MocapParent):
    """
    Class to parse pre-processed JSON files (of the Trier dataset) into DataFrame objects.
    Do not yet incorporate correspondences.
    Must be able to be reconstructed into JSON format for the C++ server.
    """

    def read_header(self):
        """Read in the JSON file"""
        print('Reading in JSON file, this may take a while')
        self.json = json.loads(self.file.read())
        print(self.json.keys())
        self.motion_lines_read = 0

        self.marker_names = self.json["channels"].keys()
        timestamps = self.json["timestamps"]

        self.max_num_frames = len(timestamps)
        self.frame_time = 1 / self.json["samplingFrequency"]

        #setup a mapping between EX EY EZ X Y Z to wave
        self.mappings = Mapping(mapping_as_list=[0, 1, 2, 3, 4, 5], angle_type='EULER')
        self.min_channels = len(self.marker_names)
        self.min_dimensions = 6
        self.component = Component6D(fileparser=self)

    def give_motion_frame(self):
        """ Return angle, position and timestamp information for a file. """
        n = self.motion_lines_read
        measurements_by_coil = []
        for ch in self.marker_names:  # TODO: Fill from reading header
            angles = self.json["channels"][ch]['eulerAngles'][n*3:n*3+3]
            position = self.json["channels"][ch]["position"][n*3:n*3+3]
            measurements_by_coil.append(angles+position)
        timestamp = MocapParent.timestamp_to_microsecs(self.json["timestamps"][n])
        print(measurements_by_coil)

        self.component.coils = [CoilBuilder6D.build_from_mapping(self.mappings, onecoil)
                                for onecoil in measurements_by_coil]

        self.component.timestamp = timestamp
        self.latest_timestamp = timestamp

        self.motion_lines_read += 1
        return 3, DataFrame(components=[self.component]).pack_all(), self.latest_timestamp


class BVHParser(MocapParent):
    """
    Class to parse .bvh motion capture files (Biovision Hierarchical Data).
    """

    def __init__(self, filename):
        """ Initialise the BVH Parser object. """

        super().__init__(filename)

        # get the mappings between the measurements and wave orderings
        self.mappings = Mapping(names_as_strings=self.marker_channels[0])

        self.component = Component6D(fileparser=self)  # builds coil objects within init

    def __str__(self):
        return "bvh mocap file with these coils: {}".format(str(self.marker_names))

    def read_header(self):
        """Read the BVH header and put in neutral format."""

        line = self.file.readline()     # First line should be 'HIERARCHY'

        # while in the header
        while not line.startswith("MOTION"):
            strippedline = line.strip(' \t\n\r')

            # capture root/joint names sequentially
            if strippedline.startswith('ROOT') or strippedline.startswith('JOINT'):  # get a marker name
                _, name = strippedline.split()
                self.marker_names.append(name)

            # capture channel information sequentially (should correspond to joint information)
            elif line.strip('\t\n ').startswith('CHANNELS'):  # get the marker's channels
                channelline = strippedline.split(' ')
                num_channels = int(channelline[1])
                if num_channels != len(channelline[2:]):
                    raise ValueError
                self.min_dimensions = num_channels if num_channels < self.min_dimensions else self.min_dimensions
                self.marker_channels.append(channelline[2:])  # append a tuple of the channels for the marker

            line = self.file.readline()
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

            # update Component6D/Coil objects from file
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
            self.component.coils = [CoilBuilder6D.build_from_mapping(self.mappings, coilvals)
                                    for coilvals in measurements_by_coil]

            return 3, DataFrame(components=[self.component]).pack_all(), None

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

        print(self.marker_channels)

        # mapping of TSV is sens_id, sens_status, x, y, z, q0, qx, qy, qz
        # desired order is q0, qx, qy, qz, x, y, z
        self.mappings = Mapping(mapping_as_list=[5, 6, 7, 8, 2, 3, 4])

        self.component = Component6D(fileparser=self)  # builds first component objects within init

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
        timestamps = [MocapParent.timestamp_to_microsecs(
                                                        line.strip('\n\r').split('\t')[self.timestamp_index]
                                                        ) for line in self.file.readlines()]
        self.max_num_frames = len(timestamps)
        self.frame_times = [t - s for s, t in zip(timestamps, timestamps[1:])]

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

            # update Component6D/Coil objects from file
            # read the next line, split into meta (eg timestamp etc) and data
            if self.file.closed:
                print(self.file_name)
                print(self.file)
                print('THE FILE IS CLOSED WHY?')
                raise Exception
            measurements = self.file.readline().rstrip('\n')
            meta, all_measurements = measurements.split('\t')[:self.extra_left_fields], \
                                     measurements.split('\t')[self.extra_left_fields:]
            measurements_by_coil = [all_measurements[x:x+self.fields_per_sensor]
                                    for x in range(0, len(all_measurements), self.fields_per_sensor)]

            # print('@@@', self.fields_per_sensor,len(measurements_by_coil[0]))
            # get the timestamp, convert to ms if seconds
            timestamp = meta[self.timestamp_index]
            timestamp = MocapParent.timestamp_to_microsecs(timestamp)  # timestamp now in microseconds

            print("about to alter component", str(self.component)[:50])
            print('measurements_by_coil:', measurements_by_coil)
            self.component.coils = [CoilBuilder6D.build_from_mapping(self.mappings, coilvals)
                                    for coilvals in measurements_by_coil]

            self.component.timestamp = timestamp # TODO: Are there any other fields that are missing? Eg should I send WavID?
            self.latest_timestamp = timestamp
            #print(self.component)

            return 3, DataFrame(components=[self.component]).pack_all(), self.latest_timestamp

        # no more data available (static, give up)
        else:
            print("All the frames have been read")
            return 4, "No more frames left in mocap file"


class POSParser(MocapParent):
    """Parses Carstens motion capture files for AG500 and AG501 machines."""

    file_read_mode = 'rb'

    def __init__(self, filename):
        """ Initialise the POS parser object. """
        super().__init__(filename)
        # POS file is a binary, read header then open in bytes

        # the mapping between pos data format and WAVE order is known
        # mapping of POS is: x, y, z, phi, theta, rms, extra
        # desired order for WAVE is: q0, qx, qy, qz, x, y, z
        # based on standard Euler rotation with order XYZ, if ph
        self.mappings = Mapping(mapping_as_list=[None, 3, 4, None, 0, 1, 2], angle_type='ELEVATION')

        self.component = Component6D(fileparser=self)  # build the first component within the mocap object

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

            sampling_rate = int(str(self.file.readline(), encoding='utf-8').split('=')[-1])
            self.frame_time = 1/sampling_rate * 1000000  # microseconds

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

            # update the timestamp
            timestamp = self.timestamp_to_microsecs(self.motion_lines_read * self.frame_time)
            self.component.timestamp, self.latest_timestamp = timestamp, timestamp
            print('BVH latest timestamp:', self.latest_timestamp)

            # 7f is floats for: x, y, z, phi, theta, rms, extra
            measurements_by_coil = struct.iter_unpack('< 7f', self.file.read(self.bytes_in_frame))
            # for m in measurements_by_coil:
            #     print('POS measurement by coil:', m)
            #
            # print([m for m in measurements_by_coil])

            self.component.coils = [CoilBuilder6D.build_from_mapping(self.mappings, coilvals)
                                    for coilvals in measurements_by_coil]
            # print([(self.mappings, coilvals)for coilvals in measurements_by_coil])
            assert len(self.component.coils) > 0  # at least one coil must be made

            # update the line statistics
            self.motion_lines_read += 1
            return 3, DataFrame(components=[self.component]).pack_all(), None

        # no more data available (static, give up)
        else:
            print("All the frames have been read")
            return 4, "No more frames left in mocap file"


if __name__ == "__main__":
    print("running main")

    if True:  # test JSON parser
        from ematoblender.scripts.ema_io.rtc3d_parser import JSONBuilder
        p = JSONParser('F:\\trier_data\\json\\aligned.json')
        for i in range(5):
            status, dfbytes, ts = p.give_motion_frame()
            df = DataFrame(rawdf=dfbytes)
            print(df.to_tsv())

            print(JSONBuilder.pack_wrapper(df, [1,2,3,4], [0, 1, 2,3]))

    if True:  # test POS parser
        p = POSParser('./data/Example4.pos')
        for i in range(10):
            mf, *_ = p.give_motion_frame()
            print('Motion frame from POSParser', mf)
        print('ET parameter string for POS Parser', ET.tostring(p.xml_tree.getroot()))

    if True:  # test TSV parser
        c = TSVParser('./data/Example3.tsv')
        print('motion frame', c.give_motion_frame())
        mf, msg, *_ = c.give_motion_frame()
        print('Parameter string for TSV parser', ET.tostring(c.xml_tree.getroot()))

    if True:  # test BVH paser
        a = BVHParser('./data/Example2.bvh')
        print('marker names', len(a.marker_names), a.marker_names)
        print('marker channels', len(a.marker_channels), a.marker_channels)
        print('parameter string', ET.tostring(a.xml_tree.getroot()))

        print('num_frames', a.num_frames)
        print('frame_time', a.frame_time)
        print('is BVH file closed',a.file.closed)
        print('position in BVH file', a.file.tell())

        mylabels = ['position', 'Yposition' ,'Zposition' ,'Zrotation', 'Xrotation', 'Yrotation']
        b = Mapping.order_measurements_as_wave(mylabels, nchannels=7)
        print(mylabels, 'get reordered as', b)
        print(a.xml_tree.getroot())


        a = BVHParser('./data/Example2.bvh')
        print('marker names', len(a.marker_names), a.marker_names)
        print('marker channels', len(a.marker_channels), a.marker_channels)
        print(a.xml_tree.getroot())

        mappings = [Mapping.order_measurements_as_wave(c,nchannels=7) for c in a.marker_channels]
        print(mappings)
