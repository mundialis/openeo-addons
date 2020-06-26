#!/usr/bin/env python3
############################################################################
#
# MODULE:       v.in.geojson
# AUTHOR(S):    Markus Metz
# PURPOSE:      Imports a geojson object.
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
#% description: Imports a geojson object.
#% keyword: vector
#% keyword: import
#%end
#%option
#% key: input
#% type: string
#% required: yes
#% multiple: no
#% key_desc: value
#% description: geojson definition
#%end
#%option G_OPT_V_OUTPUT
#% required: yes
#%end

import sys
import grass.script as grass


def main():
    geojson = options['input']
    outvect = options['output']

    tmpfile = grass.tempfile()
    fd = open(tmpfile, "w")
    fd.write("%s\n" % (geojson))
    fd.close()

    grass.run_command('v.import', input=tmpfile, output=outvect)

    grass.try_remove(tmpfile)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
