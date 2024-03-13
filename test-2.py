import os
import logging
from ofempy import libofempy, Handler, ofemmesh, sap2000handler
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

off = sap2000handler.Sap2000Handler(fname).to_ofem_struct()
logging.debug("\nSaving xfem.\n")
off.save("tests/test_6.xfem")
logging.debug("\nReading xfem.\n")
off.read("tests/test_6.xfem")
logging.debug("\nSaving xlsx.\n")
off.save("tests/test_6", file_format=".xlsx")
logging.debug("\nWrting ofem.\n")
hand = Handler.to_ofempy(off, "tests/test_6.ofem")
logging.debug("\nStart solving.\n")
test = libofempy.solver("tests/test_6.ofem", 'd', 1.0e-6)
logging.debug("\nFinish solving.\n")

logging.debug("\nStart calculating results.\n")
options = {'csryn': 'n', 'ksres': 2, 'lcaco': 'l'}
# codes = [ofemlib.DI_CSV, ofemlib.AST_CSV, ofemlib.EST_CSV, ofemlib.RS_CSV]
codes = [libofempy.DI_CSV, libofempy.AST_CSV, libofempy.EST_CSV, libofempy.RS_CSV]
txt = libofempy.results("tests/test_6", codes, **options)
logging.debug("\nFinishing calculating results.\n")
shutil.copyfile("tests/test_6.ofem", "tests/test_6.res.zip")

# gmsh.initialize()
# df = libofempy.get_csv_from_ofem("tests/test_6", libofempy.DI_CSV)
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
