"""Gateway object for identifying passage of ships with direction.
"""

import numpy as np
import shapely

def _calc_m(x1, y1, x2, y2):
    """Calculate the slope, ``m``, of the line between the two points.
    """
    return (y2 - y1) / (x2 - x1)

def _calc_b(m, x1, y1):
    """Calculate the intercept, ``b``, of the line between the two points.
    """
    return y1 - m * x1

def _std_form_params(x1, y1, x2, y2):
    """Get the standard form of the line between the two points:

    ``Ax + By = C``
    """
    A = _calc_m(x1, y1, x2, y2)
    B = -1
    C = _calc_b(A, x1, y1)
    return (np.array([A, B]), C)

class Gateway:
    """Gateway object defined as a line between two points.

    :param pt1: The first point.
    :type pt1: list, tuple, or np.array
    :param pt2: The second point.
    :type pt2: list, tuple, or np.array
    """

    def __init__(self, pt1, pt2):
        self.pt1 = np.array(pt1)
        self.pt2 = np.array(pt2)
        self.line = shapely.LineString([pt1, pt2])
        self.vec, self.offset = _std_form_params(pt1[0], pt1[1], pt2[0], pt2[1])

    def classify(self, pt):
        pt = np.array(pt)
        return self.vec @ pt + self.offset

    def get_ys(self, xs):
        return self.vec[0] * xs + self.offset

