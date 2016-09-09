import bge
import bpy
import socket
import json
import numpy
import mathutils
import GameLogic
import os

import multilinearmodel

# get scene
scene = GameLogic.getCurrentScene()

# get game mesh
gameMesh = bge.logic.getCurrentController().owner.meshes[0]

# name coil objects
#coils = ["coil01", "coil02", "coil03", "coil04", "coil05"]

# create model path
userPref = bpy.utils.script_path_pref()
basePath = os.path.join(os.path.dirname(os.path.dirname(userPref)), "model")
modelFile = os.path.join(basePath, "tongue_model.json")

# bind game mesh to tongue model
modelBinding = multilinearmodel.GameMeshBinding(modelFile, gameMesh)

first = True

BLENDERHOST = 'localhost'
BLENDERPORT = 1241

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
        first= False
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
        speakerWeights = decodedJson["speakerWeights"]
        phonemeWeights = decodedJson["phonemeWeights"]
        timeStamp = decodedJson["timeStamp"]
      #  coilPositions = convertToVectors(decodedJson["coilPositions"])
        modelBinding.update_for_weights(speakerWeights, phonemeWeights)
#        updateCoils(coilPositions)

def convertToVectors(positions):
    result = []

    for i in range(0, len(positions) // 3):

        x = positions[i*3 + 0]
        y = positions[i*3 + 1]
        z = positions[i*3 + 2]
        position = mathutils.Vector()
        position[0] = x
        position[1] = y
        position[2] = z
        result.append(position)

    return result

def updateCoils(coilPositions):

    for index in range(len(coils)):
        updateCoil(coils[index], coilPositions[index])

def updateCoil(name, position):

    coil = scene.objects[name]
    (distance, globalVector, localVector) = coil.getVectTo(position)
    motion = distance * globalVector
    coil.applyMovement(motion)

def shutdown():
    sock.close()
    bge.logic.endGame()
