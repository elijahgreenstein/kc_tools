"""Tools to identify ports of call on a given voyage.
"""

import geopandas as gpd
import pandas as pd

def get_sequence(traj_df, ports, t1="t1", t2="t2", line="line"):
    """Generate a dataframe column containing ports of call.

    :param traj_df: Dataframe of line segments.
    :type traj_df: pd.DataFrame
    :param ports: Dictionary of port names and geometries.
    :type ports: dict
    :param t1: Name of column in ``traj_df`` containing start times for each line segment.
    :type t1: str, default: "t1"
    :param t2: Name of column in ``traj_df`` containing end times for each line segment.
    :type t2: str, default: "t2"
    :param line: Name of column in ``traj_df`` containing line geometries.
    :type line: str, default: "line"
    """

    # TODO: Check intersection with each port.
    # - Filter for at least one intersection:
    # df[df[port_names].sum(axis=1) > 0]

    # Will have several columns of port_names
    # Get indicator variables for intersections, change to integer 0, 1
    # df[port_names] = df[port_names].astype(int)
    # Create a column indicating overlaps (sum plus offset)
    pass
