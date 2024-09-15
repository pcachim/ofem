import os
import logging
from src.xdfem.xfemmesh import xdfemStruct
import src.xdfem.ofem as ofem
import src.xdfem.adapters.sap2000 as sap2000handler
import shutil
from pathlib import Path
import pandas as pd
import gmsh

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.\n")

# print(os.path.expanduser('~/desktop'))
# print(Path.home())

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/demo-s2k.s2k")

off = sap2000handler.Reader(fname).to_xdfem_struct()
logging.debug("\nSaving xfem.\n")
off.save("tests/test_2.xdfem")

logging.debug("\nWriting ofem.\n")
hand = xdfemStruct.to_ofempy(off, "tests/test_2.ofem")

logging.debug("\nStart solving.\n")
test = ofem.solve("tests/test_2.ofem", 'd', 1.0e-6)
logging.debug("\nFinish solving.\n")
shutil.copyfile("tests/test_2.ofem", "tests/test_2.res.zip")

# gmsh.initialize()
# df = ofem.get_csv_from_ofem("tests/test_6", ofem.DI_CSV)
# disp_columns = [col for col in df.columns if col.startswith('disp-')]
# for i, col in enumerate(disp_columns):
#     for j in range(2):
#         view = gmsh.view.add(f'disp: {i+1} - case: {j+1}')
#         gmsh.view.addHomogeneousModelData(
#                 view, 0, "Model 0", "NodeData", df["point"].values, df[col].values)
#         gmsh.view.option.setNumber(view, "Visible", 0)
# gmsh.finalize()


#s2000.to_msh_and_open(entities='sections', physicals='sections')

logging.debug("\nTest finished.")
