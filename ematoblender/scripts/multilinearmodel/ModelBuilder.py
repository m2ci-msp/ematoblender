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
        self.modelData.dimSpeaker = rawModel['Dimensions']['SpeakerMode']
        self.modelData.dimPhoneme = rawModel['Dimensions']['PhonemeMode']

        self.modelData.coreTensor = numpy.array(rawModel['CoreTensor'])
        self.modelData.shapeSpaceOrigin = numpy.array(rawModel['ShapeSpace']['Origin'])
        self.modelData.speakerMeanWeights = numpy.array(rawModel['MeanWeights']['SpeakerMode'])
        self.modelData.phonemeMeanWeights = numpy.array(rawModel['MeanWeights']['PhonemeMode'])
        return self.modelData
