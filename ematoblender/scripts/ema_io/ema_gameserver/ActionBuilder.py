__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

class ActionBuilder:

    def fit(self, coilPositions, timeStamp):

        action = self.__base_action("FIT")
        action["points"] = coilPositions
        action["timeStamp"] = timeStamp
        return action

    def fix_speaker(self):

        return self.__base_action("FIX_SPEAKER")

    def reset(self):

        return self.__base_action("RESET")

    def set_model_indices(self, indices):

        action = self.__base_action("SET_MODEL_INDICES")
        action["indices"] = indices
        return action

    def __base_action(self, id):

        action = {}
        action["id"] = id
        return action
