"""modelmsh: A Python package for the generation of 2D and 3D meshes for finite element analysis.
with the following features:
    read and write mesh files in the following formats:
        cgns, gmsh, med, medit, msh, nastran, stl, vtk, vtu

- sap2000: reads SAP2000 files.
"""

__version__ = "0.1.0"

from . import gmshapp
from . import sap2000
from . import femix
from . import ofemmesh
from . import meshstruct
from .sap2000 import sap2000_handler
from .femix import femix_handler
from .ofemmesh import ofem_handler
from .msh import msh_handler
from .gmshapp import gmshApp
from .ofemlib import ofemSolver, ofemResults, ofemnlSolver
from .meshstruct import Slab, Beam
