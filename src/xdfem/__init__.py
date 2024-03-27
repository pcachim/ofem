"""ofempy: A Python package for the generation of 2D and 3D meshes for finite element analysis.
with the following features:
    read and write mesh files in the following formats:
        cgns, gmsh, med, medit, msh, nastran, stl, vtk, vtu

- sap2000: reads SAP2000 files.
"""

__version__ = "2024.3.2"

from . import xfemmesh
from . import ofem
from . import adapters
from .xfemmesh import xfemMesh, xfemStruct, xfemData
from . import pyfem

from .adapters import sap2000
from .adapters import msh

from .meshstruct import Slab, Beam
