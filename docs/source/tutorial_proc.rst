Tutorial: Cleaning the Kobe Collection
============================================================

Our first step in the data cleaning process is to extract the Kobe Collection (KC) from the ICOADS. Each KC observation includes data such as time and location, as well as meteorological data. For our purposes, we are only interested in the location of ships at particular times. We also want to keep track of individual ships, in order to piece together voyages from sequential observations by the same ship. We will therefore extract the following fields: year, month, day, hour, latitude, longitude, ship ID, and deck number. The "deck number" refers to a numerical code for the original source of the data. KC data comes from decks ``118``, ``119``, and ``762``.

An Awk snippet is provided in ``./src/fields.awk`` to extract these fields from the Kobe Collection. From the command line, we can use this script (``<AWK_PATH>``) to read the original ICOADS data from ``<RAW_DATA_DIR>`` (replace this with the path to the original data), extract observations from the KC decks, and write the fields listed above to files in a new directory, ``<PREPROC_DATA_DIR>``:

.. code-block:: bash

   for file in <RAW_DATA_DIR>/IMMA* # Each file begins with `IMMA`
   do name=${file: -7}              # The last 7 characters are YYYY-MM
   gawk -f <AWK_PATH> ${file} > <PREPROC_DATA_DIR>/${name}.csv
   done

The complete Kobe Collection is now organized in files by year and month (``YYYY-MM.csv``).

Our next step is to use `kc_tools` to clean the KC data in ``<PREPROC_DATA_DIR>`` and to write the cleaned data to files in a new directory, ``<PROC_DATA_DIR>``. The following code can be executed from the python REPL or copied into a file and executed with python:

>>> import kc_tools as kc
>>> import pathlib
>>> input_dir = pathlib.Path("<PREPROC_DATA_DIR>")
>>> output_dir = pathlib.Path("<PROC_DATA_DIR>")
>>> # Make sure the output directory exists:
>>> output_dir.mkdir(parents=True, exist_ok=True)
>>> # For the complete Kobe Collection, 1889 to 1961:
>>> for year in range(1889, 1962):
...     df = kc.kc_proc.proc_year(year, input_dir)
...     df.to_csv(output_dir / f"{year}.csv", index=False)

Now the cleaned data is organized by year (``YYYY.csv``) in the output directory. We can easily load the cleaned data with ``pandas``. Let's take a look at the observations for 1910:

>>> import pandas as pd
>>> df = pd.read_csv(output_dir / "1910.csv")
>>> df.head()
                     t   lat   long     id  dck
0  1910-01-01 00:00:00   5.9   91.1  09007  762
1  1910-01-01 01:00:00  47.8 -157.7  10003  762
2  1910-01-01 01:00:00  34.0  133.0  09051  762
3  1910-01-01 01:00:00  -4.7  129.4  10071  762
4  1910-01-01 02:00:00  37.2  122.9  09072  762

The cleaned data now consists of

.. table::
   :widths: auto

   ======== ============================
   ``t``    Date and hour of observation
   ``lat``  Latitude
   ``long`` Longitude
   ``id``   Ship ID number
   ``dck``  Deck (original data source)
   ======== ============================

