#!/usr/bin/env python
#
############################################################################
#
# MODULE:        r.scaleminmax
# AUTHOR(S):     Markus Metz, mundialis
# PURPOSE:       Helper module for openeo
# COPYRIGHT:     (C) 2019 by Markus Metz, and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

#%module
#% description: Rescales a raster map to new min, max values.
#% keyword: raster
#% keyword: algebra
#%end
#%option G_OPT_R_INPUT
#% description: Name of input raster map
#%end
#%option G_OPT_R_OUTPUT
#% description: Name of output raster map
#%end
#%option
#% key: min
#% type: double
#% description: New minimum value
#%end
#%option
#% key: max
#% type: double
#% description: New maximum value
#%end
#%option
#% key: type
#% type: string
#% description: Output datatype
#% options: CELL,FCELL,DCELL
#% answer: DCELL
#%end


import os
from grass.script import core as gcore
from grass.script import raster as grast
from grass.exceptions import CalledModuleError


def main():
    options, flags = gcore.parser()

    map_in = options["input"]
    map_out = options["output"]
    newmin = options["min"]
    newmax = options["max"]

    outtype = "double"
    if options["type"] == "CELL":
        outtype = "round"
    elif options["type"] == "FCELL":
        outtype = "float"

    rinfo = grast.raster_info(map_in)
    oldmin = rinfo["min"]
    oldmax = rinfo["max"]

    grast.mapcalc(
        "$map_out = ${outtype}((double($map_in - $oldmin) / ($oldmax - $oldmin)) * ($newmax - $newmin) + $newmin)",
        map_out=map_out,
        map_in=map_in,
        outtype=outtype,
        oldmin=oldmin,
        oldmax=oldmax,
        newmin=newmin,
        newmax=newmax,
    )


if __name__ == "__main__":
    main()
