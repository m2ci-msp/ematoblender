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
__credits__ = "Kristy James"
__email__ = "hewer@coli.uni-saarland.de"

import numpy
import mathutils

from .ModelBuilder import ModelBuilder
from .ModelReconstructor import ModelReconstructor
from .ModelWeights import ModelWeights

# Class for binding a blender game engine mesh to a multilinear model
class GameMeshBinding:

    # constructor
    #
    # parameters:
    #
    # - modelFileName: fileName of model file
    # - gameMesh: mesh associated to the model in the game engine
    #
    # The constructor initializes the model data structures
    # and creates a lookup table between model vertices and
    # game engine mesh vertices
    #
    def __init__(self, modelFileName, gameMesh):

        # set gameMesh
        self.__gameMesh = gameMesh

        # initialize model reconstructor
        builder = ModelBuilder()
        modelData = builder.build_from(modelFileName)
        self.__reconstructor = ModelReconstructor(modelData)

        # create lookup table
        self.__lookupTable = []
        self.__build_lookup_table()

    #--------------------------------------------------------------------------#
    # public methods
    #--------------------------------------------------------------------------#

    # updates the mesh for the provided weights
    #
    # parameters:
    #
    # - speakerWeights: weights affecting the speaker anatomy
    # - phonemeWeights: weights affecting the phoneme related shape
    #
    def update_for_weights(self, speakerWeights, phonemeWeights):

        # compute new vertex positions
        weights = ModelWeights()
        weights.speakerWeights = numpy.array(speakerWeights)
        weights.phonemeWeights = numpy.array(phonemeWeights)
        newPositions = self.__reconstructor.reconstruct_from_weights(weights)

        # update game mesh using the new positions
        self.__update_game_mesh(newPositions)

    #--------------------------------------------------------------------------#
    # private methods
    #--------------------------------------------------------------------------#

    # helper method for constructing the lookup table
    def __build_lookup_table(self):

        # get model vertices
        originalVertices = self.__reconstructor.get_shape_space_origin()

        # build kd-tree
        kd = mathutils.kdtree.KDTree(len(originalVertices))

        for i, v in enumerate(originalVertices):
            kd.insert(v, i)

        kd.balance()

        gameMeshVertices = self.__get_game_mesh_vertices()

        # build mapping
        for vertex in gameMeshVertices:
            co_find = vertex.XYZ
            co, index, dist = kd.find(co_find)
            self.__lookupTable.append(index)

    #--------------------------------------------------------------------------#

    # helper method for getting the game mesh vertices
    def __get_game_mesh_vertices(self):

        # get vertex data in the first material of the game mesh
        materialVertices = [self.__gameMesh.getVertex(0, i)\
                            for i in range(self.__gameMesh.getVertexArrayLength(0))]
        return materialVertices

    #--------------------------------------------------------------------------#

    # helper method for updating the game mesh vertex positions
    def __update_game_mesh(self, newPositions):

        # get the material index (operate over all materials)
        for m_index in range(len(self.__gameMesh.materials)):

            for v_index in range(self.__gameMesh.getVertexArrayLength(m_index)):

                vertex = self.__gameMesh.getVertex(m_index, v_index)
                # use the vertex mapping to get the right position
                vertex.XYZ = newPositions[self.__lookupTable[v_index]]

    #--------------------------------------------------------------------------#
    # private members
    #--------------------------------------------------------------------------#
    #
    # self.__lookupTable
    # self.__gameMesh
    # self.__reconstructor
    #
    #--------------------------------------------------------------------------#
