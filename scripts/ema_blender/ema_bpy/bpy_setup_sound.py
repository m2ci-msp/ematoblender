__author__ = 'Kristy'

import bpy
import os
import scripts.ema_shared.properties as pps
import scripts.ema_blender.blender_shared_objects as bsh

'''These functions should be used to find the sound to be played (to sync with the static data file).
The game engine uses from scripts.ema_shared.blender_shared_objects import soundpath,
so this script should make sure it gets there.
'''

# use either properties, or better yet the parameters from the server to find the name of the file being streamed
#pps.sound_source
# get the rel/abs path look in that same directory for similarly-named files with an audio ending


# def find_sound_path(manualsource=None):
#     """ Get the location of the streaming data file from properties' description of the streaming file.
#      Use the filename/directory to find an associated audio file."""
#     if manualsource is not None:
#         return manualsource
#     elif pps.sound_source is not None:
#         print('Sound source found in properties file!')
#         return pps.sound_source
#     elif pps.streaming_source is None:
#         return None
#     else:
#         streampath = pps.streaming_source
#         audtypes=['.wav', '.ogg', 'mp3']
#
#         # returns absolute path to audio file
#         dirname, tail = os.path.split(streampath)
#         print('dirname and tail', dirname, tail)
#         streamfilename, streamext = os.path.splitext(tail)
#         print('streamfilename, ext', streamfilename, streamext)
#
#         # search in same directory, then sister directory
#         # todo: take __file instead
#         current_search_dir = os.path.normpath(bpy.path.abspath('//')+'.'+os.path.sep+dirname+os.path.sep)
#         sister_search_dir = os.path.normpath(bpy.path.abspath('//')+'.'+os.path.sep+dirname+os.path.sep+'..'+os.path.sep)
#
#         for search_dir in [current_search_dir, sister_search_dir]: # search in current folder first
#             print('looking from here:', search_dir)
#             for root, dirs, files in os.walk(search_dir):
#                 for file in files:
#                     print('scanning file', file)
#                     fn, ext = os.path.splitext(file)
#                     if fn == streamfilename and ext in audtypes:
#                         print('candidate found!', os.path.join(root, file))
#                         bsh.soundpath = os.path.join(root, file)
#                         return os.path.join(root, file)
#
#         print('Audio source not found')
#         return None


def load_sound_to_blend(abspath):
    """Load the sound into the blend file. Not needed for game engine behaviour."""
    bpy.ops.sound.open(filepath=abspath, relative_path=True)  # TODO: Test


def set_shared_soundpath(newpath):
    bsh.soundpath = newpath
    print('Set the game engine\'s sound path to', bsh.soundpath)


if __name__=="__main__":
    pass
