__author__ = 'Kristy'

"""Create a video texture on the Screen material. This can be set up in BPY so that black appears transparent.
On each call the video is updated. One pitfall is that no timestamp control is available yet,
so when it is restarted the coils will be out of sync. Also if streaming takes a moment to initialise,
the video plays (almost) immediately, also leading to timing mismatches."""

from scripts.ema_shared.properties import video_override

import bge
import os


def bge_update_videoplane(timestamp_secs, videolocation, planename='UltrasoundPlane'):
    """Update the video appropriately based on timestamp"""
    if not hasattr(bge.logic, 'usvideo'):  # Runs on second logic tick as waits on other imports

        scene = bge.logic.getCurrentScene()
        usp = scene.objects[planename]

        # get the reference pointer to the internal texture
        matID = bge.texture.materialID(usp, 'MA' + 'Screen')

        bge.logic.usvideo = bge.texture.Texture(usp, matID)

        if video_override is not None and os.path.isfile(video_override):
            videolocation = video_override
        # define a source for the new texture
        bge.logic.usvideo.source = bge.texture.VideoFFmpeg(videolocation)
        bge.logic.usvideo.source.scale=True # TODO: remove?
        print('Video source updated to', bge.logic.usvideo.source)
        bge.logic.usvideo.source.play()

    else:
       bge.logic.usvideo.refresh(True)
       print('Modally updating video source {} with status {}'.format(bge.logic.usvideo.source,bge.logic.usvideo.source.status))


def bge_reset_videoplane(newlocation, planename='UltrasoundPlane'):
    if hasattr(bge.logic, 'usvideo'):
        bge.logic.usvideo.source.stop()
        del bge.logic.usvideo
    bge_update_videoplane(0, newlocation, planename=planename)

# must be abs path here
if __name__ == "__main__":
    bge_update_videoplane(0, os.path.abspath(video_override))




# def bge_update_videoplane(timestamp_secs, videolocation, planename='UtrasoundPlane'):
#     """Update the video appropriately based on timestamp"""
#     if not hasattr(bge.logic, 'usvideo'):  # Runs on second logic tick as waits on other imports
#         scn, objs, *_ = get_scene_info()()
#         usp = objs.get(planename, 0) # get the plane it it should be displayed on
#
#         # get the reference pointer to the internal texture # TODO: Check that this is initialised correctly
#         #image_prefix = 'IM'; placeholdername = 'face_blank.png'  #    matID = bge.texture.materialID(fp, 'MAFaceMaterial') print('@@@@@@@@@@ Material ID', matID)
#         #matID = bge.texture.materialID(image_prefix+placeholdername)
#         matID = bge.texture.materialID('MA'+'Screen')
#
#         bge.logic.usvideo = bge.texture.Texture(usp, matID)  # 0 is matID #TODO: Update this to actually check for the name??
#
#         # define a source for the new texture
#         bge.logic.usvideo.source = bge.texture.VideoFFmpeg(ultrasound_video_loc)
#         bge.logic.usvideo.source.scale=True # TODO: remove?
#         print('Video source updated to', bge.logic.usvideo.source)
#         bge.logic.usvideo.source.play()
#
#     else:
#        bge.logic.usvideo.refresh(True)
#         print('Modally updating video source {} with status {}'.format(bge.logic.usvideo.source,bge.logic.usvideo.source.status))
#
# bge_update_videoplane()