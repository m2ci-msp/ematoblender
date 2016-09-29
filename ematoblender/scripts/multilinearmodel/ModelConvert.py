'''
   This file is part of the multilinear-model-tools.
   These tools are meant to derive a multilinear tongue model or
   PCA palate model from mesh data and work with it.

   Some code of the multilinear-model-tools is based on
   Timo Bolkart's work on statistical analysis of human face shapes,
   cf. https://sites.google.com/site/bolkartt/

   Copyright (C) 2016 Alexander Hewer

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

from math import sqrt

from .ModelData import ModelData
from .ModelWeights import ModelWeights

class ModelConvert:

    def __init__(self, modelData):

        self.modelData = modelData
        self.scaleFactorSpeaker = sqrt(modelData.dimSpeakerOriginal)
        self.scaleFactorPhoneme = sqrt(modelData.dimPhonemeOriginal)

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
