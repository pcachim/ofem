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
logging.debug("\nSaving xfem.\n")
off.save("tests/test_6.xfem")
logging.debug("\nReading xfem.\n")
off.read("tests/test_6.xfem")
logging.debug("\nSaving xlsx.\n")
off.save("tests/test_6", file_format=".xlsx")
logging.debug("\nWrting ofem.\n")
hand = Handler.to_ofempy(off, "tests/test_6.ofem")
logging.debug("\nStart solving.\n")
test = ofemsolver.solver("tests/test_6.ofem", 'd', 1.0e-6)
#s2000.to_msh_and_open(entities='sections', physicals='sections')

logging.debug("\nTest finished.")
