__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

import numpy

from .ModelData import ModelData

class ModelSpace:

    def __init__(self, modelData):

        self.__modelSpeaker = []
        self.modelData = modelData
        self.__generate_model_speaker()

    def speaker(self, speakerWeights):

        result = numpy.zeros(shape=(self.modelData.dimVertex, self.modelData.dimPhoneme))

        for i_speaker in range(0, self.modelData.dimSpeaker):
            result += speakerWeights[i_speaker] * self.__modelSpeaker[i_speaker]

        return result

    def __generate_model_speaker(self):

        for i_speaker in range(0, self.modelData.dimSpeaker):

            tmp = numpy.zeros(shape=(self.modelData.dimVertex, self.modelData.dimPhoneme))

            for i_phoneme in range(0, self.modelData.dimPhoneme):

                for i_vertex in range(0, self.modelData.dimVertex):

                    index = i_speaker * self.modelData.dimPhoneme * self.modelData.dimVertex +\
                            i_phoneme * self.modelData.dimVertex +\
                            i_vertex

                    tmp[i_vertex, i_phoneme] = self.modelData.coreTensor[index]

            self.__modelSpeaker.append(tmp)
