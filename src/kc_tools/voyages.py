"""Tools to identify ports of call on a given voyage.
"""

import geopandas as gpd
import pandas as pd

def get_sequence(data, ports, dist_break, t1="t1", t2="t2", line="line"):
    """Generate a dataframe column containing ports of call.

    :param data: Dataframe of line segments.
    :type data: pd.DataFrame
    :param ports: Dictionary of port names and geometries.
    :type ports: dict
    :param t1: Name of column in ``traj_df`` containing start times for each line segment.
    :type t1: str, default: "t1"
    :param t2: Name of column in ``traj_df`` containing end times for each line segment.
    :type t2: str, default: "t2"
    :param line: Name of column in ``traj_df`` containing line geometries.
    :type line: str, default: "line"
    """

    port_names = list(ports.keys())

    # Create "break" column with arbitrarily high value (1000)
    data["BREAK"] = (data["line"].length > dist_break) * 1000

    # For each port, identify intersections
    for port in port_keys:
        data[port] = data["line"].intersects(ports[port])

    # Change to integer indicators for port intersections
    data[port_names] = data[port_names].astype(int)

    # Filter for columns with either a "BREAK" or a port intersection
    intersects = data[data[port_names + ["BREAK"]].sum(axis=1) > 0].copy()

    # Create a column indicating multiple intersections. Lines that intersect
    # one port will have an overlap value of `0.5`. Lines that intersect two
    # ports will have an overlap value of `1.5`.
    intersects["MULTIPLE"] = intersects[port_names].sum(axis=1) - 0.5

    # Get the column with the maximum value of port intersection indicators,
    # "OVERLAP", and "BREAK".
    intersects["intersect"] = intersects[
            port_names + ["BREAK", "MULTIPLE"]
            ].idxmax(axis=1)

    # Placeholder for final sequence
    res = []
    # TODO: Iterate over intersects["intersect"] to handle overlapping ports
    # TODO: Return the result
    pass
