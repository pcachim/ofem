"""modelmsh: A Python package for the generation of 2D and 3D meshes for finite element analysis.
with the following features:
    read and write mesh files in the following formats:
        cgns, gmsh, med, medit, msh, nastran, stl, vtk, vtu

- sap2000: reads SAP2000 files.
"""

__version__ = "0.1.0"

from . import ofemmesh
from . import sap2000
from . import femix
from . import ofemhandler
from . import meshstruct
from . import pyfem
from . import gmshapp
from .femix import femix_handler
from .ofemhandler import ofem_handler
from .ofemlibhandler import Handler
from .sap2000 import Sap2000Handler
from .ofemgmsh import msh_handler
from .gmshapp import gmshApp
from .ofemlib import solver, results, OfemSolverFile
from .meshstruct import Slab, Beam
from .ofemstructfile import OfemStructFile