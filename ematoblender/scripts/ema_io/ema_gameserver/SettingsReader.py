__author__  = "Alexander Hewer"
__email__   = "hewer@coli.uni-saarland.de"

import json

from .GameServerSettings import GameServerSettings
from .ExternalFittingServerSettings import ExternalFittingServerSettings

class SettingsReader:

    def read_from(fileName):

        fileStream = open(fileName, "r")
        settingsDictionary = json.load(fileStream)

        __class__.set_game_server_settings(settingsDictionary["gameServerSettings"])
        __class__.set_external_fitting_server_settings(settingsDictionary["externalFittingServerSettings"])


    def set_game_server_settings(settings):

        GameServerSettings.useHeadCorrection = settings["useHeadCorrection"]
        GameServerSettings.host = settings["host"]
        GameServerSettings.port = settings["port"]
        GameServerSettings.rtcHost = settings["rtcHost"]
        GameServerSettings.rtcPort = settings["rtcPort"]

        smoothing = settings["smoothing"]
        if smoothing["mode"] == "milliseconds":

            GameServerSettings.smoothMs = smoothing["value"]
            GameServerSettings.smoothFrames = None

        else:

            GameServerSettings.smoothMs = None
            GameServerSettings.smoothFrames = smoothing["value"]

    def set_external_fitting_server_settings(settings):

        ExternalFittingServerSettings.host = settings["host"]
        ExternalFittingServerSettings.port = settings["port"]

        ExternalFittingServerSettings.neededAmountForFixedSpeaker = settings["neededAmountForFixedSpeaker"]

        coilCorrespondences = settings["coilCorrespondences"]
        ExternalFittingServerSettings.modelVertexIndices = coilCorrespondences["modelVertexIndices"]
        ExternalFittingServerSettings.coilPositionNames = coilCorrespondences["coilPositionNames"]
        ExternalFittingServerSettings.coilIndices = coilCorrespondences["coilIndices"]
