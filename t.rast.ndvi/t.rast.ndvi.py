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
# % key: red
# % type: string
# % description: Bandname to be used as red band
# % required: no
# % multiple: no
# % answer: red
# %end

# %option
# % key: nir
# % type: string
# % description: Bandname to be used as nir band
# % required: no
# % multiple: no
# % answer: nir
# %end

# %option
# % key: target
# % type: string
# % description: Output bandname
# % required: no
# % multiple: no
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

# see https://processes.openeo.org/#ndvi

def main():

    # Get the options
    _input = options["input"]
    output = options["output"]
    base = options["basename"]
    method = options["method"]
    red_band = options["red"]
    nir_band = options["nir"]
    target_band = options["target"]
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

    # get the sensor appreviation split by _
    sensor_abbr = None
    for band in input_bands:
        if "_" in band:
            sensor_abbr = band.split('_')[0]
            # TODO: check if sensor abbreviation changes
            break

    # find bands
    if red_band not in input_bands:
        if red_band != "red":
            grass.fatal("Band %s not found in %s" % (red_band, _input))

        red_band = None
        if sensor_abbr is not None:
            if sensor_abbr == "L5":
                red_band = "L5_3"
            elif sensor_abbr == "L7":
                red_band = "L7_3"
            elif sensor_abbr == "L8":
                red_band = "L8_4"
            elif sensor_abbr == "S2":
                red_band = "S2_4"

        if red_band is None:
            grass.fatal("No red channel band found in %s" % (_input))

    if nir_band not in input_bands:
        if nir_band != "nir":
            grass.fatal("Band %s not found in %s" % (nir_band, _input))

        nir_band = None
        if sensor_abbr is not None:
            if sensor_abbr == "L5":
                nir_band = "L5_4"
            elif sensor_abbr == "L7":
                nir_band = "L7_4"
            elif sensor_abbr == "L8":
                nir_band = "L8_5"
            elif sensor_abbr == "S2":
                nir_band = "S2_8"

        if nir_band is None:
            grass.fatal("No nir channel band found in %s" % (_input))

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

    # if target band is given, the new raster maps must be registered in the input strds
    if target_band:
        import grass.temporal as tgis

        # Make sure the temporal database exists
        tgis.init()
        # We need a database interface
        dbif = tgis.SQLDatabaseInterfaceConnection()
        dbif.connect()

        in_sp = tgis.open_old_stds(_input, "strds", dbif)
        out_sp = tgis.open_old_stds(output, "strds", dbif)
        maps = out_sp.get_registered_maps_as_objects(dbif=dbif)

        if not maps:
            dbif.close()
            grass.warning("Space time raster dataset <%s> is empty" % in_sp.get_id())
            return

        for map in maps:
            map.set_semantic_label(target_band)

            # Insert map in temporal database
            map.update(dbif)
            in_sp.register_map(map, dbif)

        # remove temporary strds
        dbif.close()

        grass.run_command('t.remove', inputs=output, type="strds",
                          flags='f')


###############################################################################


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
