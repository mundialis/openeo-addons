# openeo-addons
openEO related GRASS GIS addons (see https://github.com/Open-EO/openeo-grassgis-driver)

## Installation
```
mkdir -p /src/grass_plugins/openeo-addons
grass --tmp-location EPSG:4326 --exec g.extension url=/src/grass_plugins/openeo-addons/r.scaleminmax extension=r.scaleminmax
grass --tmp-location EPSG:4326 --exec g.extension url=/src/grass_plugins/openeo-addons/t.rast.resample extension=t.rast.resample
```

## Overview

- g.region.bbox: sets the region from a bounding box and CRS for that bbox
- r.scaleminmax: rescales a raster map to new min, max values
- t.rast.bandcalc: performs spatio-temporal mapcalc expressions using different bands in a given STRDS
- t.rast.filterbands: extract selected bands from a given STRDS
- t.rast.hants: applies HANTS to a space time raster dataset
- t.rast.mask: Mask a STRDS with another STRDS
- t.rast.ndvi: calculates NDVI from a given STRDS
- t.rast.oeapply: Preserve semantic labels in t.rast.mapcalc
- t.rast.renamelabels: Rename semantic labels in a given STRDS
- t.rast.resample: applies a resampling method to each map in a space time raster dataset
- t.rast.udf: applies a user defined function (UDF) to aggregate a time series into a single output raster map
- t.rast2strds: creates a new strds from an existing raster and an existing strds
- v.in.geojson: imports a GeoJSON object
