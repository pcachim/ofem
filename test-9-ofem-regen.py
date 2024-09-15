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

fname = os.path.join( os.getcwd(), "tests/building-s2k.s2k")
ofile = sap2000.Reader(fname).to_xdfem_struct()
gfile = ofile.export_msh("tests/building-s2k.msh", model="geometry", entities="elements")
ofile = xfemmesh.xdfemStruct.import_msh("tests/building-s2k.msh")

xfile = "tests/building-refined.xdfem"
ofile.save(xfile)

logging.debug("\nStart solving.\n")
ofile.solve()
logging.debug("\nFinish solving.\n")

shutil.copyfile(xfile, xfile + ".zip")

ofile.export_msh_results(xfile, stresses_avg=True, stresses_eln=True)
path = Path(xfile)
filename = str(path.parent / (path.stem + ".res.msh"))
xfemmesh.run_gmsh(filename)

#s2000.to_msh_and_open(entities='sections', physicals='sections')

logging.debug("\nTest finished.")
