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

import json
import numpy

from .ModelData import ModelData

class ModelBuilder:

    def __init__(self):

        self.modelData = ModelData()

    def build_from(self, modelFile):

        with open(modelFile) as inputFile:
            rawModel = json.load(inputFile)

        self.modelData.dimVertex = rawModel['Dimensions']['VertexMode']
        self.modelData.dimSpeaker = rawModel['Dimensions']['TruncatedSpeakerMode']
        self.modelData.dimPhoneme = rawModel['Dimensions']['TruncatedPhonemeMode']

        self.modelData.dimSpeakerOriginal = rawModel['Dimensions']['OriginalSpeakerMode']
        self.modelData.dimPhonemeOriginal = rawModel['Dimensions']['OriginalPhonemeMode']

        self.modelData.coreTensor = numpy.array(rawModel['CoreTensor'])
        self.modelData.shapeSpaceOrigin = numpy.array(rawModel['ShapeSpace']['Origin'])
        self.modelData.speakerMeanWeights = numpy.array(rawModel['MeanWeights']['SpeakerMode'])
        self.modelData.phonemeMeanWeights = numpy.array(rawModel['MeanWeights']['PhonemeMode'])
        return self.modelData
