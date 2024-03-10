import math
import os
import logging
import pathlib
from ofempy import ofemlib, sap2000, Handler, ofemmesh
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.")

# print(os.path.expanduser('~/desktop'))
# print(Path.home())

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/demo-s2k.xlsx")
lixo = ofemmesh.OfemData()
off = sap2000.Sap2000Handler(fname)
off = off.to_ofem_struct()
off.save("tests/test_5.xfem")
off.read("tests/test_5.xfem")
off.save("tests/test_3", file_format=".xlsx")
hand = Handler.to_ofempy(off, "tests/test_4.ofem")
#s2000.to_msh_and_open(entities='sections', physicals='sections')

logging.debug("Test finished.")
