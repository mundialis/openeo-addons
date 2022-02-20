#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.renamelabels
# AUTHOR(S):    Markus Metz, mundialis
#
# PURPOSE:      Rename semantic labels in a given STRDS
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
# % description: Rename semantic labels in a given STRDS.
# % keyword: temporal
# % keyword: algebra
# % keyword: raster
# % keyword: time
# %end

# %option G_OPT_STRDS_INPUT
# %end

# %option G_OPT_STRDS_OUTPUT
# %end

# %option
# % key: new
# % type: string
# % label: new band names
# % multiple: yes
# % required: yes
# %end

# %option
# % key: old
# % type: string
# % label: old band names
# % multiple: yes
# % required: no
# %end


import grass.script as grass


def main():
    # lazy imports
    import grass.temporal as tgis

    # Get the options
    _input = options["input"]
    output = options["output"]
    source = options["old"]
    target = options["new"]

    # Make sure the temporal database exists
    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    # specs of input strds
    sp = tgis.open_old_stds(_input, "strds", dbif)
    ttype, stype, title, descr = sp.get_initial_values()
    dbif.close()

    # t.rast.list with columns name, start date, band reference
    rlist = grass.read_command("t.rast.list", input=_input, columns="name,mapset,start_time,end_time,semantic_label", flags="u")

    rlistfile = grass.tempfile(create=False)
    fd = open(rlistfile, "w")

    # test if provided source semantic labels are existing in the input strds

    if source:
        source = source.split(',')
    target = target.split(',')

    # modify band names
    for rmap in rlist.splitlines():
        name, mapset, start_time, end_time, old_label = rmap.split('|')
        new_label = None
        if source:
            if old_label in source:
                idx = source.index(old_label)
                new_label = target[idx]
            # keep old label if no new label could be determined
            # note that python prints a None object as literal "None", skip
            elif old_label and old_label != "None":
                new_label = old_label
        else:
            new_label = target[0]

        if mapset:
            name = f"{name}@{mapset}"
        if new_label:
            if end_time and end_time != "None":
                fd.write("%s|%s|%s|%s\n" % (name, start_time, end_time, new_label))
            else:
                fd.write("%s|%s||%s\n" % (name, start_time, new_label))
        else:
            # also register maps if no new label could be determined
            if end_time and end_time != "None":
                fd.write("%s|%s|%s|\n" % (name, start_time, end_time))
            else:
                fd.write("%s|%s||\n" % (name, start_time))

    fd.close()

    # t.create, use specs of input strds
    grass.run_command('t.create', type='strds', output=output,
                      temporaltype=ttype, semantictype=stype,
                      title=title, description=descr)

    # t.register to create new strds
    grass.run_command('t.register', input=output, file=rlistfile, overwrite=True)

    grass.try_remove(rlistfile)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
