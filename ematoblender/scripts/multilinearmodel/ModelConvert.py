__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

from math import sqrt

from .ModelData import ModelData
from .ModelWeights import ModelWeights

class ModelConvert:

    def __init__(self, modelData):

        self.modelData = modelData
        self.scaleFactorIdentity = sqrt(modelData.dimIdentity)
        self.scaleFactorExpression = sqrt(modelData.dimExpression)

    def to_weights(self, weights):

        result = ModelWeights()
        result.idWeights  = weights.idWeights / self.scaleFactorIdentity
        result.idWeights += self.modelData.identityCenter

        result.expWeights  = weights.expWeights / self.scaleFactorExpression
        result.expWeights += self.modelData.expressionCenter

        return result

    def to_variations(self, weights):

        result = ModelWeights()
        result.idWeights -= self.modelData.identityCenter
        result.idWeights  = weights.idWeights * self.scaleFactorIdentity

        result.expWeights -= self.modelData.expressionCenter
        result.expWeights  = weights.expWeights * self.scaleFactorExpression

        return result
