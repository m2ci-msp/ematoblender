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

import mathutils

from .ModelData import ModelData
from .ModelSpace import ModelSpace
from .ModelConvert import ModelConvert

class ModelReconstructor:

    def __init__(self, modelData):

        self.modelData = modelData
        self.modelSpace = ModelSpace(modelData)
        self.convert = ModelConvert(modelData)

    def get_shape_space_origin(self):

        result = []

        for i in range(0, self.modelData.dimVertex // 3):

            x = self.modelData.shapeSpaceOrigin[i*3 + 0]
            y = self.modelData.shapeSpaceOrigin[i*3 + 1]
            z = self.modelData.shapeSpaceOrigin[i*3 + 2]
            position = mathutils.Vector()
            position[0] = x
            position[1] = y
            position[2] = z
            result.append(position)

        return result


    def reconstruct_from_variations(self, variations):

        weights = self.convert.to_weights(variations)
        return self.reconstruct_from_weights(weights)

    def reconstruct_from_weights(self, weights):

        target = self.__reconstruct_target_from_weights(weights)

        result = []

        for i in range(0, self.modelData.dimVertex // 3):

            x = target[i*3 + 0]
            y = target[i*3 + 1]
            z = target[i*3 + 2]
            position = mathutils.Vector()
            position[0] = x
            position[1] = y
            position[2] = z
            result.append(position)

        return result

    def __reconstruct_target_from_weights(self, weights):

        speaker = self.modelSpace.speaker(weights.speakerWeights)
        result = speaker.dot(weights.phonemeWeights) + self.modelData.shapeSpaceOrigin
        return result
