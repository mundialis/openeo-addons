# openeo-addons
openEO related GRASS GIS addons

## Installation
mkdir -p /src/grass_plugins/openeo-addons
grass --tmp-location EPSG:4326 --exec g.extension url=/src/grass_plugins/openeo-addons/r.scaleminmax extension=r.scaleminmax
grass --tmp-location EPSG:4326 --exec g.extension url=/src/grass_plugins/openeo-addons/t.rast.resample extension=t.rast.resample


