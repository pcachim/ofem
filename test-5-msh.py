import os
import logging
from src.xdfem.adapters import msh
from src.xdfem import xfemmesh
from src.xdfem import common
from pathlib import Path
import pandas as pd
import gmsh, sys


fname = os.path.join( os.getcwd(), "tests/untitled.msh")

off = xfemmesh.xfemStruct.import_msh(fname)
off.save(file_format=".xlsx")
off.export_msh(fname + ".msh")
off.solve()
off.save()
off.save(file_format=".xlsx")
off.export_msh_results(fname + ".msh")

logging.debug("\n\nWrting gmsh.\n")

xfemmesh.run_gmsh(fname + ".msh")

logging.debug("\n\nTest finished.")
