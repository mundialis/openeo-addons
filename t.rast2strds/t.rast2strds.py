#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.rast2strds
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Create a new strds from an existing raster and an
#               existing strds
# COPYRIGHT:    (C) 2021 by the GRASS Development Team
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
# % description: Creates a new strds from an existing raster and an existing strds.
# % keyword: temporal
# % keyword: metadata
# % keyword: extent
# % keyword: time
# %end

# %option G_OPT_STDS_INPUT
# % key: strds
# % description: Name of an existing space time raster dataset
# %end

# %option G_OPT_R_INPUT
# % key: raster
# % description: Name of an existing raster map
# %end

# %option G_OPT_STDS_OUTPUT
# % description: Name of the new space time raster dataset
# %end

# %option
# % key: bandname
# % type: string
# % label: band name
# %end

from __future__ import print_function

import grass.script as grass

############################################################################


def main():
    # lazy imports
    import grass.temporal as tgis

    strdsin = options["strds"]
    rasterin = options["raster"]
    strdsout = options["output"]
    bandname = options["bandname"]

    type_ = "strds"

    # make sure the temporal database exists
    tgis.init()

    dbif, connection_state_changed = tgis.init_dbif(None)

    rows = tgis.get_tgis_metadata(dbif)

    if strdsin.find("@") >= 0:
        strdsid_ = strdsin
    else:
        strdsid_ = strdsin + "@" + grass.gisenv()["MAPSET"]

    if rasterin.find("@") >= 0:
        rasterid_ = rasterin
    else:
        rasterid_ = rasterin + "@" + grass.gisenv()["MAPSET"]

    datasetin = tgis.dataset_factory(type_, strdsid_)

    if not datasetin.is_in_db(dbif):
        grass.fatal(
            _("Dataset <{n}> of type <{t}> not found in temporal database").format(
                n=strdsid_, t=type_
            )
        )

    datasetin.select(dbif)

    start_time = datasetin.temporal_extent.get_start_time()
    end_time = datasetin.temporal_extent.get_end_time()

    # create a new strds using the old strds as template

    # specs of input strds
    sp = tgis.open_old_stds(strdsid_, "strds", dbif)
    ttype, stype, title, descr = sp.get_initial_values()
    dbif.close()

    # t.create, use specs of input strds
    grass.run_command('t.create', type='strds', output=strdsout,
                      temporaltype=ttype, semantictype=stype,
                      title=title, description=descr)

    # register the raster map in the new strds
    rlistfile = grass.tempfile(create=False)
    fd = open(rlistfile, "w")
    if bandname is not None:
        fd.write("%s|%s|%s|%s\n" % (rasterid_, str(start_time), str(end_time),
                                    bandname))
    else:
        fd.write("%s|%s|%s\n" % (rasterid_, str(start_time), str(end_time)))
    fd.close()
    # t.register to create new strds
    grass.run_command('t.register', input=strdsout, file=rlistfile)
    grass.try_remove(rlistfile)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
