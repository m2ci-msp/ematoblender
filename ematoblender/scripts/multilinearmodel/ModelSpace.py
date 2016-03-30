__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

import numpy

from .ModelData import ModelData

class ModelSpace:

    def __init__(self, modelData):

        self.__modelIdentity = []
        self.modelData = modelData
        self.__generate_model_identity()

    def identity(self, idWeights):

        result = numpy.zeros(shape=(self.modelData.dimTarget, self.modelData.dimExpression))

        for i_id in range(0, self.modelData.dimIdentity):
            result += idWeights[i_id] * self.__modelIdentity[i_id]

        return result

    def __generate_model_identity(self):

        for i_identity in range(0, self.modelData.dimIdentity):

            tmp = numpy.zeros(shape=(self.modelData.dimTarget, self.modelData.dimExpression))

            for i_expression in range(0, self.modelData.dimExpression):

                for i_target in range(0, self.modelData.dimTarget):

                    index = i_target +\
                            i_identity * self.modelData.dimTarget +\
                            i_expression * self.modelData.dimTarget * self.modelData.dimIdentity

                    tmp[i_target, i_expression] = self.modelData.model[index]

            self.__modelIdentity.append(tmp)
