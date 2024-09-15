"""xdfem: A Python package for the generation of 2D and 3D meshes for finite element analysis.
"""

from . import xfemmesh
from . import ofem
from . import adapters
from . import common
from .xfemmesh import xdfemMesh, xdfemStruct, xdfemData

from .adapters import sap2000
from .adapters import msh

from .meshstruct import Slab, Beam

from .common import replace_bytesio_in_zip
