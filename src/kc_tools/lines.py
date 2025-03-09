"""Tools to convert point data to a series of lines.
"""

import geopandas as gpd
import pandas as pd
import shapely


def pts2lines(df, dt_col="t", lat_col="lat", long_col="long"):
    """Generate a dataframe of line segments from point data.

    Given a series of points ordered by time, this function creates a series of lines between each sequential pair of points. The lines are stored in a column with type ``shapely.LineString``.

    :param df: The point data.
    :type df: pd.DataFrame
    :param dt_col: Name of the datetime column.
    :type dt_col: str, default: "t"
    :param lat_col: Name of the latitude column.
    :type lat_col: str, default: "lat"
    :param long_col: Name of the longitude column.
    :type long_col: str, default: "long"
    :return res: Dataframe of line segments with time data.
    :rtype: pd.DataFrame
    """
    df = df.sort_values(dt_col)  # Ensure that the dates are sorted
    df = df.dropna(axis=0)  # Remove rows with missing values
    res = pd.DataFrame(
        {
            "t1": df[dt_col][:-1].values,
            "t2": df[dt_col][1:].values,
            "x1": df[long_col][:-1].values,
            "x2": df[long_col][1:].values,
            "y1": df[lat_col][:-1].values,
            "y2": df[lat_col][1:].values,
        }
    )
    # Generate linestring geometry
    res["line"] = res.apply(
        lambda r: shapely.LineString([[r.x1, r.y1], [r.x2, r.y2]]), axis=1
    )
    return res[["t1", "t2", "line"]]


def batch_lines(df, t="t", x="long", y="lat", uid="id"):
    """Generate a dataframe of line segments organized by id.

    For each unique ID, ``pts2lines`` is used to generate line segments for that moving object. The line segments are then concatenated back into a single dataframe.

    :param df: The point data.
    :type df: pd.DataFrame
    :param t: Name of the time series column.
    :type t: str, default: "t"
    :param x: Name of the x coordinates (longitude) column.
    :type x: str, default: "long"
    :param y: Name of the y coordinates (latitude) column.
    :type y: str, default: "lat"
    :param uid: Name of the id column.
    :type uid: str, default: "id"
    :return res: Dataframe of line segments.
    :rtype: pd.DataFrame

    Use ``batch_lines`` to generate line segments for all ships in a dataframe.

    Example usage (set up ``in_dir`` and ``out_dir`` as ``pathlib.Path`` first):

    >>> import kc_tools as kc
    >>> import pandas as pd
    >>> dtypes = {"t": str, "lat": float, "long": float, "id": str, "dck": int}
    >>> for year in range(1889, 1962):  # Full Kobe Collection
    >>>     df = pd.read_csv(in_dir / f"{year}.csv", dtype=dtypes)
    >>>     lines = kc.batch_lines(df)
    >>>     if len(lines) > 0:          # Check for empty dataframes
    >>>         lines.to_csv(out_dir / f"{year}.csv", index=False)

    To load the data later as a Geopandas GeoDataFrame, use ``shapely.wkt.loads``:

    >>> import pandas as pd
    >>> import shapely
    >>> import geopandas as gpd
    >>> df = pd.read_csv(file)
    >>> gdf = gpd.GeoDataFrame(df, geometry="line")
    """
    res = []
    for val in df[uid].unique():
        subset = df[df[uid] == val]
        if subset.shape[0] > 1: # Must have two or more points in sequence
            lines = pts2lines(subset)
            lines["id"] = val
            res.append(lines)
        else:
            pass
    if len(res) > 0:
        # Concatenate the results back into a single data frame
        res = pd.concat(res, axis=0, ignore_index=True)
    return res
