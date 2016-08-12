__author__  = "Alexander Hewer"
__credits__ = "Kristy James"
__email__   = "hewer@coli.uni-saarland.de"

class GameServerSettings:

    useHeadCorrection = False

    host = "localhost"
    port = 1111

    rtcHost = "localhost"
    rtcPort = 9995

    outputWave = False
    waveOutputDir = None

    outputReceivedData = False
    receivedDataOutputDir = None

    smoothMs = 20
    smoothFrames = 4
