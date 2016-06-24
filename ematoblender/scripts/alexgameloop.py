import bge
import socket
import json
import numpy
import mathutils
import GameLogic

from multilinearmodel import *

# get scene
scene = GameLogic.getCurrentScene()

# prepare model data structures
builder = ModelBuilder()
modelData = builder.build_from('./palateModel.rmm')
reconstructor = ModelReconstructor(modelData)
originalVertices = reconstructor.get_mean()

# build kd tree
size = len(originalVertices)
kd = mathutils.kdtree.KDTree(size)

for i, v in enumerate(originalVertices):
    kd.insert(v, i)

kd.balance()

# get vertex data in game engine
firstMaterial = bge.logic.getCurrentController().owner.meshes[0]
materialVertices = [firstMaterial.getVertex(0, i) for i in range(firstMaterial.getVertexArrayLength(0))]

# build vertex mapping between original mesh and game engine mesh
vertexMapping = []

for vertex in materialVertices:
    co_find = vertex.XYZ
    co, index, dist = kd.find(co_find)
    vertexMapping.append(index)

first = True

BLENDERHOST = 'localhost'
BLENDERPORT = 2235

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0)
sock.bind((BLENDERHOST, BLENDERPORT))


def listen():
    data = ''
    try:
        data = sock.recv(32768)
    except:
        pass
    return data



def main():
    global first
   # print('I am executing the game loop')
#    print('top value of first is', first)
    if first:
        first = False
        initial()
    else:
        model()

    #print('value of first is', first)

def initial():
    print("I am the initial execution")

def model():
   # print("I am the model loop")
    if bge.logic.keyboard.events[bge.events.QKEY]:
        shutdown()

    byteData = listen()
    if(len(byteData) > 0):
        stringData = byteData.decode('utf-8')
        decodedJson = json.loads(stringData)
        idWeights = decodedJson["idWeights"]
        expWeights = decodedJson["expWeights"]
        weights = ModelWeights()
        weights.idWeights = numpy.array(idWeights)
        weights.expWeights = numpy.array(expWeights)
        result = reconstructor.reconstruct_from_weights(weights)
        updateMesh(result)
       
def updateMesh(newPositions):

    tongue = bge.logic.getCurrentController().owner

    for mesh in tongue.meshes:


        # get the material index (operate over all materials)
        for m_index in range(len(mesh.materials)):

            vertices = [mesh.getVertex(m_index, i) for i in range(mesh.getVertexArrayLength(m_index))]

            for index in range(len(vertices)):
                # use the vertex mapping to get the right position
                vertices[index].XYZ = newPositions[vertexMapping[index]]

def shutdown():
    sock.close()
    bge.logic.endGame()
