"""Function to convert a series of points to a series of lines.

Given a series of points ordered by time, this function creates a series of lines between each sequential pair of points. The lines are stored in a column with type ``shapely.LineString``.
"""

import geopandas as gpd
import pandas as pd
import shapely


def pts2lines(df, dt_col="t", lat_col="lat", long_col="long"):
    """Generate a dataframe of line segments from point data.

    :param df: The data.
    :type df: pd.DataFrame
    :param dt_col: Name of the datetime column.
    :type dt_col: str, default: "t"
    :param lat_col: Name of the latitude column.
    :type lat_col: str, default: "lat"
    :param long_col: Name of the longitude column.
    :type long_col: str, default: "long"
    :return gdf: The data with a geometry column of linestrings connecting points sequentially.
    :rtype: gpd.GeoDataFrame
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
    geometry = res.apply(
        lambda r: shapely.LineString([[r.x1, r.y1], [r.x2, r.y2]]), axis=1
    )
    # Generate geopandas GeoDataFrame
    gdf = gpd.GeoDataFrame(res, geometry=geometry)
    return gdf
