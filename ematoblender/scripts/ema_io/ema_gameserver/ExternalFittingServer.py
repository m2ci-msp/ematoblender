__author__  = "Alexander Hewer"
__credits__ = "Kristy James"
__email__   = "hewer@coli.uni-saarland.de"

import socket
import json

from .ActionBuilder import ActionBuilder
from .ExternalFittingServerSettings import ExternalFittingServerSettings as settings
from .GameServerSettings import GameServerSettings as gameSettings

class ExternalFittingServer:

    def __init__(self):

        self.processedFrames = 0
        self.actionBuilder = ActionBuilder()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #--------------------------------------------------------------------------#
    # PUBLIC METHODS
    #--------------------------------------------------------------------------#

    def fit(self, dataFrame):

        # fix speaker if we have enough frames
        if self.processedFrames == settings.neededAmountForFixedSpeaker:

            self.send(self.actionBuilder.build_fix_speaker_action())

        # fit frame
        coilPositions = self.__extract_coil_positions_from(dataFrame)
        timeStamp = self.__extract_time_stamp_from(dataFrame)

        self.send(self.actionBuilder.build_fit_action(coilPositions, timeStamp))

        self.processedFrames += 1

    #--------------------------------------------------------------------------#

    def reset(self):

        self.processedFrames = 0
        self.send(self.actionBuilder.build_reset_action())

    #--------------------------------------------------------------------------#

    def set_model_vertex_indices(self):

        self.send(
            self.actionBuilder.build_set_model_indices_action(
                settings.modelVertexIndices)
        )

    #--------------------------------------------------------------------------#

    def send(self, dataToBeSent):

        self.socket.sendto(bytes(json.dumps(dataToBeSent), "utf-8"),
                           (settings.host, settings.port)
        )

    #--------------------------------------------------------------------------#
    # PRIVATE METHODS
    #--------------------------------------------------------------------------#

    def __extract_coil_positions_from(self, dataFrame):

        # extract needed coil objects from data frame
        coilObjects = [dataFrame.components[0].coils[i] for i in settings.coilIndices]

        # now get the actual coil positions
        if gameSettings.useHeadCorrection == False:
            coilPositions = [position for coil in coilObjects for position in coil.abs_loc]
        else:
            coilPositions = [position for coil in coilObjects for position in coil.bp_corr_loc]

        return coilPositions

    #--------------------------------------------------------------------------#

    def __extract_time_stamp_from(self, dataFrame):

        return dataFrame.components[0].timestamp / 1000000

    #--------------------------------------------------------------------------#
