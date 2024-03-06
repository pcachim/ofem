import modelmsh as msh
import math
import os
import logging
import pathlib
from modelmsh import ofemlib
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)

print(os.path.expanduser('~/desktop'))
print(Path.home())

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/test.xlsx")
s2000 = msh.Sap2000Handler(fname)
s2000.to_ofem_structure()
#s2000.to_msh_and_open(entities='sections', physicals='sections')

logging.debug("Test finished.")
