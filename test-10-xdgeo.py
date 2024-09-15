import os
import logging
import src.xdfem
from pathlib import Path
import pandas as pd
import gmsh, sys

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.\n")

# print(os.path.expanduser('~/desktop'))
# print(Path.home())

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/test-xdgeo.xdgeo")

off = src.xdfem.adapters.geo.xdgeo(fname)

logging.debug("\n\nTest finished.")
