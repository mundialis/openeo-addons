#!/usr/bin/env python3
############################################################################
#
# MODULE:       g.region.bbox
# AUTHOR(S):    Markus Metz
# PURPOSE:      Sets the region from a bounding box and CRS for that bbox
# COPYRIGHT:    (C) 2019 by mundialis, and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

#%module
#% description: Sets the region from a bounding box and CRS for that bbox.
#% keyword: general
#% keyword: settings
#% keyword: computational region
#% keyword: extent
#%end
#%flag
#% key: p
#% description: Print the current region
#% guisection: Print
#%end
#%flag
#% key: g
#% description: Print in shell script style
#% guisection: Print
#%end
#%option
#% key: n
#% type: string
#% required: yes
#% multiple: no
#% key_desc: value
#% description: Value for the northern edge
#% guisection: Bounds
#%end
#%option
#% key: s
#% type: string
#% required: yes
#% multiple: no
#% key_desc: value
#% description: Value for the southern edge
#% guisection: Bounds
#%end
#%option
#% key: e
#% type: string
#% required: yes
#% multiple: no
#% key_desc: value
#% description: Value for the eastern edge
#% guisection: Bounds
#%end
#%option
#% key: w
#% type: string
#% required: yes
#% multiple: no
#% key_desc: value
#% description: Value for the western edge
#% guisection: Bounds
#%end
#%option
#% key: crs
#% type: string
#% required: no
#% multiple: no
#% key_desc: value
#% answer: EPSG:4326
#% label: CRS of the coordinates (default EPSG:4326)
#% description: CRS must be EPSG code or proj string
#% guisection: Bounds
#%end
#%option G_OPT_R_INPUT
#% key: raster
#% required: no
#%end
#%option G_OPT_STRDS_INPUT
#% key: strds
#% required: no
#%end

import sys

import grass.script as grass
from osgeo import osr, ogr


def main():
    bboxcrs = options['crs']
    in_n = float(options['n'])
    in_s = float(options['s'])
    in_w = float(options['w'])
    in_e = float(options['e'])
    raster = options['raster']
    strds = options['strds']

    source = osr.SpatialReference()
    if "EPSG" in bboxcrs:
        epsgcode = bboxcrs[5:len(bboxcrs)]
        source.ImportFromEPSG(epsgcode)
    else:
        source.ImportFromWkt(bboxcrs)

    source.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    outprojstring = grass.read_command('g.proj', flags='w')

    target = osr.SpatialReference()
    target.ImportFromWkt(outprojstring)
    target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    transform = osr.CoordinateTransformation(source, target)

    lower_left = ogr.CreateGeometryFromWkt(
        f"POINT ({in_w} {in_s})")
    lower_left.Transform(transform)
    upper_right = ogr.CreateGeometryFromWkt(
        f"POINT ({in_e} {in_n})")
    upper_right.Transform(transform)

    out_w = lower_left.GetPoint()[0]
    out_s = lower_left.GetPoint()[1]
    out_e = upper_right.GetPoint()[0]
    out_n = upper_right.GetPoint()[1]

    stepsize = (in_n - in_s) / 21.0
    counter = 1
    while counter < 21:
        x = in_w
        y = in_s + counter * stepsize
        border_point = ogr.CreateGeometryFromWkt(
            f"POINT ({x} {y})")
        border_point.Transform(transform)
        out_x = border_point.GetPoint()[0]
        out_y = border_point.GetPoint()[1]

        if out_w > out_x:
            out_w = out_x
        if out_e < out_x:
            out_e = out_x

        if out_s > out_y:
            out_s = out_y
        if out_n < out_y:
            out_n = out_y

        counter = counter + 1

    stepsize = (in_e - in_w) / 21.0
    counter = 1
    while counter < 21:
        x = in_w + counter * stepsize
        y = in_s
        border_point = ogr.CreateGeometryFromWkt(
            f"POINT ({x} {y})")
        border_point.Transform(transform)

        if out_w > out_x:
            out_w = out_x
        if out_e < out_x:
            out_e = out_x

        if out_s > out_y:
            out_s = out_y
        if out_n < out_y:
            out_n = out_y
        counter = counter + 1

    outflags = ""
    if flags['p']:
        outflags = 'p'
    if flags['g']:
        outflags = 'g'

    if raster:
        grass.run_command('g.region', n=out_n, s=out_s, w=out_w, e=out_e,
                          align=raster, flags=outflags)
    elif strds:
        strds_info = grass.parse_command('t.info', input=strds, flags='g',
                                         delimiter='=')
        res = ((float(strds_info['nsres_min'])
               + float(strds_info['ewres_min'])) / 2.0)
        outflags = outflags + 'a'
        grass.run_command('g.region', n=out_n, s=out_s, w=out_w, e=out_e,
                          res=res, flags=outflags)
    else:
        grass.run_command('g.region', n=out_n, s=out_s, w=out_w, e=out_e,
                          flags=outflags)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
