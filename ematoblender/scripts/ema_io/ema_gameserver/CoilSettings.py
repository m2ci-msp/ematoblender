__author__  = "Alexander Hewer"
__credits__ = "Kristy James"
__email__   = "hewer@coli.uni-saarland.de"

import json

from ...ema_shared import properties as pps

class CoilSettings:

    coils = {}

    def save():

        jsonData = {}

        for key, value in __class__.coils.items():

            entry = {}
            entry["place"] = __class__.__translate(key)
            entry["active"] = True
            entry["reference"] = "reference" in key
            entry["biteplate"] = "bitePlate" in key
            jsonData[str(value)] = entry

        output = open("ematoblender/scripts/ema_shared/" + pps.json_loc, 'w')
        json.dump(jsonData, output)
        output.close()

    def __translate(id):

        if id == "tongueTip":
            return "TT"
        elif id == "tongueCenter":
            return "TM"
        elif id == "tongueBack":
            return "TB"
        elif id == "tongueLeft":
            return "TL"
        elif id == "tongueRight":
            return "TR"
        elif id =="upperLips":
            return "UL"
        elif id == "sideLips":
            return "SL"
        elif id == "upperIncisors":
            return "UI"
        elif id == "lowerIncisors":
            return "LI"
        elif id == "referenceFront":
            return "FT"
        elif id == "referenceLeft":
            return "MR"
        elif id == "referenceRight":
            return "ML"
        elif id == "referenceOrigin":
            return "REF"
        elif id == "bitePlateFront":
            return "BPF"
        elif id == "bitePlateLeft":
            return "BPL"
        elif id == "bitePlateRight":
            return "BPR"
        else:
            return id
