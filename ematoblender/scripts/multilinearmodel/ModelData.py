__author__ = "Alexander Hewer"
__email__ = "hewer@coli.uni-saarland.de"

# Class representing the raw data of the multilinear model
class ModelData:

    def __init__(self):

        self.model = None
        self.mean  = None
        self.identityCenter = None
        self.expressionCenter = None
        self.dimIdentity = 0
        self.dimExpression = 0
        self.dimTarget = 0
