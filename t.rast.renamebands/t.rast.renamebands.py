#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.renamebands
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Rename band names in a given STRDS
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

#%module
#% description: Rename bands in a given STRDS.
#% keyword: temporal
#% keyword: algebra
#% keyword: raster
#% keyword: time
#%end

#%option G_OPT_STRDS_INPUT
#%end

#%option G_OPT_STRDS_OUTPUT
#%end

#%option
#% key: target
#% type: string
#% label: new band names
#% multiple: yes
#% required: yes
#%end

#%option
#% key: source
#% type: string
#% label: old band names
#% multiple: yes
#% required: no
#%end


import grass.script as grass


def main():
    # lazy imports
    import grass.temporal as tgis

    # Get the options
    _input = options["input"]
    output = options["output"]
    source = options["source"]
    target = options["target"]

    # Make sure the temporal database exists
    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    # specs of input strds
    sp = tgis.open_old_stds(input, "strds", dbif)
    ttype, stype, title, descr = sp.get_initial_values()
    dbif.close()

    # t.rast.list with columns name, start date, band reference
    rlist = grass.read_command("t.rast.list", input=_input, columns="name,start_time,semantic_label", flags="u")

    rlistfile = grass.tempfile(create=False)
    fd = open(rlistfile, "w")

    if source:
        source = source.split(',')
    target = target.split(',')

    # modify band names
    for rmap in rlist.splitlines():
        name, start_time, semantic_label = rmap.split('|')
        if source:
            if semantic_label in source:
                idx = source.index(semantic_label)
                semantic_label = target[idx]
        else:
            semantic_label = target[0]
        fd.write("%s|%s|%s\n" % (name, start_time, semantic_label))
    
    fd.close()

    # t.create, use specs of input strds
    grass.run_command('t.create', type='strds', output=output,
                      temporaltype=ttype, semantictype=stype,
                      title=title, description=descr)

    # t.register to create new strds
    grass.run_command('t.register', input=output, file=rlistfile)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
