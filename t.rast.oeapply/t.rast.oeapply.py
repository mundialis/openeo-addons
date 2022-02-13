#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.mask
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Mask a STRDS with another STRDS
# COPYRIGHT:    (C) 2022 by mundialis and the GRASS Development Team
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
# % description: Mask a STRDS with another STRDS.
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

import sys
import grass.script as grass


############################################################################

# see https://processes.openeo.org/#ndvi

def main():
    # lazy imports
    import grass.temporal as tgis

    # Get the options
    _input = options["input"]
    expression = options["expression"]
    output = options["output"]
    base = options["basename"]
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
    input_labels = None
    if int(t_info["number_of_semantic_labels"]) > 0:
        input_labels = t_info["semantic_labels"].split(',')

    if input_labels is None:
        grass.run_command('t.rast.mapcalc',
                          input=_input,
                          expression=expression,
                          method="equal",
                          output=output,
                          basename=base,
                          nprocs=nprocs, flags=new_flags)
        sys.exit()

    # Make sure the temporal database exists
    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    in_sp = tgis.open_old_stds(_input, "strds", dbif)
    # specs of input strds
    ttype, stype, title, descr = in_sp.get_initial_values()

    # t.create, use specs of input strds
    # use tgis.open_new_stds() instead ?
    grass.run_command('t.create', type='strds', output=output,
                      temporaltype=ttype, semantictype=stype,
                      title=title, description=descr)

    out_sp = tgis.open_old_stds(output, "strds", dbif)

    # preserve labels in input
    counter = 0
    for label in input_labels:
        counter += 1

        # extract
        extract_strds = "%s_extract" % (output)
        grass.run_command('t.rast.extract',
                          input=_input,
                          output=extract_strds,
                          where="semantic_label = '%s'" % label)

        # apply
        apply_strds = "%s_masked" % (output)
        label_expression = expression.replace(_input, extract_strds)

        grass.run_command('t.rast.mapcalc',
                          input=extract_strds,
                          expression=label_expression,
                          method="equal",
                          output=apply_strds,
                          basename="%s_%d" % (base, counter),
                          nprocs=nprocs, flags=new_flags)

        # remove extract_strds
        grass.run_command('t.remove', inputs=extract_strds, flags='f')

        apply_sp = tgis.open_old_stds(apply_strds, "strds", dbif)
        maps = apply_sp.get_registered_maps_as_objects(dbif=dbif)

        for map in maps:
            map.set_semantic_label(label)

            # update map in temporal database
            map.update(dbif)
            out_sp.register_map(map, dbif)

        # remove masked_strds
        grass.run_command('t.remove', inputs=apply_strds, flags='f')

    # Update the spatio-temporal extent and the metadata table entries
    out_sp.update_from_registered_maps(dbif)

    # done


###############################################################################


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
