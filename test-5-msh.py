import os
import logging
from src.ofempy.adapters import msh
from src.ofempy import xfemmesh
from src.ofempy import common
from pathlib import Path
import pandas as pd
import gmsh, sys


fname = os.path.join( os.getcwd(), "tests/untitled.msh")

off = xfemmesh.xfemStruct.import_msh(fname)
off.save(fname + ".xlsx")
off.export_msh(fname + ".msh")
off.solve()

logging.debug("\n\nWrting gmsh.\n")

xfemmesh.run_gmsh(fname + ".msh")

logging.debug("\n\nTest finished.")
