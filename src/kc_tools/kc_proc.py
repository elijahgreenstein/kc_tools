"""Tools to process Kobe Collection data.

These tools clean Kobe Collection data from ICOADS.

.. warning::
    The data must be preprocessed before using these tools. See the project
    ``README`` for details. The preprocessed data must contain the following
    eight IMMA fields in the following order: C0-1 year, C0-2 month, C0-3 day,
    C0-4 hour, C0-5 latitude, C0-6 longitude, C0-15 ID, and C1-6 deck. See the
    repository ``README.md`` for details.

Use ``kc_tools.kc_proc.proc_year`` to clean the preprocessed data in
``<PREPROC_DATA_DIR>`` and write the cleaned data to ``<PROC_DATA_DIR>``:

>>> import kc_tools as kc
>>> import pathlib
>>> input_dir = pathlib.Path("<PREPROC_DATA_DIR>")
>>> output_dir = pathlib.Path("<PROC_DATA_DIR>")
>>> # For the complete Kobe Collection, 1889 to 1961:
>>> for year in range(1889, 1962):
...     df = kc.kc_proc.proc_year(year, input_dir)
...     df.to_csv(output_dir / f"{year}.csv", index=False)

"""

import datetime
import numpy as np
import pandas as pd
import pathlib

# Default column names on load
_COL_LOAD = ["year", "month", "day", "hour", "lat", "long", "id", "DCK"]
# Default data types on load
_DTYPE_LOAD = {"id": str, "lat": str, "hour": float}
# Alternative data types, for cases where "hour" field is only spaces "    "
_DTYPE_ALT = {"id": str, "lat": str, "hour": str}
# Default output column names
_OUT_COL = ["DATETIME", "LAT", "LONG", "ID", "DCK"]

def load_raw(path):
    """Load raw Kobe Collection data.

    :param path: The file to load.
    :type path: str, pathlib.Path
    :return df: The data.
    :rtype df: pd.DataFrame
    """
    # Try the default load
    try:
        df = pd.read_csv(path, names=_COL_LOAD, dtype=_DTYPE_LOAD)
    # Clean the "hour" column if it fails to load as float (i.e. has entries
    # consisting of empty spaces).
    except ValueError:
        df = pd.read_csv(path, names=_COL_LOAD, dtype=_DTYPE_ALT)
        # Remove white space, and replace empty strings with np.nan values
        df["hour"] = df["hour"].str.strip()
        df["hour"] = df["hour"].replace('', np.nan)
        # Convert type back to float
        df["hour"] = df["hour"].astype(float)
    return df

def _proc_long180(df):
    """Convert longitude.

    Some observations range from -180 to 179.99; others from 0 to 359.99.
    Convert the latter to the former for consistency.
    """
    df["long180"] = df["long"]
    df["long180"] = df["long180"].case_when([
        (df["long"] > 18000, df["long"] - 36000)
    ])
    # Convert to string for processing as coordinate
    df["long180"] = df["long180"].astype(str)
    return df

def _proc_coord(df, col):
    """Process latitude and longitude to degrees to two decimal places.
    """
    left = df[col].str.strip().str[:-2]
    right = df[col].str.strip().str[-2:]
    new_col = left + "." + right
    return new_col

def proc_kobe(df):
    """Process Kobe Collection dataframe.

    :param df: Preprocessed Kobe Collection data.
    :type df: pd.DataFrame
    :return df: Processed dataframe.
    :rtype df: pd.DataFrame
    """
    # Process the dataframe if it is not empty.
    if df.shape[0] > 0:
        df["hour"] = df["hour"] / 100               # Rescale hour
        df["DATETIME"] = pd.to_datetime(            # Generate datetime field
            df[["year", "month", "day", "hour"]],
            errors="coerce"
        )
        df = _proc_long180(df)                      # Convert long to -180/180
        df["LAT"] = _proc_coord(df, "lat")          # Process lat, long
        df["LONG"] = _proc_coord(df, "long180")
        df["ID"] = df["id"].str.strip()             # Remove whitespace from ids
        df = df[_OUT_COL]
    # If dataframe is empty, return empty dataframe with default column names
    else:
        df = pd.DataFrame(columns=_OUT_COL)
    return df

def proc_year(yr, path):
    """Process Kobe Collection data by year.

    :param yr: Year to process.
    :type yr: int
    :param path: Directory containing preprocessed files, named ``YYYY-MM.csv``.
    :type path: str, pathlib.Path
    :return: Concatenated data from the entire year.
    :rtype: pd.DataFrame
    """
    path = pathlib.Path(path)
    df = load_raw(path / f"{yr}-01.csv")
    df = proc_kobe(df)
    for month in range(2, 13):
        mo = str(month).rjust(2, "0")
        new_df = load_raw(path / f"{yr}-{mo}.csv")
        new_df = proc_kobe(new_df)
        if df.shape[0] == 0:
            df = new_df
        elif new_df.shape[0] == 0:
            pass
        else:
            df = pd.concat([df, new_df], axis=0, ignore_index=True)
    return df.sort_values("DATETIME").reset_index(drop=True)

