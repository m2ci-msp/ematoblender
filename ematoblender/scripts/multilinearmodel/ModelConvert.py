__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

from math import sqrt

from .ModelData import ModelData
from .ModelWeights import ModelWeights

class ModelConvert:

    def __init__(self, modelData):

        self.modelData = modelData
        self.scaleFactorSpeaker = sqrt(modelData.dimSpeaker)
        self.scaleFactorPhoneme = sqrt(modelData.dimPhoneme)

    def to_weights(self, weights):

        result = ModelWeights()
        result.speakerWeights  = weights.speakerWeights / self.scaleFactorSpeaker
        result.speakerWeights += self.modelData.speakerMeanWeights

        result.phonemeWeights  = weights.phonemeWeights / self.scaleFactorPhoneme
        result.phonemeWeights += self.modelData.phonemeMeanWeights

        return result

    def to_variations(self, weights):

        result = ModelWeights()
        result.speakerWeights -= self.modelData.speakerMeanWeights
        result.speakerWeights  = weights.speakerWeights * self.scaleFactorSpeaker

        result.phonemeWeights -= self.modelData.phonemeMeanWeights
        result.phonemeWeights  = weights.phonemeWeights * self.scaleFactorPhoneme

        return result
