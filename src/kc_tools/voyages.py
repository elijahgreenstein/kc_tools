"""Tools to identify ports of call on a given voyage.
"""

import geopandas as gpd
import pandas as pd

def get_sequence(traj_df, port_df, t1="t1", t2="t2", line="line", port="port",
                 geometry="geometry"):
    """Generate a dataframe column containing ports of call.

    :param traj_df: Dataframe of line segments.
    :type traj_df: pd.DataFrame
    :param port_df: Dataframe of port names and geometries.
    :type port_df: geopandas.GeoDataFrame
    :param t1: Name of column in ``traj_df`` containing start times for each line segment.
    :type t1: str, default: "t1"
    :param t2: Name of column in ``traj_df`` containing end times for each line segment.
    :type t2: str, default: "t2"
    :param line: Name of column in ``traj_df`` containing line geometries.
    :type line: str, default: "line"
    :param port: Name of column in ``port_df`` containing names of ports.
    :type port: str, default: "port"
    :param geometry: Name of column in ``port_df`` containing port geometries.
    :type geometry: str, default: "geometry"
    """
    pass
