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
