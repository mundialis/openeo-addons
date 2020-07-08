#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.udf
# AUTHOR(S):    Soeren Gebbert
#
# PURPOSE:      Apply a user defined function (UDF) to aggregate a time series into a single output raster map
# COPYRIGHT:    (C) 2018 - 2020 by the GRASS Development Team
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
#%description: Apply a user defined function (UDF) to aggregate a time series into a single output raster map
#%keyword: temporal
#%keyword: aggregation
#%keyword: raster
#%keyword: time
#%end

#%option G_OPT_STRDS_INPUTS
#%end

#%option G_OPT_STRDS_OUTPUT
#%end

#%option G_OPT_R_OUTPUT
#%key: basename
#%description: The basename of the output raster maps
#%end

#%option G_OPT_F_INPUT
#%key: pyfile
#%description: The Python file with user defined function to apply to the input STRDS and create an output raster map
#%end

#%option
#%key: nrows
#%type: integer
#%description: Number of rows that should be provided at once to the user defined function
#%required: no
#%multiple: no
#%answer: 1
#%end

#%option G_OPT_T_WHERE
#%end
from datetime import datetime
from pandas import DatetimeIndex
import geopandas
import pandas
import numpy
import xarray
from shapely.geometry import Polygon, Point
import json
import sys
from typing import Optional, List, Dict, Tuple
import numpy as np

from openeo_udf.api.datacube import DataCube
from openeo_udf.api.udf_data import UdfData
from openeo_udf.api.run_code import run_user_code

from grass.temporal import RasterDataset, SpaceTimeRasterDataset, SQLDatabaseInterfaceConnection, open_new_stds, register_map_object_list
import grass.temporal as tgis
import grass.script as gcore
from grass.pygrass.raster import RasterRow
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.gis.region import Region
from grass.pygrass.raster.raster_type import TYPE as RTYPE


class StrdsEntry:

    def __init__(self, dbif: SQLDatabaseInterfaceConnection, strds: SpaceTimeRasterDataset,
                 map_list: List[RasterDataset], region:Region, open_input_maps: List[RasterRow]=[],
                 start_times=[], end_times=[], mtype=None):

        self.dbif = dbif
        self.strds = strds
        self.map_list = map_list
        self.region = region
        self.open_input_maps = open_input_maps
        self.start_times = start_times
        self.end_times = end_times
        self.dt_start_times: Optional[DatetimeIndex] = None
        self.dt_end_times: Optional[DatetimeIndex] = None
        self.mtype = mtype

    def to_datacube(self, index: int, usable_rows: int) -> DataCube:

        array = np.ndarray(shape=[len(self.map_list), usable_rows,
                                  self.region.cols],
                           dtype=RTYPE[self.mtype]['numpy'])

        # We support the reading of several rows for a single udf execution
        for rmap, tindex in zip(self.open_input_maps, range(len(self.map_list))):
            for n in range(usable_rows):
                row = rmap[index + n]
                array[tindex][n][:] = row[:]

        datacube = self.create_datacube(id=self.strds.get_id(), region=self.region, array=array,
                                        usable_rows=usable_rows, index=index,
                                        start_times=self.dt_start_times, end_times=self.dt_end_times)
        return datacube

    def setup(self):
        """Open all input raster maps, generate the time vectors and return them with the map type as tuple

        :param map_list:
        :param dbif:
        :return:
        """
        print("Setup strds", self.strds.get_id())
        self.start_times = []
        self.end_times = []

        # Open all existing maps for processing
        for map in self.map_list:
            start, end = map.get_temporal_extent_as_tuple()
            self.start_times.append(start)
            self.end_times.append(end)

            rmap = RasterRow(map.get_id())
            rmap.open(mode='r')
            if self.mtype is not None:
                if self.mtype != rmap.mtype:
                    self.dbif.close()
                    gcore.fatal(_("Space time raster dataset <%s> is contains map with different type. "
                                  "This is not supported.") % input)

            self.mtype = rmap.mtype
            self.open_input_maps.append(rmap)

        self.dt_start_times = DatetimeIndex(self.start_times)
        self.dt_end_times = DatetimeIndex(self.end_times)

    @staticmethod
    def create_datacube(id: str, region: Region, array, index: int, usable_rows: int,
                        start_times: DatetimeIndex, end_times: DatetimeIndex) -> DataCube:
        """Create a data cube

        >>> array = xarray.DataArray(numpy.zeros(shape=(2, 3)), coords={'x': [1, 2], 'y': [1, 2, 3]}, dims=('x', 'y'))
        >>> array.attrs["description"] = "This is an xarray with two dimensions"
        >>> array.name = "testdata"
        >>> h = DataCube(array=array)

        :param id: The id of the strds
        :param region: The GRASS GIS Region
        :param array: The three dimensional array of data
        :param index: The current index
        :param usable_rows: The number of usable rows
        :param start_times: Start timed
        :param end_times: End tied
        :return: The udf data object
        """

        left = region.west
        top = region.north + index * region.nsres

        xcoords = []
        for col in range(region.cols):
            xcoords.append(left + col * region.ewres + region.ewres/2.0)

        ycoords = []
        for row in range(usable_rows):
            ycoords.append(top + row * region.nsres + region.nsres/2.0)

        tcoords = start_times.tolist()

        new_array = xarray.DataArray(array, dims=('t', 'y', 'x'), coords=[tcoords, ycoords, xcoords])
        new_array.name = id

        return DataCube(array=new_array)


def count_resulting_maps(input_strds: List[StrdsEntry], code: str, epsg_code: str) -> int:
    """Run the UDF code for a single raster line for each input map and count the
    resulting slices in the first raster collection tile

    :param input_strds: The dict of input strds
    :param code: The UDF code
    :param epsg_code: The EPSG code
    :return: The number of slices that were counted
    """

    # We need to count the number of slices that are returned from the udf, so we feed the first row to
    # the udf
    numberof_slices = 0

    datacubes = []
    for entry in input_strds:
        datacubes.append(entry.to_datacube(index=0, usable_rows=1))

    data = run_udf(code=code, epsg_code=epsg_code, datacube_list=datacubes)
    for slice in data.get_datacube_list()[0].array:
        numberof_slices += 1

    return numberof_slices


def run_udf(code: str, epsg_code: str, datacube_list: List[DataCube]) -> UdfData:
    """Run the user defined code (udf) and  create the required input for the function

    :param code: The UDF code
    :param epsg_code: The EPSG code of the projection
    :param datacube: The id of the strds
    :return: The resulting udf data object
    """

    data = UdfData(proj={"EPSG": epsg_code}, datacube_list=datacube_list)

    return run_user_code(code=code, data=data)


############################################################################

def main():

    # Get the options
    inputs = options["inputs"]
    output = options["output"]
    basename = options["basename"]
    where = options["where"]
    pyfile = options["pyfile"]
    nrows = int(options["nrows"])

    input_name_list = inputs.split(",")

    input_strds: List[StrdsEntry] = []

    # Import the python code into the current function context
    code = open(pyfile, "r").read()
    projection_kv = gcore.parse_command("g.proj", flags="g")
    epsg_code = projection_kv["epsg"]

    tgis.init()
    mapset = gcore.gisenv()["MAPSET"]

    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    region = Region()
    num_input_maps = 0
    open_output_maps = []

    for input_name in input_name_list:
        sp = tgis.open_old_stds(input_name, "strds", dbif)
        map_list = sp.get_registered_maps_as_objects(where=where, order="start_time", dbif=dbif)

        if not map_list:
            dbif.close()
            gcore.fatal(_("Space time raster dataset <%s> is empty") % input)

        if nrows == 0:
            dbif.close()
            gcore.fatal(_("Number of rows for the udf must be greater 0."))

        num_input_maps = len(map_list)
        input_strds.append(StrdsEntry(dbif=dbif, strds=sp, map_list=map_list, region=region))

    for strds in input_strds:
        if len(strds.map_list) != num_input_maps:
            dbif.close()
            gcore.fatal(_("The number of maps in the input STRDS must be equal"))

    # Setup the input strds to compute the output maps and the resulting strds
    mtype = None
    for strds in input_strds:
        strds.setup()
        mtype = strds.mtype

    num_output_maps = count_resulting_maps(input_strds=input_strds, code=code, epsg_code=epsg_code)

    if num_output_maps == 1:
        output_map = RasterRow(name=basename)
        output_map.open(mode="w", mtype=mtype, overwrite=gcore.overwrite())
        open_output_maps.append(output_map)
    elif num_output_maps > 1:
        for index in range(num_output_maps):
            output_map = RasterRow(name=basename + f"_{index}", mapset=mapset)
            output_map.open(mode="w", mtype=mtype, overwrite=gcore.overwrite())
            open_output_maps.append(output_map)
    else:
        dbif.close()
        gcore.fatal(_("No result generated") % input)

    # Workaround because time reduction will remove the timestamp
    result_start_times = [datetime.now()]
    first = False

    # Read several rows for each map of each input strds and load them into the udf
    for index in range(0, region.rows, nrows):
        if index + nrows > region.rows:
            usable_rows = index + nrows - region.rows + 1
        else:
            usable_rows = nrows

        # Read all input strds as cubes
        datacubes = []
        for strds in input_strds:
            datacube = strds.to_datacube(index=index, usable_rows=usable_rows)
            datacubes.append(datacube)

        # Run the UDF code
        data = run_udf(code=code, epsg_code=epsg_code, datacube_list=datacubes)

        # Read only the first cube
        datacubes = data.get_datacube_list()
        first_cube_array: xarray.DataArray = datacubes[0].get_array()

        if first is False:
            if 't' in first_cube_array.coords:
                result_start_times = first_cube_array.coords['t']

        # Three dimensions
        if first_cube_array.ndim == 3:
            for count, slice in enumerate(first_cube_array):
                output_map = open_output_maps[count]
                # print(f"Write slice at index {index} \n{slice} for map {output_map.name}")
                for row in slice:
                    # Write the result into the output raster map
                    b = Buffer(shape=(region.cols,), mtype=mtype)
                    b[:] = row[:]
                    output_map.put_row(b)
        # Two dimensions
        elif first_cube_array.ndim == 2:
            output_map = open_output_maps[0]
            # print(f"Write slice at index {index} \n{slice} for map {output_map.name}")
            for row in first_cube_array:
                # Write the result into the output raster map
                b = Buffer(shape=(region.cols,), mtype=mtype)
                b[:] = row[:]
                output_map.put_row(b)

        first = True

    # Create new STRDS
    new_sp = open_new_stds(name=output, type="strds",
                           temporaltype=input_strds[0].strds.get_temporal_type(),
                           title="new STRDS",
                           descr="New STRDS from UDF",
                           semantic="UDF",
                           overwrite=gcore.overwrite(),
                           dbif=dbif)

    maps_to_register = []
    for count, output_map in enumerate(open_output_maps):
        output_map.close()
        print(output_map.fullname())
        rd = RasterDataset(output_map.fullname())
        if input_strds[0].strds.is_time_absolute():
            if hasattr(result_start_times, "data"):
                d = pandas.to_datetime(result_start_times.data[count])
            else:
                d = result_start_times[count]
            rd.set_absolute_time(start_time=d)
        elif input_strds[0].strds.is_time_relative():
            if hasattr(result_start_times, "data"):
                d = result_start_times.data[count]
            else:
                d = result_start_times[count]
            rd.set_relative_time(start_time=d, end_time=None, unit="seconds")
        rd.load()
        if rd.is_in_db(dbif=dbif):
            rd.update(dbif=dbif)
        else:
            rd.insert(dbif=dbif)
        maps_to_register.append(rd)
        rd.print_info()

    register_map_object_list(type="raster", map_list=maps_to_register, output_stds=new_sp, dbif=dbif)

    dbif.close()


if __name__ == "__main__":
    options, flags = gcore.parser()
    main()
