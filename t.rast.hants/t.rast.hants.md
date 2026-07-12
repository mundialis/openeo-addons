## DESCRIPTION

*t.rast.hants* uses [r.hants](r.hants.md) to filter map values and fill
gaps in a space time raster dataset (STRDS).

The user must provide an input and an output space time raster dataset
The resulting STRDS will have the same temporal resolution as the input
dataset. All maps will be processed using the current region settings.

The user can select a subset of the input space time raster dataset for
processing using a SQL WHERE statement. The number of CPU's to be used
for parallel processing can be specified with the *nprocs* option to
speedup the computation on multi-core system.

## SEE ALSO

*[r.hants](r.hants.md), [t.info](t.info.md), [g.region](g.region.md),
[r.mask](r.mask.md)*

## AUTHOR

Markus Metz, [mundialis](https://www.mundialis.de/), Germany
