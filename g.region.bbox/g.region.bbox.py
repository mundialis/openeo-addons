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

import sys

import grass.script as grass

def main():
    bboxcrs = options['crs']
    in_n = float(options['n'])
    in_s = float(options['s'])
    in_w = float(options['w'])
    in_e = float(options['e'])

    inprojstring = bboxcrs
    if "EPSG" in bboxcrs:
        epsgcode = bboxcrs[5:len(bboxcrs)]
        inprojstring = grass.read_command('g.proj', epsg=epsgcode, flags='j')

    outprojstring = grass.read_command('g.proj', flags='j')
    
    n = (in_n + in_s) / 2.0
    e = (in_e + in_w) / 2.0

    outcoords = grass.read_command('m.proj', coordinates=("%.16g,%.16g") % (e, n),
                                   proj_in=inprojstring,
                                   proj_out=outprojstring,
                                   separator=',', flags='d')

    out_e, out_n, z = outcoords.split(',')
    out_e = float(out_e)
    out_n = float(out_n)
    out_w = out_e
    out_s = out_n

    tmpfile = grass.tempfile()
    fd = open(tmpfile, "w")
    x = in_w
    y = in_n
    fd.write("%.16g,%.16g\n" % (x, y))
    x = in_e
    y = in_n
    fd.write("%.16g,%.16g\n" % (x, y))
    x = in_e
    y = in_s
    fd.write("%.16g,%.16g\n" % (x, y))
    x = in_w
    y = in_s
    fd.write("%.16g,%.16g\n" % (x, y))

    stepsize = (in_n - in_s) / 21.0
    counter = 1
    while counter < 21:
        x = in_w
        y = in_s + counter * stepsize
        fd.write("%.16g,%.16g\n" % (x, y))
        x = in_e
        fd.write("%.16g,%.16g\n" % (x, y))
        
        counter = counter + 1

    stepsize = (in_e - in_w) / 21.0
    counter = 1
    while counter < 21:
        x = in_w + counter * stepsize
        y = in_s
        fd.write("%.16g,%.16g\n" % (x, y))
        y = in_n
        fd.write("%.16g,%.16g\n" % (x, y))
        
        counter = counter + 1
    
    fd.close()

    outcoords = grass.read_command('m.proj', input=tmpfile,
                                   proj_in=inprojstring,
                                   proj_out=outprojstring,
                                   separator=',', flags='d')

    for line in outcoords.splitlines():
        e, n, z = line.split(',')
        e = float(e)
        n = float(n)
        if out_e < e:
            out_e = e
        if out_w > e:
            out_w = e
        if out_n < n:
            out_n = n
        if out_s > n:
            out_s = n

    grass.try_remove(tmpfile)

    outflags = ""
    if flags['p']:
        outflags = 'p'
    if flags['g']:
        outflags = 'g'

    grass.run_command('g.region', n=out_n, s=out_s, w=out_w, e=out_e, flags=outflags)

    return 0

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
