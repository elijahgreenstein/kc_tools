"""Tools to identify edges between nodes.
"""

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import shapely


def _shift_to_360(linestring):
    """Shift a line from -180 to 180 longitude to 0 to 360 longitude."""
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


def get_node_seq(
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
    """Generate a sequence of nodes from a sequence of line segments.

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

    # Get indices of "_break", "line", "t1", "t2" columns
    brk_idx = data.columns.get_loc("_break")
    l_i = data.columns.get_loc(line)
    t1_i = data.columns.get_loc(t1)
    t2_i = data.columns.get_loc(t2)

    # Set up result: A sequence of nodes representing "stops."
    #
    # - "id": The ship id
    # - "node": The node where the ship stopped.
    # - "t1": Line segment `t1`
    # - "t2": Line segment `t2`
    # - "line": The line segment.
    # - "num_intersect": Number of intersections between line and nodes.

    node_columns = ["id", "node", "t1", "t2", "line", "num_intersect"]
    unk_columns = ["id", "t1", "t2", "line"]
    node_seq = []   # Placeholder for node sequence
    unk = []    # Placeholder for possible stops, but lacking intersections
    add_node = True # Add node(s), unless unknown

    for row in subset.itertuples(index=False):
        print(row[brk_idx])
        if row[brk_idx]:
            # Break is automatically not a multi-intersection (1 intersection)
            node = [[sid, "_BREAK", row[t1_i], row[t2_i], row[l_i], 1]]
        else:
            # Get the number of intersections with the node geometries
            intersections = nodes[node_geom].intersects(row[l_i])
            n_int = len(nodes[intersections])
            # If no intersections, then store in `unk` list
            if n_int == 0:
                unk.append([sid, row[t1_i], row[t2_i], row[l_i]])
                add_node = False # Do not add nodes to node seq
            # If one intersection, get node
            elif n_int == 1:
                label = nodes[intersections][node_label].values[0]
                node = [[sid, label, row[t1_i], row[t2_i], row[l_i], n_int]]
            # If two intersections, then extract two nodes and add to node_seq
            elif n_int == 2:
                # TODO: Extract both nodes
                label = "MULTIPLE_2"
                node = [[sid, label, row[t1_i], row[t2_i], n_int]]
            # If three intersections, then extract three nodes
            elif n_int == 3:
                # TODO: Extract all three nodes
                label = "MULTIPLE_3"
                node = [[sid, label, row[t1_i], row[t2_i], n_int]]
            # Case of more than three intersections, handle manually
            else:
                label = "_MANUAL"
                node = [[sid, label, row[t1_i], row[t2_i], n_int]]
        if add_node:
            node_seq += node
        else:
            add_node = True
    node_seq = pd.DataFrame(node_seq, columns=node_columns)
    unk = pd.DataFrame(unk, columns=unk_columns)
    return (node_seq, unk)


def get_edges(
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
            # If no intersections, then store as "_UNKNOWN"
            if n_int == 0:
                node = "_UNKNOWN"
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
    return pd.DataFrame(res[1:], columns=res[0])


def make_digraph(
    edges,
    from_node="node1",
    to_node="node2",
    weighted=True,
    remove_unknown=True,
    unk="_UNKNOWN",
    breaks="_BREAK",
    self_loops=False,
):
    """Generate a digraph from a dataframe of edges.

    :param edges: Dataframe of edges.
    :type edges: pd.DataFrame
    :param from_node: Name of the column with origin node.
    :type from_node: str, "node1"
    :param to_node: Name of the column with the target node.
    :type to_node: str, default: "node2"
    :param weighted: Optionally add weight of ``1`` for each edge.
    :type weighted: bool, default: True
    :param remove_unknown: Remove edges with unknown nodes.
    :type remove_unknown: bool, default: True
    :param unk: Node string indicating a "stop" without an intersection.
    :type unk: str, default: "_UNKNOWN"
    :param breaks: String indicating a "break" in the graph.
    :type breaks: str, default: "_BREAK"
    :param self_loops: If true, allow self-loop edges.
    :type self_loops: bool, default: False
    """
    # Initialize directed graph
    DG = nx.DiGraph()

    # Optionally remove "stops" without a node intersection
    if remove_unknown:
        data = edges[(edges[from_node] != unk) & (edges[to_node] != unk)].copy()
    else:
        data = edges.copy()

    # Get the sequence of target nodes
    seq = data[to_node].values

    for idx_to in range(1, len(seq)):  # Iterate over targets from index 1
        idx_from = idx_to - 1
        n1 = seq[idx_from]
        n2 = seq[idx_to]
        if (n1 == breaks) or (n2 == breaks):
            pass  # Skip the edge if it is on a "break"
        elif (n1 != n2) or (n1 == n2 and self_loops):
            # Increment weight if generating a weighted graph
            if DG.has_edge(n1, n2) and weighted:
                DG[n1][n2]["weight"] += 1
            else:
                DG.add_edge(n1, n2, weight=1)
        else:
            pass
    return DG
