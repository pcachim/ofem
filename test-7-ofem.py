import os
import logging
from src.xfemmesh import xfemStruct
import src.xfemmesh as xfemmesh
import src.ofem as ofem
import src.sap2000handler as sap2000handler
import shutil
from pathlib import Path
import pandas as pd
import gmsh
import src.decorators

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.\n")

# print(os.path.expanduser('~/desktop'))
# print(Path.home())

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/demo-s2k.s2k")
ofile = sap2000handler.Reader(fname).to_ofem_struct()

xfile = "tests/test_7.xfem"

logging.debug("\nSaving xfem.\n")
ofile.save(xfile)

logging.debug("\nStart solving.\n")
ofile.solve()
logging.debug("\nFinish solving.\n")

ofile.save(xfile)

shutil.copyfile(xfile, xfile + ".zip")

ofile.to_gmsh(xfile)
path = Path(xfile)
filename = str(path.parent / (path.stem + ".msh"))
xfemmesh.run_gmsh(filename)

#s2000.to_msh_and_open(entities='sections', physicals='sections')

logging.debug("\nTest finished.")
