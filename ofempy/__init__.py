"""modelmsh: A Python package for the generation of 2D and 3D meshes for finite element analysis.
with the following features:
    read and write mesh files in the following formats:
        cgns, gmsh, med, medit, msh, nastran, stl, vtk, vtu

- sap2000: reads SAP2000 files.
"""

__version__ = "0.1.0"

from . import xfemmesh
from . import ofem
from . import sap2000handler
from .xfemmesh import xfemMesh, xfemStruct, xfemData
# from .pyfiles import femixhandler
# from . import meshstruct
from . import pyfem
from . import gmshapp
# from .femixhandler import femix_handler

from . import sap2000handler
from .sap2000handler import Reader

from .gmshhandler import GmshHandler
from .gmshapp import gmshApp
from .meshstruct import Slab, Beam
# from .ofemstructfile import OfemStructFile
