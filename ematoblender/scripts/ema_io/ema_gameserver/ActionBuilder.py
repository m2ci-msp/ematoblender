__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

class ActionBuilder:

    def build_fit_action(self, coilPositions, timeStamp):

        action = self.__base_action("FIT")
        action["points"] = coilPositions
        action["timeStamp"] = timeStamp
        return action

    def build_fix_speaker_action(self):

        return self.__base_action("FIX_SPEAKER")

    def build_reset_action(self):

        return self.__base_action("RESET")

    def build_set_model_indices_action(self, indices):

        action = self.__base_action("SET_MODEL_INDICES")
        action["indices"] = indices
        return action

    def __base_action(self, id):

        action = {}
        action["id"] = id
        return action
