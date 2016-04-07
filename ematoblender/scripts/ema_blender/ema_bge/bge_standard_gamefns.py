__author__ = 'Kristy'

import bge
from collections import defaultdict


def get_scene_info():
    """Typical functions run every tick to access scene objects.
    Returns scene object, list of objects in scene, controller object,
    owner of the controller, actuators of this object."""
    scn = bge.logic.getCurrentScene()
    objs = scn.objects
    cont = bge.logic.getCurrentController()
    own = cont.owner
    acts = own.actuators
    return scn, objs, cont, own, acts



def catch_keypresses(keyboard=bge.logic.keyboard):
    """Return a default dictionary indicating whether a key is KX_INPUT_JUST_ACTIVATED or KX_INPUT_ACTIVE.
    Queries for keys not defined return false."""

    # key definitions
    IJA = bge.logic.KX_INPUT_JUST_ACTIVATED
    IA = bge.logic.KX_INPUT_ACTIVE

    # define all the necessary flags for events (keys or buttons)
    esckey = keyboard.events[bge.events.QKEY] == IJA or keyboard.events[bge.events.QKEY] == IA

    wkey = keyboard.events[bge.events.WKEY] == IJA or keyboard.events[bge.events.WKEY] == IA
    ekey = keyboard.events[bge.events.EKEY] == IJA or keyboard.events[bge.events.EKEY] == IA
    rkey = keyboard.events[bge.events.RKEY] == IJA or keyboard.events[bge.events.RKEY] == IA
    tkey = keyboard.events[bge.events.TKEY] == IJA or keyboard.events[bge.events.TKEY] == IA
    ykey = keyboard.events[bge.events.YKEY] == IJA or keyboard.events[bge.events.YKEY] == IA

    okey = keyboard.events[bge.events.OKEY] == IJA or keyboard.events[bge.events.OKEY] == IA

    skey = keyboard.events[bge.events.SKEY] == IJA or keyboard.events[bge.events.SKEY] == IA
    dkey = keyboard.events[bge.events.DKEY] == IJA   # for d, only take just activated, one activation per press
    fkey = keyboard.events[bge.events.FKEY] == IJA or keyboard.events[bge.events.FKEY] == IA
    gkey = keyboard.events[bge.events.GKEY] == IJA or keyboard.events[bge.events.GKEY] == IA
    hkey = keyboard.events[bge.events.HKEY] == IJA or keyboard.events[bge.events.HKEY] == IA

    upkey = keyboard.events[bge.events.UPARROWKEY] == IJA or keyboard.events[bge.events.UPARROWKEY] == IA
    downkey = keyboard.events[bge.events.DOWNARROWKEY] == IJA or keyboard.events[bge.events.DOWNARROWKEY] == IA
    leftkey = keyboard.events[bge.events.LEFTARROWKEY] == IJA or keyboard.events[bge.events.LEFTARROWKEY] == IA
    rightkey = keyboard.events[bge.events.RIGHTARROWKEY] == IJA or keyboard.events[bge.events.RIGHTARROWKEY] == IA


    commakey = keyboard.events[bge.events.COMMAKEY] == IJA or keyboard.events[bge.events.COMMAKEY] == IA
    periodkey = keyboard.events[bge.events.PERIODKEY] == IJA or keyboard.events[bge.events.PERIODKEY] == IA

    spacekey = keyboard.events[bge.events.SPACEKEY] == IJA or keyboard.events[bge.events.SPACEKEY] == IA

    keydict = defaultdict(lambda: False, locals())

    return keydict