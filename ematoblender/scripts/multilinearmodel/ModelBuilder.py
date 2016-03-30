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

        self.modelData.dimTarget = rawModel['ModeDimensions'][0]
        self.modelData.dimIdentity = rawModel['ModeDimensions'][1]
        self.modelData.dimExpression = rawModel['ModeDimensions'][2]

        self.modelData.model = numpy.array(rawModel['MultilinearModel'])
        self.modelData.mean = numpy.array(rawModel['Mean'])
        self.modelData.identityCenter = numpy.array(rawModel['ModeMean'][0:self.modelData.dimIdentity])
        self.modelData.expressionCenter = numpy.array(rawModel['ModeMean'][self.modelData.dimIdentity:])
        return self.modelData
