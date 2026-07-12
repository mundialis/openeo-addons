## DESCRIPTION

*t.rast.mask* applies one strds as a mask to another strds. By default,
all cells in the input strds are set to *mask_value* where the mask
strds is NULL or zero. This behaviour can be inverted with the *-i*
flag, such that all cells in the input strds set to *mask_value* where
the mask strds is not NULL and not zero.

Any semantic labels in the input strds are transferred to the output
strds.

This module expects several parameters. The resulting space time raster
dataset must be specified in the **output** option together with the
**basename** of generated raster maps that are registered in the
resulting STRDS. Empty maps resulting from map-calculation are not
registered by default. This behavior can be changed with the **-n**
flag. The flag **-s** can be used to assure that only spatially related
maps in the STRDS's are processed. Spatially related means that
temporaly related maps overlap in their spatial extent.

## SEE ALSO

*[t.rast.algebra](t.rast.algebra.md),
[i.band.library](i.band.library.md),
[r.semantic.label](r.semantic.label.md)*

[Temporal data processing
Wiki](http://grasswiki.osgeo.org/wiki/Temporal_data_processing)

## AUTHOR

Markus Metz, [mundialis](https://www.mundialis.de/), Germany
