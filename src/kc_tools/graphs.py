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
    node_pt="point",
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
            intsec = nodes[node_geom].intersects(row[l_i])
            n_int = len(nodes[intsec])
            # If no intersections, then store in `unk` list
            if n_int == 0:
                unk.append([sid, row[t1_i], row[t2_i], row[l_i]])
                add_node = False  # Do not add nodes to node seq
            # If one intersection, get node
            elif n_int == 1:
                label = nodes[intsec][node_label].values[0]
                node = [[sid, label, row[t1_i], row[t2_i], row[l_i], n_int]]
            # If two or more intersections, use helper function to get sequence
            else:
                cur_line = row[l_i] # Get the linestring
                node_chk = nodes[intsec] # Get the nodes to check
                labels = _handle_multi(cur_line, node_chk, node_label, node_pt)
                node = []
                for lbl in labels:
                    node += [[sid, lbl, row[t1_i], row[t2_i], row[l_i], n_int]]
        if add_node:
            node_seq += node
        else:
            add_node = True
    node_seq = pd.DataFrame(node_seq, columns=node_columns)
    unk = pd.DataFrame(unk, columns=unk_columns)
    return (node_seq, unk)


def _handle_multi(line, intsec, node_label, node_pt):
    """Get a sequence of nodes from multiple intersections.

    :type line: shapely.LineString
    :param intsec: The intersected node data.
    :type intsec: gpd.GeoDataFrame
    :param node_label: Name of the column containing node labels.
    :type node_label: str
    :param node_pt: Name of the column containing the node point geometries.
    :type node_pt: str
    :return labels: Tuple of labels, ordered by time.
    :type labels: (str, str)

    This function determines the sequence of nodes in the case of multiple node intersections as follows:

    * It projects the node points onto the line running through the line segment.
    * It determines the direction of movement along the line segment by determining if the ``x`` coordinate (longitude) is increasing from one end of the line to the other, or if it is decreasing.
    * It sorts the projected node coordinates by their ``x`` coordinate. It sorts in ascending order if the line segment moves from west to east; it sorts in descending order if the line segment moves from east to west.

    The function returns the node labels in sequence.
    """
    line1 = np.array(line.coords[0])
    line2 = np.array(line.coords[1])
    # Check for vertical line (if vertical handle manually)
    if line1[0] == line2[0]:
        return ("_MULTI_MANUAL",) * len(intsec)
    # Get coordinates of point as ``np.array``
    intsec["_coord"] = intsec[node_pt].apply(lambda x: np.array(x.coords[0]))
    # Move the line start to the origin; reposition the line stop and nodes
    line1_adj = np.array((0, 0))
    line2_adj = line2 - line1
    intsec["_adj"] = intsec["_coord"].apply(lambda x: x - line1)
    # Project nodes onto the line spanned by adjusted line stop
    intsec["_proj_adj"] = intsec["_adj"].apply(lambda x: _proj_xu(x, line2_adj))
    # Move the coordinates back to original area
    intsec["_proj"] = intsec["_proj_adj"].apply(lambda x: x + line1)
    # Get the ``x`` coordinates of the projection
    intsec["_x"] = intsec["_proj"].apply(lambda x: x[0])
    # Check that ``x`` values are unique; handle matching ``x`` values manually
    if len(intsec) != len(intsec["_x"].unique()):
        return ("_MULTI_MANUAL",) * len(intsec)
    # Determine whether to sort ascending or descending
    if line1[0] < line2[0]:
        ascending = True
    else:
        ascending = False
    intsec = intsec.sort_values("_x", ascending=ascending)
    # Return the sorted labels
    return tuple(intsec[node_label].values)


def _proj_xu(x, u):
    """Project vector ``x`` onto the line spanned by ``u``."""

    return np.dot(x, u) / np.dot(u, u) * u


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

    A "graph of direct linkages" (GDL) is a directed graph in which edges represent the movement of ships from one node to the next. Given a voyage from port A to B to C, the graph will consist of directed edges from A to B and from B to C, without an edge from A to C. [#GDL_ref]_

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

    A "graph of all linkages" (GAL) is an undirected graph in which edges represent the co-occurrence of nodes on a voyage by a given ship. Given a voyage from port A to B to C, the graph will consist of undirected edges between A and B, between A and C, and between B and C. [#GAL_ref]_

    .. [#GAL_ref] César Ducruet and Theo Notteboom, "The worldwide maritime network of container shipping: spatial structure and regional dynamics," *Global Networks* 12, no. 3 (2012): 402--3.
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
