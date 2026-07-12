## DESCRIPTION

*t.rast.ndvi* calculates NDVI from a STRDS. It uses a single STRDS as
input and calculates a new STRDS using the red and nir bands included in
the input STRDS.

This module is a front-end for *[t.rast.mapcalc](t.rast.mapcalc.md)*.

Different bands must be referenced in the expression by *data\[index\]*
with index being a number starting with 0. For example, with Sentinel-2,
*data\[3\]* refers to the fourth Sentinel-2 band "S2_4 Visible (Red)".
*t.rast.bandcalc* replaces *data\[index\]* with the according selections
of the input STRDS.

This module expects several parameters. The resulting space time raster
dataset must be specified in the **output** option together with the
**basename** of generated raster maps that are registered in the
resulting STRDS. Empty maps resulting from map-calculation are not
registered by default. This behavior can be changed with the **-n**
flag. The flag **-s** can be used to assure that only spatially related
maps in the STRDS's are processed. Spatially related means that
temporaly related maps overlap in their spatial extent.

## SEE ALSO

*[t.rast.mapcalc](t.rast.mapcalc.md),
[i.band.library](i.band.library.md),
[r.semantic.label](r.semantic.label.md)*

[Temporal data processing
Wiki](http://grasswiki.osgeo.org/wiki/Temporal_data_processing)

## AUTHOR

Markus Metz, [mundialis](https://www.mundialis.de/), Germany
