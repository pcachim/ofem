import math
import os
import logging
import pathlib
import ofempy
from ofempy import sap2000handler
from ofempy import ofem
from pathlib import Path

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/test.xlsx")
s2000 = ofempy.Reader(fname)
# s2000.to_femix()
# fname = os.path.join( os.getcwd(), "test.xlsx")
# s2000.read_excel(fname, 'pandas')
s2000.to_msh_and_open(entities='sections', physicals='sections')

# s2000 = msh.sap2000_handler()
# fname = os.path.join( os.getcwd(), "tests/test.s2k")
# s2000.read_s2k(fname)
# fname = os.path.join( os.getcwd(), "tests/test-2.msh")
# s2000.write_msh(fname)

logging.debug("Test finished.")
