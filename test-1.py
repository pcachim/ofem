import math
import os
import logging
import pathlib
import ofempy
from ofempy import libofempy, sap2000handler, solver, results
from pathlib import Path


logging.basicConfig(level=logging.DEBUG)

print(os.path.expanduser('~/desktop'))
print(Path.home())

# Test ofem
fname = os.path.join( os.getcwd(), "tests/cyl2")
ofile = libofempy.OfemSolverFile(fname)
solver(fname, 'd', 1.0e-6)
options = {'csryn': 'n', 'ksres': 2, 'lcaco': 'c'}
codes = [libofempy.DI_CSV, libofempy.AST_CSV, libofempy.EST_CSV]
results(fname, codes, **options)


# Test ofemnl
# fname = os.path.join( os.getcwd(), "tests/cyl2")
# msh.ofemnlSolver(fname, 'd', 1.0e-6)

# fname = os.path.join( os.getcwd(), "tests/x4_t1_1.msh")
# path = pathlib.Path(fname)
# mesh = msh.mesh_handler()
# mesh.import_mesh(fname)

# fname = os.path.join(path.parent, path.stem + ".gldat")
# mesh.to_femix(fname)

# femix.read_msh(fname)

fname = os.path.join( os.getcwd(), "tests/demo.gldat")
mat = {'E': 30000000, 'nu': 0.3, 'rho': 25.0, 'alpha': 1.0e-5}
slab = ofempy.Slab()
slab.addGeometry(ofempy.meshstruct.CIRCULAR_WITH_HOLE, (0, 0, 0), 3, 1, 0.2,
                 boundary=[0, 0, 1, 1], material=mat, thick=0.25, load=-10.0)

# slab.addGeometry(msh.meshstruct.CIRCULAR_QUARTER, (0, 0, 0), 3, 0*math.pi/180, 0.2,
#                 boundary=[1, 1, 1], material=mat, thick=0.25, load=-10.0)
# slab.addGeometry(msh.meshstruct.CIRCULAR_SEGMENT, (1, 1, 0), 3, 30*math.pi/180, 70*math.pi/180, 
#                 boundary=[1, 1, 1], material=mat, thick=0.25, load=-10.0)
# slab.addGeometry(msh.meshstruct.CIRCULAR, (1, 1, 0), 3, boundary=[1, 1], material=mat, thick=0.25, load=-10.0)
# slab.addGeometry(msh.meshstruct.POLYGON, [(0, 0, 0), (10, 0, 0), (10, 5, 0), (0, 5, 0)],
#                     boundary=[1, 1, -1, 1], material=mat, thick=0.25, load=-10.0)
slab.getNodes()
slab.getElements()
slab.getBoundaries()
slab.to_ofem(fname)
slab.run()
#slab.addParameters(boundary=[1, 1, -1, 0], material=2)
# sec = {'name': 'sec', 'A': 0.5, 'I2': 0.3, 'I3': 0.3, 'It': 0.3, 'angle': 0.3}
# beam = msh.Beam()
# beam.addGeometry(msh.meshstruct.SPATIAL3D,  [(0, 0, 0), (3, 0, 0), (6, 5, 0), (9, 5, 0)], boundary=[1, 0, 0, 0, 0], material=mat, section=sec, load=-10.0)
# beam.run()

#fname = os.path.join( os.getcwd(), "tests/test.s2k")
fname = os.path.join( os.getcwd(), "tests/test.xlsx")
s2000 = ofempy.Sap2000Handler(fname)
# s2000.to_femix()
# fname = os.path.join( os.getcwd(), "test.xlsx")
# s2000.read_excel(fname, 'pandas')
s2000.to_msh_and_open(entities='sections', physicals='sections')

# s2000 = msh.sap2000_handler()
# fname = os.path.join( os.getcwd(), "tests/test.s2k")
# s2000.read_s2k(fname)
# fname = os.path.join( os.getcwd(), "tests/test-2.msh")
# s2000.write_msh(fname)

logging.debug("Test finished.")
