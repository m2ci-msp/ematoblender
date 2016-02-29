__author__ = 'Kristy'

###############################################################################
# DEFINITION OF A POINT OBJECT - THE SENSORS (CURRENT LOCATION/STATUS)
# AND META-INFORMATION ABOUT THEM
###############################################################################

class PointsDefinitions():
    """Maintain meta information about the points being sampled (eg which sensor is where)
    Should persist over each change to the point itself."""

    ALL_SENSORS = []

    def __init__(self, namesinorder, activelist, staticlist):
        """Initialise the points that data is collected from with getcurrentframe/streamframes"""
        PointsDefinitions.ALL_SENSORS = [Point(name, order, active=False if name in staticlist else True)
                                  for order, name in enumerate(namesinorder)]

class Point(PointsDefinitions):
    '''All the information about a point in space.
    These are operated on directly by the parsers.
    Attributes should be restricted to: (grow this list)
        # self.absolute_location = (x, y, z)
        # self.absolute_rotation = (q0, qx, qy, qz) # quaternion
        # self.error
        # self.reliability
        # * self.order
        # * self.active
        # * self.name

        * set by PointsDefinition initialisation
    '''
    def __init__(self, name, toolorder, active=True):
        self.name = name
        self.order = toolorder
        self.active = active