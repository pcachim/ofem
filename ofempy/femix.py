import meshio
import gmsh
import openpyxl
import numpy as np
import pandas as pd
import pathlib
import sys
import logging
import timeit
from . import ofemlib


def gmsh2femix(code: int, lnods: list):
    ln = []
    if code == 1: 
        return 7, 2, lnods
    if code == 2: 
        return 9, 3, lnods
    if code == 3: 
        return 6, 4, lnods
    if code == 5: 
        return 4, 8, lnods
    if code == 8: 
        return 7, 2, lnods
    if code == 8: 
        ln[0] = lnods[0]
        ln[1] = lnods[3]
        ln[2] = lnods[1]
        ln[3] = lnods[4]
        ln[4] = lnods[2]
        ln[5] = lnods[5]
        return 7, 2, ln
    if code == 10: 
        ln[0] = lnods[0]
        ln[1] = lnods[4]
        ln[2] = lnods[1]
        ln[3] = lnods[5]
        ln[4] = lnods[2]
        ln[5] = lnods[6]
        ln[6] = lnods[3]
        ln[7] = lnods[7]
        ln[8] = lnods[8]
        return 6, 9, lnods
    if code == 12: 
        return 4, 27, lnods
    if code == 16: 
        ln[0] = lnods[0]
        ln[1] = lnods[4]
        ln[2] = lnods[1]
        ln[3] = lnods[5]
        ln[4] = lnods[2]
        ln[5] = lnods[6]
        ln[6] = lnods[3]
        ln[7] = lnods[7]
        return 6, 8, lnods
    if code == 17: 
        return 4, 20, lnods


def femix2gmsh(code: int, nnode: int, lnods: list):
    ln = []
    if code == 1 or code == 2 or code == 3 or code == 5 or code == 6 or code == 9 or code == 10:
        if nnode == 3: 
            return 2, 2, lnods
        if nnode == 4: 
            return 3, 2, lnods
        if nnode == 6: 
            ln[0] = lnods[0]
            ln[1] = lnods[2]
            ln[2] = lnods[4]
            ln[3] = lnods[1]
            ln[4] = lnods[3]
            ln[5] = lnods[5]
            return 9, 2, ln
        if nnode == 8:
            ln[0] = lnods[0]
            ln[1] = lnods[2]
            ln[2] = lnods[4]
            ln[3] = lnods[6]
            ln[4] = lnods[1]
            ln[5] = lnods[3]
            ln[6] = lnods[5]
            ln[7] = lnods[7]
            return 16, 2, ln
        if nnode == 9: 
            ln[0] = lnods[0]
            ln[1] = lnods[2]
            ln[2] = lnods[4]
            ln[3] = lnods[6]
            ln[4] = lnods[1]
            ln[5] = lnods[3]
            ln[6] = lnods[5]
            ln[7] = lnods[7]
            ln[8] = lnods[8]
            return 10, 2, ln
    elif code == 4:
        if nnode == 8: return 5, 3, lnods
        if nnode == 20: 
            return 17, 3, lnods
        if nnode == 27: 
            return 12, 3, lnods
    elif code == 7 or code == 8 or code == 13 or code == 14 or code == 15 or code == 16:
        if nnode == 2: return 1, 1, lnods
        if nnode == 3: 
            ln[0] = lnods[0]
            ln[1] = lnods[2]
            ln[2] = lnods[1]
            return 8, 1, ln
    else:
        return 15, 0 # POINT


LINE_INTERFACE = 11
PLANE_INTERFACE = 12

PYRAMID5 = 6
PYRAMID13 = 18


class femix_handler:
    
    def __init__(self):
        self.mesh = {}  # SAP2000 S2K file database


    def read_pva(self, filename: str):
        with open(filename, 'r') as f:
            nodes = []
            values = []
            for line in f:
                x, y = line.strip().split()
                nodes.append(float(x))
                values.append([float(y)])

        return nodes, values


    def read_s3dx(self, filename: str):
        with open(filename, 'r') as f:
            title = f.readline()

            while True:
                try:
                    title = f.readline()
                    if title.strip() == "": break
                except:
                    break

                nelems, nnodes, nspec = f.readline().strip().split()

                elems = []
                types = []
                lnode = []
                ndims = []
                for i in range(int(nelems)):
                    lin = f.readline().strip().split()
                    # n, ty, nn, ln = f.readline().strip().split()
                    n  = int(lin[0])
                    ty = int(lin[1])
                    nn = int(lin[2])
                    ln = lin[-nn:]
                    code, ndim, ln = femix2gmsh(ty, nn, ln)
                    if code not in types:
                        types.append(code)
                        elems.append([n])
                        lnode.append(ln)
                        ndims.append(int(ndim))
                    else:
                        index = types.index(code)
                        lnode[index].extend(ln)
                        elems[index].append(n)

                nodes = []
                coord = []
                for i in range(int(nnodes)):
                    lin = f.readline().strip().split()
                    nodes.append(int(lin[0]))
                    coord.extend([float(lin[1]), float(lin[2]), float(lin[3])])

                specs = []
                for i in range(int(nspec)):
                    lin = f.readline().strip().split()
                    specs.append(int(lin[1]))

        gmsh.initialize()

        gmsh.model.add(title)
        for i in range(len(elems)):
            tag = gmsh.model.addDiscreteEntity(ndims[i], -1)
            gmsh.model.mesh.addNodes(ndims[i], tag, nodes, coord)
            gmsh.model.mesh.addElements(ndims[i], tag, [types[i]], [elems[i]], [lnode[i]])

        # tag = gmsh.model.addDiscreteEntity(0, -1)
        # gmsh.model.mesh.addNodes(0, tag, nodes, coord)
        # gmsh.model.mesh.addElements(0, tag, [15], [[i for i in range(1, int(nspec)+1)]], [specs])

        gmsh.write(filename + ".msh")
        gmsh.finalize()
        return ndims, types, elems, lnode, nodes, coord, specs


    def read_msh(self, filename: str):
        gmsh.initialize()
        gmsh.open(filename)
        mesh = meshio.read(filename)

        # 1) store the mesh
        m = {}
        for e in gmsh.model.getEntities():
            m[e] = (gmsh.model.getBoundary([e]),
                    gmsh.model.mesh.getNodes(e[0], e[1]),
                    gmsh.model.mesh.getElements(e[0], e[1]))

        # 2) create a new model
        gmsh.model.add('model2')

        # 3) create discrete entities in the new model and copy the mesh
        for e in sorted(m):
            gmsh.model.addDiscreteEntity(e[0], e[1], [b[1] for b in m[e][0]])
            gmsh.model.mesh.addNodes(e[0], e[1], m[e][1][0], m[e][1][1])
            gmsh.model.mesh.addElements(e[0], e[1], m[e][2][0], m[e][2][1], m[e][2][2])

        # Launch the GUI to see the results:
        if '-nopopup' not in sys.argv:
            gmsh.fltk.run()


        gmsh.finalize()


    def runnl(self, filename: str): 
        #filename = os.path.join(os.getcwd(), 'scripts/tri')
        if filename.endswith(".gldat"):
            filename = filename[:len(filename) - 6]
        ofemlib.ofemnlSolver(filename, 'd', 1.0e-6)


    def run(self, filename: str): 
        #filename = os.path.join(os.getcwd(), 'scripts/tri')
        if filename.endswith(".gldat"):
            filename = filename[:len(filename) - 6]
        ofemlib.solver(filename, 'd', 1.0e-6)


    def posprocess(self, filename: str, options: list):
        if filename.endswith(".gldat"):
            filename = filename[:len(filename) - 6]
        for option in options:
            #option = {'lcaco': 'l', 'cstyn': 'y', 'stnod': 'a', 'csryn': 'n', 'ksres': 1}
            ofemlib.results(filename, **option)
            # femixlib.posfemix(filename, option, lcaco='l', cstyn='y', stnod='a', csryn='n', ksres=1)
        return


    def rungmsh(self, filename: str):
        gmsh.initialize()

        # Copied from discrete.py...
        gmsh.model.add("test")
        gmsh.model.addDiscreteEntity(2, 1)
        gmsh.model.mesh.addNodes(2, 1, [1, 2, 3, 4],
                                [0., 0., 0., 1., 0., 0., 1., 1., 0., 0., 1., 0.])
        gmsh.model.mesh.addElements(2, 1, [2], [[1, 2]], [[1, 2, 3, 1, 3, 4]])
        # ... end of copy

        # Create a new post-processing view
        t = gmsh.view.add("some data")

        # add 10 steps of model-based data, on the nodes of the mesh
        # for step in range(0, 10):
        #     gmsh.view.addModelData(
        #         t,
        #         step,
        #         "test",
        #         "NodeData",
        #         nodes,  # tags of nodes
        #         values)  # data, per node

        gmsh.view.write(t, "data.msh")

        gmsh.finalize()
