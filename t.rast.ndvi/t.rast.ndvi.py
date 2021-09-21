#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.ndvi
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Calculate NDVI from a given STRDS
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
# % description: Calculates NDVI from a given STRDS.
# % keyword: temporal
# % keyword: algebra
# % keyword: raster
# % keyword: time
# %end

# %option G_OPT_STRDS_INPUT
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
    input_bands = t_info["band_names"].split(',')

    # get the sensor appreviation split by _
    sensor_abbr = None
    for band in input_bands:
        if "_" in band:
            sensor_abbr = band.split('_')[0]
            # TODO: check if sensor abbreviation changes
            break

    # hard-coded for now, as long as there are no STAC-like common names
    # in the output of g.bands

    red_band = None
    nir_band = None
    if sensor_abbr is not None:
        if sensor_abbr == "L5":
            red_band = "L5_3"
            nir_band = "L5_4"
        elif sensor_abbr == "L7":
            red_band = "L7_3"
            nir_band = "L7_4"
        elif sensor_abbr == "L8":
            red_band = "L8_4"
            nir_band = "L8_5"
        elif sensor_abbr == "S2":
            red_band = "S2_4"
            nir_band = "S2_8"

    if red_band is None:
        grass.warning("Assuming 'red' and 'nir as band names in %s" % _input)
        red_band = "red"
        nir_band = "nir"

    new_inputs = []
    if '@' in _input:
        strds, mapset = _input.split('@')
        new_inputs.append("%s.%s@%s" % (strds, red_band, mapset))
        new_inputs.append("%s.%s@%s" % (strds, nir_band, mapset))

        expression = ("float(%(instrds)s.%(nir)s@%(mapset)s - %(instrds)s.%(red)s@%(mapset)s) / "
                      "(%(instrds)s.%(nir)s@%(mapset)s + %(instrds)s.%(red)s@%(mapset)s)" %
                      {"instrds": strds,
                       "nir": nir_band,
                       "red": red_band,
                       "mapset": mapset})
    else:
        new_inputs.append("%s.%s" % (_input, red_band))
        new_inputs.append("%s.%s" % (_input, nir_band))
        expression = ("float(%(instrds)s.%(nir)s - %(instrds)s.%(red)s) / "
                      "(%(instrds)s.%(nir)s + %(instrds)s.%(red)s)" %
                      {"instrds": _input,
                       "nir": nir_band,
                       "red": red_band})

    # print(expression)

    grass.run_command('t.rast.mapcalc', inputs=(',').join(new_inputs),
                      expression=expression, method=method,
                      output=output, basename=base,
                      nprocs=nprocs, flags=new_flags)

###############################################################################


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
