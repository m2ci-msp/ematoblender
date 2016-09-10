class ExternalFittingServerSettings:

    host = "localhost"
    port = 1234

    neededAmountForFixedSpeaker = 100

    # example coil -> vertex index correspondences
    modelVertexIndices = [1991, 2230, 2236, 2549, 2687]
    coilPositionNames  = ['Back', 'Center', 'Right', 'Tip', 'Left']
    coilIndices        = [14, 8, 15, 10, 9]

    weights = {
        "speakerSmoothnessTerm" : 300,
        "phonemeSmoothnessTerm" : 200
    }

    priorSize = 2
