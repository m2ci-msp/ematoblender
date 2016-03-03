__author__ = 'Kristy'

"""
This module controls how the audio stream is coordinated with the datastream,
and how it is recorded and saved.
"""


from threading import Thread, Event
from collections import deque

from scripts.ema_shared.properties import wave_writing_chunk_size

recording = None
stop_recording = Event()


def start_sound_recording(f):
    """Write to the wave file,
    performing the audio recording in a thread.
    Return a deque that contains the latest sample number written to the audio file.
    This number should be included in the TSV file when it is written.
    """
    global recording, stop_recording
    stop_recording.clear()
    last_wave_time = deque(maxlen=1)
    last_wave_time.append(0)  # set a starting value
    recording = Thread(target=record_wav_to_file, args=(f, stop_recording, last_wave_time))
    recording.daemon = True
    recording.start()
    return last_wave_time


def stop_sound_recording():
    global stop_recording
    if not stop_recording.is_set():
        stop_recording.set()


def record_wav_to_file(fname, endflag, tsqueue):
    """Waiting for a flag to terminate, record all audio to the given file location.
    Inspired by http://stackoverflow.com/questions/892199/detect-record-audio-in-python"""

    import wave
    import pyaudio

    print('Initialising wave recording.')

    chunk = wave_writing_chunk_size
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    p = pyaudio.PyAudio()
    sas = p.get_sample_size(FORMAT)
    aud_stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=chunk)

    wf = wave.open(fname, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setframerate(RATE)
    wf.setsampwidth(sas)

    aud_stream.start_stream()
    while not endflag.is_set():
        data = aud_stream.read(chunk)
        print('Saving to wav sample number', wf.tell()/(CHANNELS*16))
        tsqueue.append(wf.tell()/(CHANNELS*16))  # save the most recent sample number
        wf.writeframes(data)

    print('Ceasing wave recording.')
    aud_stream.stop_stream()
    aud_stream.close()
    p.terminate()
    wf.close()
