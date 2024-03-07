import modelmsh as msh
import math
import os
import logging
import pathlib
from modelmsh import ofemlib
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.")

# print(os.path.expanduser('~/desktop'))
# print(Path.home())

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/s2ksamplefile.xlsx")
off = msh.Sap2000Handler(fname).to_ofem_struct()
off.save("tests/test_2.xfem")
off.save("tests/test_2", file_format=".xlsx")
#s2000.to_msh_and_open(entities='sections', physicals='sections')

logging.debug("Test finished.")
