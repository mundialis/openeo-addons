"""Test t.rast.aggr_func

(C) 2017 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

:authors: Soeren Gebbert
"""
import os
import grass.temporal as tgis
from grass.gunittest.case import TestCase


class TestAggregationAbsolute(TestCase):

    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region
        """
        os.putenv("GRASS_OVERWRITE", "1")
        tgis.init()
        cls.use_temp_region()
        cls.runModule("g.region", s=0, n=80, w=0, e=120, b=0, t=50, res=10, res3=10)
        cls.runModule("r.mapcalc", expression="a1 = 100.0", overwrite=True)
        cls.runModule("r.mapcalc", expression="a2 = 200.0", overwrite=True)
        cls.runModule("r.mapcalc", expression="a3 = 300.0", overwrite=True)

        cls.runModule("t.create", type="strds", temporaltype="absolute", output="A", title="A test",
                      description="A test", overwrite=True)

        cls.runModule("t.register", flags="i", type="raster", input="A", maps="a1,a2,a3",
                      start="2001-01-01",
                      increment="2 days",
                      overwrite=True)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region
        """
        cls.del_temp_region()
        cls.runModule("t.remove", flags="rf", type="strds", inputs="A")
        cls.runModule("t.remove", flags="rf", type="strds", inputs="B")

    def test_pass_function(self):
        """Pass the input as output"""
        udf_file = open("/tmp/udf_pass_raster_collection.py", "w")
        code = """
def rct_sum(data):
    return data

        """
        udf_file.write(code)
        udf_file.close()

        self.assertModule("t.rast.udf", inputs="A,A,A", output="B",
                          basename="pass_a", pyfile="/tmp/udf_pass_raster_collection.py",
                          overwrite=True, nrows=1)

        self.assertModule("t.info", type="strds", input="B")

        self.assertModule("t.rast.list", input="B")
        self.assertRasterMinMax(map="pass_a_0", refmin=100, refmax=100,
                                msg="Minimum must be 100")

        self.assertRasterMinMax(map="pass_a_1", refmin=200, refmax=200,
                                msg="Minimum must be 200")

        self.assertRasterMinMax(map="pass_a_2", refmin=300, refmax=300,
                                msg="Minimum must be 300")


if __name__ == '__main__':
    from grass.gunittest.main import test

    test()
