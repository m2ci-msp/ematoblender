__author__ = "Alexander Hewer"
__credits__ = "Kristy James"

import mathutils
from .biteplate_headcorr import HeadCorrector
from . import data_manipulation as dm
from ...ema_blender import coil_info as ci

class ReferencePointBuilder:

    def __init__(self, headCorrector):

        self.headCorrector = headCorrector

    def load_live(self, serverobj, seconds=5):
        """Using the server object, """
        response = self.headCorrector.inform_recording_start()

        # if response is to abort:
        if not response == 1:
            print("Live streaming aborted.")

        # if streaming ready, stream biteplate recording for 5 seconds
        else:
            dfs = self.headCorrector.record_for_seconds(serverobj, secs=seconds)
            av = self.headCorrector.process_frames_pre_calc(dfs)
            self.__compute_origin_shift(av)
            self.headCorrector.inform_recording_end()


    def __compute_origin_shift(self, df):

        # perform head correction and project to bite plane
        dm.head_corr_bp_correct(df, self.headCorrector.biteplane, self.headCorrector.refplane)

        # get reference coil and set shifted origin in biteplane
        self.headCorrector.biteplane.shiftedOrigin =  mathutils.Vector((df.give_coils()[ci.find_sensor_index('REF')].bp_corr_loc))
        print(self.headCorrector.biteplane.shiftedOrigin)
