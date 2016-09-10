__author__  = "Alexander Hewer"
__email__   = "hewer@coli.uni-saarland.de"

import json

class OverrideSettings:

    overrides = {
        "audio" : { "active" : False}
    }

    def save():

        jsonData = {}

        output = open("ematoblender/scripts/ema_shared/overrides.json", "w")
        json.dump(__class__.overrides, output)
        output.close()
