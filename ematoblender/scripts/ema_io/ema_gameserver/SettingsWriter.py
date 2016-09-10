__author__  = "Alexander Hewer"
__email__   = "hewer@coli.uni-saarland.de"

import json

from .GameServerSettings import GameServerSettings
from .ExternalFittingServerSettings import ExternalFittingServerSettings
from .CoilSettings import CoilSettings
from .OverrideSettings import OverrideSettings

class SettingsWriter:

    def write_to(fileName):

        fileStream = open(fileName, "w")
        settingsDictionary = {}

        settingsDictionary["gameServerSettings"] = __class__.get_game_server_settings()
        settingsDictionary["externalFittingServerSettings"] = __class__.get_external_fitting_server_settings()
        settingsDictionary["coilSettings"] = __class__.get_coil_settings()
        settingsDictionary["overrideSettings"] = __class__.get_override_settings()

        fileStream.write(json.dumps(settingsDictionary, indent=4, sort_keys=True))



    def get_game_server_settings():

        settings = {}
        settings["host"] = GameServerSettings.host
        settings["port"] = GameServerSettings.port
        settings["rtcHost"] = GameServerSettings.rtcHost
        settings["rtcPort"] = GameServerSettings.rtcPort
        settings["bitePlateFrontIsBack"] = GameServerSettings.bitePlateFrontIsBack

        settings["useHeadCorrection"] = GameServerSettings.useHeadCorrection

        if GameServerSettings.useHeadCorrection:
            settings["bitePlane"] = GameServerSettings.bitePlane

        return settings

    def get_external_fitting_server_settings():

        settings = {}

        settings["host"] = ExternalFittingServerSettings.host
        settings["port"] = ExternalFittingServerSettings.port
        settings["neededAmountForFixedSpeaker"] = ExternalFittingServerSettings.neededAmountForFixedSpeaker

        coilCorrespondences = {}

        coilCorrespondences["modelVertexIndices"] = ExternalFittingServerSettings.modelVertexIndices
        coilCorrespondences["coilPositionNames"] = ExternalFittingServerSettings.coilPositionNames
        coilCorrespondences["coilIndices"] = ExternalFittingServerSettings.coilIndices

        settings["coilCorrespondences"] = coilCorrespondences

        settings["weights"] = ExternalFittingServerSettings.weights
        settings["priorSize"] = ExternalFittingServerSettings.priorSize

        return settings

    def get_coil_settings():

        return CoilSettings.coils

    def get_override_settings():

        return OverrideSettings.overrides
