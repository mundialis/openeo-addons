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

# %option G_OPT_STRDS_INPUT
# % key: mask
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

# %option
# % key: value
# % type: string
# % label: The value used to replace masked cells
# % description: Default: NULL
# % required: no
# % multiple: no
# %end

# %flag
# % key: i
# % label: Invert the mask
# % description: Default: keep cells that are not NULL and not zero in the mask
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

# see https://processes.openeo.org/#mask

def main():
    # lazy imports
    import grass.temporal as tgis

    # Get the options
    _input = options["input"]
    mask = options["mask"]
    output = options["output"]
    base = options["basename"]
    mask_value = options["value"]
    nprocs = int(options["nprocs"])
    register_null = flags["n"]
    spatial = flags["s"]
    invert_mask = flags["i"]

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

    # get list of bands available in the mask strds
    t_info = grass.parse_command('t.info', input=mask, flags='g')
    if int(t_info["number_of_semantic_labels"]) > 1:
        grass.fatal("mask input must not contain several bands")

    if not mask_value:
        mask_value = "null()"

    if input_labels is None:
        if invert_mask:
            expression = ("%(outstrds)s = if(isnull(%(maskstrds)s), %(instrds)s, "
                          "if(%(maskstrds)s == 0, %(instrds)s, %(mask_value)s))" %
                          {"instrds": _input,
                           "maskstrds": mask,
                           "outstrds": output,
                           "mask_value": mask_value})
        else:
            expression = ("%(outstrds)s = if(isnull(%(maskstrds)s), %(mask_value)s, "
                          "if(%(maskstrds)s == 0, %(mask_value)s, %(instrds)s))" %
                          {"instrds": _input,
                           "maskstrds": mask,
                           "outstrds": output,
                           "mask_value": mask_value})

        grass.run_command('t.rast.algebra',
                          expression=expression,
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

        # mask
        masked_strds = "%s_masked" % (output)
        if invert_mask:
            expression = ("%(outstrds)s = if(isnull(%(maskstrds)s), %(instrds)s, "
                          "if(%(maskstrds)s == 0, %(instrds)s, %(mask_value)s))" %
                          {"instrds": extract_strds,
                           "maskstrds": mask,
                           "outstrds": masked_strds,
                           "mask_value": mask_value})
        else:
            expression = ("%(outstrds)s = if(isnull(%(maskstrds)s), %(mask_value)s, "
                          "if(%(maskstrds)s == 0, %(mask_value)s, %(instrds)s))" %
                          {"instrds": extract_strds,
                           "maskstrds": mask,
                           "outstrds": masked_strds,
                           "mask_value": mask_value})

        grass.run_command('t.rast.algebra',
                          expression=expression,
                          basename="%s_%d" % (base, counter),
                          nprocs=nprocs, flags=new_flags)

        # remove extract_strds
        grass.run_command('t.remove', inputs=extract_strds, flags='f')

        masked_sp = tgis.open_old_stds(masked_strds, "strds", dbif)
        maps = masked_sp.get_registered_maps_as_objects(dbif=dbif)

        for map in maps:
            map.set_semantic_label(label)

            # update map in temporal database
            map.update(dbif)
            out_sp.register_map(map, dbif)

        # remove masked_strds
        grass.run_command('t.remove', inputs=masked_strds, flags='f')

    # Update the spatio-temporal extent and the metadata table entries
    out_sp.update_from_registered_maps(dbif)

    dbif.close()

    # done


###############################################################################


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
