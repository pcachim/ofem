import os
import logging
from src.ofempy.adapters import msh
from src.ofempy import xfemmesh
from src.ofempy import common
from pathlib import Path
import pandas as pd
import gmsh, sys


fname = os.path.join( os.getcwd(), "tests/untitled.msh")

# off = msh.Reader(fname)
off = xfemmesh.xfemStruct.import_msh(fname)
off.save(fname + ".xlsx")
off.export_msh(fname + ".msh")

logging.debug("\n\nWrting gmsh.\n")

gmsh.initialize(sys.argv)

gmsh.option.setNumber("Mesh.Nodes", 1)
gmsh.option.setNumber("Mesh.NodeSize", 8)
gmsh.option.setNumber("Mesh.Lines", 1)
gmsh.option.setNumber("Mesh.LineWidth", 5)
gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
gmsh.option.setNumber("Mesh.ColorCarousel", common.gmsh_colors['physical'])

gmsh.open(fname + ".msh")
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()

logging.debug("\n\nTest finished.")
