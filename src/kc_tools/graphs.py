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
    :return (node_seq, unk): A tuple containing a node sequence and "unknown" line segments.
    :rtype: (pd.DataFrame, pd.DataFrame)
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
    node_seq = []  # Placeholder for node sequence
    unk = []  # Placeholder for possible stops, but lacking intersections
    add_node = True  # Add node(s), unless unknown

    for row in subset.itertuples(index=False):
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
                add_node = False  # Do not add nodes to node seq
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


def add_edges_GDL(node_seq, GDL, breaks="_BREAK", weighted=True, self_loops=False):
    """Add edges to a "graph of direct linkages" (GDL).

    :param node_seq: Sequence of nodes to add to the graph.
    :type node_seq: pd.Series, list
    :param GDL: Graph of direct linkages.
    :type GDL: nx.DiGraph
    :param breaks: String indicating a break in the node sequence.
    :type breaks: str, default: "_BREAK"
    :param weighted: Create a weighted graph if true.
    :type weighted: bool, default: True
    :param self_loops: Allow self loops.
    :type self_loops: bool, default: False
    :return GDL: Graph of direct linkages updated with edges from node sequence.
    :rtype GDL: nx.DiGraph

    A "graph of direct linkages" (GDL) is a directed graph in which edges represent the movement of ships from one node to the next. Given a voyage from port A to B to C, the graph will consist of directed edges from A to B and from B to C, without an edge from A to C.[#GDL_ref]_

    .. [#GDL_ref] César Ducruet and Theo Notteboom, "The worldwide maritime network of container shipping: spatial structure and regional dynamics," *Global Networks* 12, no. 3 (2012): 402--3.
    """
    # Ensure that graph is nx.DiGraph
    if type(GDL) != nx.DiGraph:
        raise TypeError("GDL must be a networkx DiGraph.")
    else:
        # Copy graph so that changes are not made to original graph
        graph = GDL.copy()
        for from_node, to_node in zip(node_seq[:-1], node_seq[1:]):
            if from_node == breaks or to_node == breaks:
                pass
            else:
                if graph.has_edge(from_node, to_node) and weighted:
                    graph[from_node][to_node]["weight"] += 1
                else:
                    graph.add_edge(from_node, to_node, weight=1)
        return graph


def add_edges_GAL(node_seq, GAL, breaks="_BREAK", weighted=True, self_loops=False):
    """Add edges to a "graph of all linkages" (GAL).

    :param node_seq: Sequence of nodes to add to the graph.
    :type node_seq: pd.Series, list
    :param GAL: Graph of all linkages.
    :type GAL: nx.Graph
    :param breaks: String indicating a break in the node sequence.
    :type breaks: str, default: "_BREAK"
    :param weighted: Create a weighted graph if true.
    :type weighted: bool, default: True
    :param self_loops: Allow self loops.
    :type self_loops: bool, default: False
    :return GAL: Graph of all linkages updated with edges from node sequence.
    :rtype GAL: nx.Graph

    A "graph of all linkages" (GDL) is an undirected graph in which edges represent the co-occurrence of nodes on a voyage by a given ship. Given a voyage from port A to B to C, the graph will consist of undirected edges between A and B, between A and C, and between B and C.[#GDL_ref]_

    .. [#GDL_ref] César Ducruet and Theo Notteboom, "The worldwide maritime network of container shipping: spatial structure and regional dynamics," *Global Networks* 12, no. 3 (2012): 402--3.
    """
    # Ensure that graph is nx.Graph
    if type(GAL) != nx.Graph:
        raise TypeError("GAL must be a networkx Graph.")
    else:
        # Copy graph so that changes are not made to original graph
        graph = GAL.copy()
        # Remove break and get unique nodes
        node_set = node_seq[node_seq != breaks].unique()
        # Create edges between every pair of nodes
        if self_loops:
            idx_add = 0
        else:
            idx_add = 1
        edges = []
        for idx1 in range(len(node_set) - 1):
            for idx2 in range(idx1 + idx_add, len(node_set)):
                edges.append((node_set[idx1], node_set[idx2]))
        # Increment weights if weighted, or simply add edges
        if weighted:
            for edge in edges:
                if graph.has_edge(edge[0], edge[1]):
                    graph[edge[0]][edge[1]]["weight"] += 1
                else:
                    graph.add_edge(edge[0], edge[1], weight=1)
        else:
            graph.add_edges_from(edges)
        return graph
