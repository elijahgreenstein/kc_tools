# Overview

A set of tools for working with the Kobe Collection: ship logbook data from 1889 to 1961 included in the [International Comprehensive Ocean-Atmosphere Data Set](https://icoads.noaa.gov/) (ICOADS). These tools are designed around the analysis of historical patterns of Japanese commercial shipping.

With minor modifications, the tools can also be applied to other collections in ICOADS.

# Data cleaning

## Preprocessing

[Individual ICOADS observations](https://rda.ucar.edu/datasets/d548000/#) can be accessed from the National Center for Atmospheric Research. ICOADS data follows the International Maritime Meteorological Archive (IMMA) common data format.[^IMMA_format] Analysis of shipping patterns does not require meteorological or ocean surface data; it only requires the following IMMA fields:

[^IMMA_format]: Smith, S.R., E. Freeman, S.J. Lubker, S.D. Woodruff, S.J. Worley, W.E. Angel, D.I. Berry, P. Brohan P, Z. Ji, E.C. Kent, et al., 2016: The International Maritime Meteorological Archive (IMMA) Format <http://icoads.noaa.gov/e-doc/imma/R3.0-imma1.pdf>.

1. C0-1 Year
1. C0-2 Month
1. C0-3 Day
1. C0-4 Hour
1. C0-5 Latitude
1. C0-6 Longitude
1. C0-15 ID
1. C1-6 Deck

Use the `AWK` snippet, `./src/fields.awk`, to extract the above fields from the Kobe Collection from the ICOADS. From the command line, use the following to preprocess data in `<RAW_DATA_DIR>` and to write the preprocessed data to `<PREPROC_DATA_DIR>`. The preprocessed data will be named by year and month (`YYYY-MM.csv`).

```{.bash}
$ for file in <RAW_DATA_DIR>/IMMA*
> do name=${file: -7}
> gawk -f <AWK SCRIPT_PATH> ${file} > <PREPROC_DATA_DIR>/${name}.csv
> done
```

