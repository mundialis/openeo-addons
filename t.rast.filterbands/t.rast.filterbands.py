#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.filterbands
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Extract selected bands from a given STRDS
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
#% description: Extract selected bands from a given STRDS.
#% keyword: temporal
#% keyword: algebra
#% keyword: raster
#% keyword: time
#%end

#%option G_OPT_STRDS_INPUT
#%end

#%option G_OPT_T_SAMPLE
#% key: method
#% answer: equal
#%end

#%option G_OPT_STRDS_OUTPUT
#%end

#%option
#% key: bands
#% type: string
#% label: Bands to extract
#% description: Bands can be real or common band names
#% multiple: yes
#% required: no
#%end

#%option
#% key: wavelengths
#% type: double
#% label: Wavelengths to extract in micrometers
#% description: Wavelengths are defined by min, max
#% multiple: yes
#% key_desc: min,max
#% required: no
#%end

#%option
#% key: nprocs
#% type: integer
#% description: Number of r.mapcalc processes to run in parallel
#% required: no
#% multiple: no
#% answer: 1
#%end


import grass.script as grass


def main():

    # Get the options
    _input = options["input"]
    output = options["output"]
    bandsin = options["bands"]
    wavelengths = options["wavelengths"]
    nprocs = int(options["nprocs"])

    bandssel = list()
    if bandsin:
        bandsin = bandsin.split(',')
        for bandname in bandsin:
            if bandname in common_names:
                bandname = common_names[bandname]
            bandssel.append("'" + bandname + "'")

    if wavelengths:
        # get the first entry of the output of t.rast.list columns=band_reference
        br_raw = grass.read_command('t.rast.list', input=_input, columns="band_reference", flags='u')

        # get the sensor appreviation split by _
        sensor_abbr = None
        for line in br_raw.splitlines():
            sensor_abbr = line.split('_')[0]
            # TODO: check if sensor abbreviation changes
            break

        if sensor_abbr is None:
            grass.fatal("Sensor abbreviation is not available")
        if sensor_abbr not in ("L5", "L7", "L8", "S2"):
            grass.fatal("Unknown sensor abbreviation <%s>" % sensor_abbr)

        # hard-coded for now, as long as there are no STAC-like common names
        # in the output of g.bands

        # from https://github.com/radiantearth/stac-spec/tree/master/extensions/eo#common-band-names

        common_names = dict()
        if sensor_abbr == "L5":
            common_names["blue"] = "L5_1"
            common_names["green"] = "L5_2"
            common_names["red"] = "L5_3"
            common_names["nir"] = "L5_4"
            common_names["swir16"] = "L5_5"
            common_names["swir22"] = "L5_7"
            common_names["lwir"] = "L5_6"
        elif sensor_abbr == "L7":
            common_names["blue"] = "L7_1"
            common_names["green"] = "L7_2"
            common_names["red"] = "L7_3"
            common_names["nir"] = "L7_4"
            common_names["swir16"] = "L7_5"
            common_names["swir22"] = "L7_7"
            common_names["lwir"] = "L7_6"
            common_names["pan"] = "L7_8"
        elif sensor_abbr == "L8":
            common_names["coastal"] = "L8_1"
            common_names["blue"] = "L8_2"
            common_names["green"] = "L8_3"
            common_names["red"] = "L8_4"
            common_names["nir08"] = "L8_5"
            common_names["swir16"] = "L8_6"
            common_names["swir22"] = "L8_7"
            common_names["pan"] = "L8_8"
            common_names["cirrus"] = "L8_9"
            common_names["lwir11"] = "L8_10"
            common_names["lwir12"] = "L8_11"
        elif sensor_abbr == "S2":
            common_names["coastal"] = "S2_1"
            common_names["blue"] = "S2_2"
            common_names["green"] = "S2_3"
            common_names["red"] = "S2_4"
            common_names["nir"] = "S2_8"
            common_names["nir08"] = "S2_8A"
            common_names["nir09"] = "S2_9"
            common_names["cirrus"] = "S2_10"
            common_names["swir16"] = "S2_11"
            common_names["swir22"] = "S2_12"

        wavecenter = dict()
        if sensor_abbr == "L5":
            wavecenter["L5_1"] = 0.48
            wavecenter["L5_2"] = 0.56
            wavecenter["L5_3"] = 0.66
            wavecenter["L5_4"] = 0.83
            wavecenter["L5_5"] = 1.65
            wavecenter["L5_6"] = 11.45
            wavecenter["L5_7"] = 2.21
        elif sensor_abbr == "L7":
            wavecenter["L7_1"] = 0.48
            wavecenter["L7_2"] = 0.56
            wavecenter["L7_3"] = 0.66
            wavecenter["L7_4"] = 0.83
            wavecenter["L7_5"] = 1.65
            wavecenter["L7_6"] = 11.45
            wavecenter["L7_7"] = 2.22
            wavecenter["L7_8"] = 0.6
        elif sensor_abbr == "L8":
            wavecenter["L8_1"] = 0.44
            wavecenter["L8_2"] = 0.48
            wavecenter["L8_3"] = 0.56
            wavecenter["L8_4"] = 0.66
            wavecenter["L8_5"] = 0.87
            wavecenter["L8_6"] = 1.61
            wavecenter["L8_7"] = 2.20
            wavecenter["L8_8"] = 0.59
            wavecenter["L8_9"] = 1.37
            wavecenter["L8_10"] = 10.9
            wavecenter["L8_11"] = 12
        elif sensor_abbr == "S2":
            wavecenter["S2_1"] = 0.44
            wavecenter["S2_2"] = 0.49
            wavecenter["S2_3"] = 0.56
            wavecenter["S2_4"] = 0.66
            wavecenter["S2_5"] = 0.70
            wavecenter["S2_6"] = 0.74
            wavecenter["S2_7"] = 0.78
            wavecenter["S2_8"] = 0.83
            wavecenter["S2_8A"] = 0.86
            wavecenter["S2_9"] = 0.94
            wavecenter["S2_10"] = 1.37
            wavecenter["S2_11"] = 1.61
            wavecenter["S2_12"] = 2.2

        wavelengths = wavelengths.split(',')
        # not very elegant
        i = 0
        while i < len(wavelengths):
            wmin = float(wavelengths[i])
            wmax = float(wavelengths[i + 1])
            for bandname in wavecenter.keys():
                if wavecenter[bandname] >= wmin and \
                   wavecenter[bandname] <= wmax:
                    bandssel.append("'" + bandname + "'")
                    break
            i += 2

    wherestr = ("band_reference in (%s)") % (", ".join(bandssel))
    grass.message("selecting bands %s" % (", ".join(bandssel)))

    grass.run_command('t.rast.extract', input=_input, where=wherestr,
                      output=output, nprocs=nprocs)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
