import os
import logging
from src.xdfem.xfemmesh import xdfemStruct
import src.xdfem.xfemmesh as xfemmesh
import src.xdfem.ofem as ofem
import src.xdfem.adapters as sap2000
import shutil
from pathlib import Path
import pandas as pd
import gmsh
import src.xdfem.decorators

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.\n")

fname = os.path.join( os.getcwd(), "tests/demo-s2k.s2k")
ofile = sap2000.Reader(fname).to_ofem_struct()

xfile = "tests/test_7.xdfem"
ofile.save(xfile)

logging.debug("\nStart solving.\n")
ofile.solve()
logging.debug("\nFinish solving.\n")

ofile.save(xfile)

shutil.copyfile(xfile, xfile + ".zip")

ofile.export_msh_results(xfile)
path = Path(xfile)
filename = str(path.parent / (path.stem + "_res.msh"))
xfemmesh.run_gmsh(filename)

#s2000.to_msh_and_open(entities='sections', physicals='sections')

logging.debug("\nTest finished.")
