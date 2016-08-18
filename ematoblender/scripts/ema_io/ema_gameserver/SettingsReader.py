__author__  = "Alexander Hewer"
__email__   = "hewer@coli.uni-saarland.de"

import json

from .GameServerSettings import GameServerSettings
from .ExternalFittingServerSettings import ExternalFittingServerSettings
from .CoilSettings import CoilSettings

class SettingsReader:

    def read_from(fileName):

        fileStream = open(fileName, "r")
        settingsDictionary = json.load(fileStream)

        __class__.set_game_server_settings(settingsDictionary["gameServerSettings"])
        __class__.set_external_fitting_server_settings(settingsDictionary["externalFittingServerSettings"])
        __class__.set_coil_settings(settingsDictionary["coilSettings"])

    def set_game_server_settings(settings):

        GameServerSettings.host = settings["host"]
        GameServerSettings.port = settings["port"]
        GameServerSettings.rtcHost = settings["rtcHost"]
        GameServerSettings.rtcPort = settings["rtcPort"]
        GameServerSettings.bitePlateFrontIsBack = settings["bitePlateFrontIsBack"]

    def set_external_fitting_server_settings(settings):

        ExternalFittingServerSettings.host = settings["host"]
        ExternalFittingServerSettings.port = settings["port"]

        ExternalFittingServerSettings.neededAmountForFixedSpeaker = settings["neededAmountForFixedSpeaker"]

        coilCorrespondences = settings["coilCorrespondences"]
        ExternalFittingServerSettings.modelVertexIndices = coilCorrespondences["modelVertexIndices"]
        ExternalFittingServerSettings.coilPositionNames = coilCorrespondences["coilPositionNames"]
        ExternalFittingServerSettings.coilIndices = coilCorrespondences["coilIndices"]

    def set_coil_settings(settings):

        CoilSettings.coils = settings
        CoilSettings.save()
