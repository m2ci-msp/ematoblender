__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

# Class representing the raw data of the multilinear model
class ModelData:

    def __init__(self):

        self.coreTensor = None
        self.shapeSpaceOrigin  = None
        self.speakerMeanWeights = None
        self.phonemeMeanWeights = None
        self.dimSpeaker = 0
        self.dimPhoneme = 0
        self.dimVertex = 0
