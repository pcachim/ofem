import os
import logging
from src.xdfem import libofemc, Handler, sap2000handler, common, xfemmesh
import src.xdfem
from pathlib import Path
import pandas as pd
import gmsh, sys

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.\n")

# print(os.path.expanduser('~/desktop'))
# print(Path.home())

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/demo-s2k.s2k")

off = sap2000handler.Reader(fname).to_ofem_struct()

logging.debug("\n\nWrting gmsh.\n")
hand = Handler.to_gmsh(off, "tests/test_6.msh", entities='sections')

gmsh.initialize(sys.argv)

gmsh.option.setNumber("Mesh.Lines", 1)
gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
gmsh.option.setNumber("Mesh.LineWidth", 5)
gmsh.option.setNumber("Mesh.ColorCarousel", common.gmsh_colors['physical'])

gmsh.open("tests/test_6.msh")
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()

logging.debug("\n\nTest finished.")
