#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.bandcalc
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Perform spatio-temporal mapcalc expressions using different bands in a given STRDS
# COPYRIGHT:    (C) 2019 by mundialis and the GRASS Development Team
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
#############################################################################

# %module
# % description: Performs spatio-temporal mapcalc expressions using different bands in a given STRDS.
# % keyword: temporal
# % keyword: algebra
# % keyword: raster
# % keyword: time
# %end

# %option G_OPT_STRDS_INPUT
# %end

# %option
# % key: expression
# % type: string
# % description: Spatio-temporal mapcalc expression
# % required: yes
# % multiple: no
# %end

# %option G_OPT_T_SAMPLE
# % key: method
# % answer: equal
# %end

# %option G_OPT_STRDS_OUTPUT
# %end

# %option G_OPT_R_BASENAME_OUTPUT
# % key: basename
# % label: Basename for output raster maps
# % description: A numerical suffix separated by an underscore will be attached to create a unique identifier
# % required: yes
# %end

# %option
# % key: nprocs
# % type: integer
# % description: Number of r.mapcalc processes to run in parallel
# % required: no
# % multiple: no
# % answer: 1
# %end

# %flag
# % key: n
# % description: Register Null maps
# %end

# %flag
# % key: s
# % description: Check the spatial topology of temporally related maps and process only spatially related maps
# %end

import grass.script as grass


############################################################################


def main():

    # Get the options
    _input = options["input"]
    output = options["output"]
    expression = options["expression"]
    base = options["basename"]
    method = options["method"]
    nprocs = int(options["nprocs"])
    register_null = flags["n"]
    spatial = flags["s"]

    new_flags = ""
    if register_null:
        new_flags = "n"
    if spatial:
        new_flags = new_flags + "s"

    # get list of bands available in the input strds
    t_info = grass.parse_command('t.info', input=_input, flags='g')
    input_bands = t_info["semantic_labels"].split(',')

    nbands = len(input_bands)

    # find needed bands in formula: if "data[0]" in formula:
    # go through the list of bands and replace (str.replace(old, new)
    # in the formula e.g. data[0] with (input_strds + '.' + bandref[0])
    counter = 0
    new_inputs = []
    band_used = [False for i in range(nbands)]
    while counter < nbands:
        fstr = "data[" + str(counter) + "]"
        bandname = input_bands[counter]
        data_band = ("data.%s") % (bandname)
        if fstr in expression:
            band_used[counter] = True
            newstr = ("%s.%s") % (_input, bandname)
            new_inputs.append(newstr)
            expression = expression.replace(fstr, newstr)
        elif data_band in expression:
            band_used[counter] = True
            newstr = ("%s.%s") % (_input, bandname)
            new_inputs.append(newstr)
            expression = expression.replace(data_band, newstr)
        else:
            band_used[counter] = False
        counter = counter + 1
    # print(expression)

    grass.run_command('t.rast.mapcalc', inputs=(',').join(new_inputs),
                      expression=expression, method=method,
                      output=output, basename=base,
                      nprocs=nprocs, flags=new_flags)

###############################################################################


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
