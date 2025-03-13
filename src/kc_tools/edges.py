"""Tools to identify edges between nodes.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import shapely

def _shift_to_360(linestring):
    """Shift a line from -180 to 180 longitude to 0 to 360 longitude.
    """
    x1, y1 = linestring.coords[0]
    x2, y2 = linestring.coords[1]
    if x1 < 0:
        x1 = x1 + 360
    else:
        pass
    if x2 < 0:
        x2 = x2 + 360
    else:
        pass
    return shapely.LineString(((x1, y1), (x2, y2)))

def get_edge_seq(
        data,
        nodes,
        dist_break,
        stop_duration,
        uid="id",
        t1="t1",
        t2="t2",
        line="line",
        node_label="label",
        node_geom="geometry",
        ):
    """Generate dataframe of directed edges between designated node geometries.

    :param data: Dataframe of line segments.
    :type data: pd.DataFrame
    :param nodes: Dataframe of node geometries.
    :type nodes: pd.DataFrame
    :param dist_break: Minimum gap between points (length of line segment) to mark as a "break" in the graph.
    :type dist_break: int
    :param stop_duration: Minimum duration between point observations ("duration" of the line segment) to mark as a possible node intersection.
    :type stop_duration: int
    :param uid: Name of column in ``data`` containing the ship id.
    :type uid: str, default: "id"
    :param t1: Name of column in ``data`` containing start times for each line segment.
    :type t1: str, default: "t1"
    :param t2: Name of column in ``data`` containing end times for each line segment.
    :type t2: str, default: "t2"
    :param line: Name of column in ``data`` containing line geometries.
    :type line: str, default: "line"
    :param node_label: Name of column in ``nodes`` containing labels of geometries.
    :type node_label: str, default: "label"
    :param node_geom: Name of column in ``nodes`` containing geometries.
    :type node_geom: str, default: "geometry"
    """

    # Confirm single id number and get that id
    if len(data[uid].unique()) > 1:
        print("ERROR: Data should only have a single ship id.")
        return None
    else:
        sid = data[uid].unique()[0]


    # Confirm that t1, t2 are of type datetime64
    if t1 not in data.select_dtypes(np.datetime64).columns:
        data[t1] = pd.to_datetime(data[t1])
    if t2 not in data.select_dtypes(np.datetime64).columns:
        data[t2] = pd.to_datetime(data[t2])

    # Add a timedelta column (length of time between points 1 and 2)
    data["_timedelta"] = data[t2] - data[t1]
    # Add an hours column
    data["_hours"] = data["_timedelta"] / np.timedelta64(1, "h")

    # Add a column of linestrings shifted to 0--360 longitude scale
    data["_l360"] = data[line].apply(lambda x: _shift_to_360(x))

    # Identify possible stops
    data["_poss_stop"] = data["_hours"] >= stop_duration

    # Identify -180--180 break points
    data["_br180"] = data[line].length >= dist_break
    # Identify 0--360 break points
    data["_br360"] = data["_l360"].length >= dist_break
    # Identify break points
    data["_break"] = (data["_br180"]) & (data["_br360"])

    # Filter for possible stops, break points
    subset = data[(data["_poss_stop"]) | (data["_break"])].copy()

    # Get index of "_break", "line", "t1", "t2" columns
    brk_idx = data.columns.get_loc("_break")
    ln_idx = data.columns.get_loc(line)
    t1_idx = data.columns.get_loc(t1)
    t2_idx = data.columns.get_loc(t2)

    # Set up result: A list of edges containing the following information:
    #
    # - "id": The ship id
    # - "p1": The node from which the ship departed
    # - "p2": The node to which the ship arrived next
    # - "t_depart_p1": The time of departure
    # - "t_arrive_p2": The time of arrival
    # - "num_intersect": The number of intersections (possibly multiple nodes)

    res = [["id", "node1", "node2", "t_dep_p1", "t_arr_p2", "num_intersect"]]

    # Set up initial node, with blank departure
    prev = "_START"
    t_dep = None


    for row in subset.itertuples(index=False):
        # Check for "break" points
        if row[brk_idx]:
            node = "_BREAK"
            n_int = 1
            edge = [sid, prev, node, t_dep, row[t1_idx], n_int]
            prev = node
            t_dep = row[t2_idx]
        else:
            # Get the number of intersections with the port geometries
            intersections = nodes[node_geom].intersects(row[ln_idx])
            n_int = len(nodes[intersections])
            # If no intersections, then store as "_NO_INTERSECT"
            if n_int == 0:
                node = "_NO_INTERSECT"
                edge = [sid, prev, node, t_dep, row[t1_idx], n_int]
                prev = node
                t_dep = row[t2_idx]
            # If one intersection, then only one node from that line
            elif n_int == 1:
                node = nodes[intersections][node_label].values[0]
                edge = [sid, prev, node, t_dep, row[t1_idx], n_int]
                prev = node
                t_dep = row[t2_idx]
            # If two intersections, then extract two nodes
            elif n_int == 2:
                # TODO: Extract both nodes
                node = "MULTIPLE_2"
                edge = [sid, prev, node, t_dep, row[t1_idx], n_int]
                prev = node
                t_dep = row[t2_idx]
            # If three intersections, then extract three nodes
            elif n_int == 3:
                # TODO: Extract all three nodes
                node = "MULTIPLE_3"
                edge = [sid, prev, node, t_dep, row[t1_idx], n_int]
                prev = node
                t_dep = row[t2_idx]
            # Case of more than three intersections, handle manually
            else:
                node = "_MULTIPLE"
                edge = [sid, prev, node, t_dep, row[t1_idx], n_int]
                prev = node
                t_dep = row[t2_idx]
        res.append(edge)
    return res

