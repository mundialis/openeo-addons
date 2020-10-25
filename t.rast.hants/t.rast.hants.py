#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.hants
# AUTHOR(S):    Markus Metz
#               based on t.rast.neighbors
#
# PURPOSE:      Applies HANTS to a space time raster dataset.
# COPYRIGHT:    (C) 2019 by the GRASS Development Team
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

#%module
#% description: Applies HANTS to a space time raster dataset.
#% keyword: temporal
#% keyword: filtering
#% keyword: raster
#% keyword: time
#%end

#%option G_OPT_STRDS_INPUT
#%end

#%option G_OPT_STRDS_OUTPUT
#%end

#%option G_OPT_T_WHERE
#%end

#%option
#% key: nf
#% type: integer
#% description: Number of frequencies
#% required: yes
#% multiple: no
#%end

#%option
#% key: fet
#% type: double
#% description: Fit error tolerance
#% required: no
#% multiple: no
#% gisprompt:
#%end

#%option
#% key: dod
#% type: integer
#% description: Degree of over-determination
#% answer: 0
#% required: no
#% multiple: no
#%end

#%option
#% key: range
#% key_desc: lo,hi
#% type: double
#% description: Ignore values outside this range
#% required: no
#% multiple: no
#% gisprompt:
#%end

#%flag
#% key: n
#% description: Register Null maps
#%end

#%flag
#% key: l
#% description: Reject low outliers
#%end

#%flag
#% key: h
#% description: Reject high outliers
#%end

#%flag
#% key: i
#% description: Do not extrapolate, only interpolate
#%end

from __future__ import print_function

import copy
import grass.script as grass


############################################################################

def main():
    # lazy imports
    import grass.temporal as tgis
    import grass.pygrass.modules as pymod

    # Get the options
    input = options["input"]
    output = options["output"]
    where = options["where"]
    register_null = flags["n"]

    # Make sure the temporal database exists
    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    overwrite = grass.overwrite()

    sp = tgis.open_old_stds(input, "strds", dbif)
    maps = sp.get_registered_maps_as_objects(where=where, dbif=dbif)

    if not maps:
        dbif.close()
        grass.warning(_("Space time raster dataset <%s> is empty") % sp.get_id())
        return

    new_sp = tgis.check_new_stds(output, "strds", dbif=dbif,
                                               overwrite=overwrite)
    # Configure the HANTS module
    hants_flags = ""
    if flags["l"]:
        hants_flags = hants_flags + 'l'
    if flags["h"]:
        hants_flags = hants_flags + 'h'
    if flags["i"]:
        hants_flags = hants_flags + 'i'

    kwargs = dict()
    kwargs['nf'] = options['nf']
    if options['fet']:
        kwargs['fet'] = options['fet']
    kwargs['dod'] = options['dod']
    if options['range']:
        kwargs['range'] = options['range']
    kwargs['suffix'] = "_hants"
    if len(hants_flags) > 0:
        kwargs['flags'] = hants_flags

    count = 0
    num_maps = len(maps)
    new_maps = []

    maplistfile = script.tempfile()
    fd = open(maplistfile, 'w')

    # create list of input maps and their time stamps
    for map in maps:
        count += 1
        map_name = "{ba}_hants".format(ba=map.get_id())

        new_map = tgis.open_new_map_dataset(map_name, None, type="raster",
                                            temporal_extent=map.get_temporal_extent(),
                                            overwrite=overwrite, dbif=dbif)
        new_maps.append(new_map)

        f.write("{0}\n".format(map.get_id()))

    f.close()

    # run r.hants
    grass.run_command('r.hants', file=maplistfile, suffix="_hants", quiet=True, **kwargs)

    # Open the new space time raster dataset
    ttype, stype, title, descr = sp.get_initial_values()
    new_sp = tgis.open_new_stds(output, "strds", ttype, title,
                                descr, stype, dbif, overwrite)
    num_maps = len(new_maps)
    # collect empty maps to remove them
    empty_maps = []

    # Register the maps in the database
    count = 0
    for map in new_maps:
        count += 1

        if count %10 == 0:
            grass.percent(count, num_maps, 1)

        # Do not register empty maps
        map.load()
        if map.metadata.get_min() is None and \
            map.metadata.get_max() is None:
            if not register_null:
                empty_maps.append(map)
                continue

        # Insert map in temporal database
        map.insert(dbif)
        new_sp.register_map(map, dbif)

    # Update the spatio-temporal extent and the metadata table entries
    new_sp.update_from_registered_maps(dbif)
    grass.percent(1, 1, 1)

    # Remove empty maps
    if len(empty_maps) > 0:
        names = ""
        count = 0
        for map in empty_maps:
            if count == 0:
                count += 1
                names += "%s" % (map.get_name())
            else:
                names += ",%s" % (map.get_name())

        grass.run_command("g.remove", flags='f', type='raster', name=names, quiet=True)

    dbif.close()

############################################################################

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
