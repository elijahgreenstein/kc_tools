"""Gateway object to identify movement across a line segment, with direction.

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
xs, ys = G.get_xys(x)
clf = G.classify_array(xmesh, ymesh) > 0

# Plot the classified grid, with an arrow indicating the "positive" side
fig, ax = plt.subplots()
# "Positive" points are blue, "negative" points are orange
ax.scatter(xmesh, ymesh, c=clf, cmap=ListedColormap(["orange", "blue"]), s=0.5)
# Plot the two points and the line through the points
ax.scatter(pt1[0], pt1[1], c="black")
ax.scatter(pt2[0], pt2[1], c="black")
ax.plot(xs, ys, color="black", linewidth=1)
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
    """Get the standard form of the line between the two points.

    Returns ``A``, ``B``, and ``C`` of :math:`Ax + By + C = 0`.
    """
    # Check for vertical line
    if x1 == x2:
        A = 1
        B = 0
        C = -x1
    else:
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

    The Gateway object is initialized with two points. An equation for the line between the two points is found in general form: :math:`Ax + By + C = 0`. [#gen_form]_ By default, :math:`A` is set to the slope of the line (usually denoted :math:`m`) and :math:`B` is set to :math:`-1`. :math:`A` and :math:`B` are stored as ``Gateway.vector`` and :math:`C` is stored as ``Gateway.offset``. For vertical gateways, however, :math:`A` is set to :math:`1`, :math:`B` is set to :math:`0`, :math:`C` is set to the x value shared by both points.

    Points are "classified" in terms of location on one side of the line or another by taking the dot product of the point and ``Gateway.vector`` and adding ``Gateway.offset``.

    .. note:: Due to the default calculation of :math:`A=m` and :math:`B=-1`, the Gateway vector will, by default, point "south" unless the Gateway is vertical. A Gateway with a positive slope will have a vector that points to the southeast, while a Gateway with a negative slope will have a vector that points to the southwest. A horizontal Gateway will have a vector that points due south. Hence, points to the south of the line will be classified as "positive" while points to the north will be classified as "negative." In the case of vertical Gateways, however, the vector will point due east, and points to the east of the line will be classified as "positive."

    .. [#gen_form] See Edwin "Jed" Herman and Gilbert Strang, "1.2 Basic Classes of Functions," in *Calculus*, Vol. 1, OpenStax: 2018.  <https://openstax.org/books/calculus-volume-1/pages/1-2-basic-classes-of-functions>

    """

    def __init__(self, pt1, pt2):
        self.pt1 = np.array(pt1)
        self.pt2 = np.array(pt2)
        self.is_vert = self.pt1[0] == self.pt2[0]
        self.midpt = _get_midpt(pt1, pt2)
        self.line = shapely.LineString([pt1, pt2])
        self.vec, self.offset = _std_form_params(pt1[0], pt1[1], pt2[0], pt2[1])

    def classify_pt(self, pt):
        pt = np.array(pt)
        return self.vec @ pt + self.offset

    def classify_array(self, xs, ys):
        return self.vec[0] * xs + self.vec[1] * ys + self.offset

    def get_xys(self, xs):
        """Get x, y coordinates to plot the line.

        :param xs: An array of x coordinates.
        :type xs: np.array
        :return xs: An array of x coordinates.
        :rtype xs: np.array
        :return ys: An array of y coordinates.
        :rtype ys: np.array

        .. note::

           If the gateway is vertical, the y coordinates are set to the input x coordinates and the x coordinates are changed to an array of the same length, but with all values set to :math:`-C` (the offset, but with the sign reversed).
        """
        if self.is_vert:
            ys = xs
            xs = np.ones(len(xs)) * (-self.offset)
            return (xs, ys)
        else:
            return (xs, self.vec[0] * xs + self.offset)
