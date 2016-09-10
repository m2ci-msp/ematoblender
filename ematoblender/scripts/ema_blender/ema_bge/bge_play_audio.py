__author__ = 'Kristy'

import bge
import aud
import time
import random
import math
import json
import os
import bpy

from .. import blender_shared_objects as bsh
from ...ema_shared import properties as pps

sound_first_exec = True


def main():
    print('doing main, runs during testing only')
    if sound_first_exec:
        sound_setup()
    else:
        sound_update()


def sound_setup(*filepath):
    print('DOING SOUND SETUP')
    global sound_first_exec
    sound_first_exec = False

    import os

    # get the sound actuator
    sound_actuator = bge.logic.getCurrentController().owner.actuators['SoundAct']
    #print(sound_actuator, sound_actuator.__dir__())

    # get override information
    userPref = bpy.utils.script_path_pref()
    overridesFile = os.path.join(userPref, "ema_shared", "overrides.json")
    fileStream = open(overridesFile, "r")
    overrides = json.load(fileStream)
    fileStream.close()

    audioOverride = overrides["audio"]

    # prepare the sound factory
    if audioOverride["active"] == True:
        soundpath = audioOverride["path"]
        print('USING MANUAL SOUND OVERRIDE:', soundpath)
    else:
        soundpath = bsh.soundpath
        print('USING STANDARD SOUND FILE', soundpath)

    if soundpath is not None and os.path.isfile(soundpath):

        factory = aud.Factory(soundpath)
        sound_actuator.sound = factory

    sound_actuator.startSound()
    sound_actuator.pauseSound()


def sound_update(timestamp=None):
    """Give timestamp in seconds (float) and sound time coordinates to it."""
    #print('\n\ndoing sound update update')
    #print('kw in timestamp is', timestamp)

    act = bge.logic.getCurrentController().owner.actuators['SoundAct']
    if timestamp is None:
        return
    else:
        tstime = timestamp  # timestamp is in seconds

    print('difftime is', tstime)
    print('soundtime is', act.time)

    if abs(tstime - act.time) < 0.1:  # acceptable difference
        # print('acceptable difference in sound time')
        act.startSound()

    elif tstime > act.time:  # timestamp ahead, sound needs to catch up!
        act.time = tstime  # skip ahead to timestamp and play
        # print(' new soundtime is', act.time)
        act.startSound()

    elif tstime < act.time:  # sound ahead, need to slow down
        print('i should pause here')
        act.pauseSound()    # pause until timestamp catches up, eg when streaming suspended
        act.time = tstime  # skip ahead to timestamp and play # new


def pause_sound():
    act = bge.logic.getCurrentController().owner.actuators['SoundAct']
    act.pauseSound()


def sound_shutdown():
    print('shutting down')
    act = bge.logic.getCurrentController().owner.actuators['SoundAct']
    act.stopSound()

if __name__ == "__main__":
    # for testing, populate this manually instead of server
    bsh.soundpath = bge.logic.expandPath('//testpiano.m4a')
    main()

