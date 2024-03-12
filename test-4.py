import os
import logging
from ofempy import ofemsolver, Handler, ofemmesh, sap2000handler
import ofempy
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.\n")

# print(os.path.expanduser('~/desktop'))
# print(Path.home())

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/demo-s2k.s2k")

off = sap2000handler.Sap2000Handler(fname).to_ofem_struct()

logging.debug("\n\nWrting gmsh.\n")
hand = Handler.to_gmsh(off, "tests/test_6.msh", entities='sections')

logging.debug("\n\nTest finished.")
