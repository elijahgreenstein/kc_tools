"""Gateway object to identify movement across a line segment, with direction.

The Gateway object is initialized with two points. An equation for the line between the two points is found in standard form: ``Ax + By = C``.[^std_form] By default, ``A`` is set to the slope of the line (usually denoted ``m``) and ``B`` is set to ``-1``. The equation is stored as ``Gateway.vector`` (``[A, B]``) and ``Gateway.offset`` (``C``).

[^std_form]: See Edwin "Jed" Herman and Gilbert Strang, "1.2 Basic Classes of Functions," in *Calculus*, Vol. 1, OpenStax: 2018. <https://openstax.org/books/calculus-volume-1/pages/1-2-basic-classes-of-functions>

Due to this calculation of ``A`` and ``B = -1``, the Gateway vector will, by default, point "south." A Gateway with a positive slope will have a vector that points to the southeast, while a Gateway with a negative slope will have a vector that points to the southwest. A horizontal Gateway will have a vector that points straight south.


Example usage:

import kc_tools as kc
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

# Set up the gateway
pt1 = (2, 4)
pt2 = (-2, 3.25)
G = kc.Gateway(pt1, pt2)

# Classify a grid of points
x = np.linspace(-10, 10, 50)
y = np.linspace(-10, 10, 50)
xmesh, ymesh = np.meshgrid(x, y)
ys = G.get_ys(x)
clf = G.classify_array(xmesh, ymesh) > 0

# Plot the classified grid, with an arrow indicating the "positive" side
fig, ax = plt.subplots()
# "Positive" points are blue, "negative" points are orange
ax.scatter(xmesh, ymesh, c=clf, cmap=ListedColormap(["orange", "blue"]), s=0.5)
# Plot the two points and the line through the points
ax.scatter(pt1[0], pt1[1], c="black")
ax.scatter(pt2[0], pt2[1], c="black")
ax.plot(x, ys, color="black", linewidth=1)
# Plot the direction of the vector
ax.quiver(G.midpt[0], G.midpt[1], G.vec[0], G.vec[1], scale=10)
plt.show()

"""

import numpy as np
import shapely


def _calc_m(x1, y1, x2, y2):
    """Calculate the slope, ``m``, of the line between the two points."""
    return (y2 - y1) / (x2 - x1)


def _calc_b(m, x1, y1):
    """Calculate the intercept, ``b``, of the line between the two points."""
    return y1 - m * x1


def _std_form_params(x1, y1, x2, y2):
    """Get the standard form of the line between the two points:

    ``Ax + By = C``
    """
    A = _calc_m(x1, y1, x2, y2)
    B = -1
    C = _calc_b(A, x1, y1)
    return (np.array([A, B]), C)


def _get_midpt(pt1, pt2):
    x_mid = pt1[0] + (pt2[0] - pt1[0]) / 2
    y_mid = pt1[1] + (pt2[1] - pt1[1]) / 2
    return np.array([x_mid, y_mid])


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
        self.midpt = _get_midpt(pt1, pt2)
        self.line = shapely.LineString([pt1, pt2])
        self.vec, self.offset = _std_form_params(pt1[0], pt1[1], pt2[0], pt2[1])

    def classify_pt(self, pt):
        pt = np.array(pt)
        return self.vec @ pt + self.offset

    def classify_array(self, xs, ys):
        return self.vec[0] * xs - ys + self.offset

    def get_ys(self, xs):
        return self.vec[0] * xs + self.offset

