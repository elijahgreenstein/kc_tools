"""Tools to identify ports of call on a given voyage.
"""

import geopandas as gpd
import pandas as pd

def get_sequence(traj_df, port_names, port_geom, t1="t1", t2="t2", line="line"):
    """Generate a dataframe column containing ports of call.

    :param traj_df: Dataframe of line segments.
    :type traj_df: pd.DataFrame
    :param port_names: List of port names.
    :type port_df: list, pd.Series
    :param port_geom: List of port geometries.
    :type port_df: list, pd.Series
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
    pass
