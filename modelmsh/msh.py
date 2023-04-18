import meshio
import gmsh
import openpyxl
import numpy as np
from numpy.typing import NDArray
import pandas as pd
import pathlib
import sys
import logging
import timeit


physical_attributes = [
    "section",
    "group",
    "material",
    "support",
    ""
]

nnode = {
    1: 2,
    2: 3,
    3: 4,
    4: 4,
    5: 8,
    6: 6,
    7: 5,
    8: 3,
    9: 6,
    10: 9,
    11: 10,
    12: 27,
    13: 18,
    14: 14,
    15: 1,
    16: 8,
    17: 20,
    18: 10
}

def getPhysicalAttrAndValue(name: str) -> str:
    n = name.strip().find(':')
    if n == -1:
        return "", name.strip()
    attr = name[:n].lower()
    value = name[n+1:].strip()
    return attr, value


def getAttributeData():
    return


def getAllPhysical(names: list) -> NDArray:
    sec = []
    mat = []
    group = []
    fix = []
    other = {}
    for i, v in enumerate(names):
        attr, value = getPhysicalAttrAndValue(v)
        if attr == 'section' or attr == 'sec':
            attr = 'section'
        elif attr == 'material' or attr == 'mat':
            attr = 'material'
        elif attr == 'group':
            attr = 'group'
        elif attr in ['boundary', 'support', 'bound', 'sup', 'fix']:
            attr = 'fix'
        elif attr == '':
            attr = 'null'
        else:
            pass
        
        if attr in other:
            other[attr].append((i+1, value))
        else:
            other[attr] = [(i+1, value)]
    
    return other


def getBoundaries(model: gmsh.model):
    # nodes
    bounds = model.getPhysicalGroups(1)
    names = []
    bound = {}
    for b in bounds:
        name = model.getPhysicalName(b[0], b[1])
        names.append(name)
        groups = model.getEntitiesForPhysicalGroup(b[0], b[1])
        for g in groups:
            t, c, _ = model.mesh.getNodes(b[0], g, includeBoundary=True)
            c = np.array(c).reshape(len(t), 3)
            bound.update({k: v for k, v in zip(t, np.full((len(t),), name))})

    all = getAllPhysical(names)
    # lines
    # areas
    return

def getNodes(model: gmsh.model, dims: list=[1, 2, 3]) -> pd.DataFrame:
    coords = {}
    for idim in dims:
        t, c, _ = model.mesh.getNodes(idim,includeBoundary=True)
        c = np.array(c).reshape(len(t), 3)
        coords.update({k: v for k, v in zip(t, c)})
    return coords

def getElements(model: gmsh.model):
    lnods = {}
    for t in np.arange(1, 19):
        e, l = model.mesh.getElementsByType(t)
        l = np.array(l).reshape(len(e), nnode[t])
        lnods.update({k: v for k, v in zip(e, l)})
    return lnods

def getElementFrames(model: gmsh.model, types: list=[1, 8]) -> pd.DataFrame:
    lnods = {}
    for t in types:
        e, l = model.mesh.getElementsByType(t)
        l = np.array(l).reshape(len(e), nnode[t])
        lnods.update({k: v for k, v in zip(e, l)})
    return lnods

def getElementShell(model: gmsh.model, types: list=[2, 3, 9, 16, 10, 18]) -> pd.DataFrame:
    lnods = {}
    for t in types:
        e, l = model.mesh.getElementsByType(t)
        l = np.array(l).reshape(len(e), nnode[t])
        lnods.update({k: v for k, v in zip(e, l)})
    return lnods

def getElementSolid(model: gmsh.model, types: list=[4, 7, 6, 5, 11, 14, 13, 17, 12]) -> pd.DataFrame:
    lnods = {}
    for t in types:
        e, l = model.mesh.getElementsByType(t)
        l = np.array(l).reshape(len(e), nnode[t])
        lnods.update({k: v for k, v in zip(e, l)})
    return lnods


class msh_handler:
    def __init__(self):
        if not gmsh.isInitialized():
            gmsh.initialize()


    def import_s3dx(self, filename: str):
        """Import a .s3dx file and write a .msh file

        Args:
            filename (str): the .s3dx file to be imported

        Raises:
            Exception: wrong file extension
        """

        path = pathlib.Path(filename)
        if path.suffix.lower() != ".s3dx":
            raise Exception("File extension is not .s3dx")
        self._filename = str(path.parent / path.stem)

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

        gmsh.model.add(title)
        for i in range(len(elems)):
            tag = gmsh.model.addDiscreteEntity(ndims[i], -1)
            gmsh.model.mesh.addNodes(ndims[i], tag, nodes, coord)
            gmsh.model.mesh.addElements(ndims[i], tag, [types[i]], [elems[i]], [lnode[i]])

        gmsh.write(self._filename + ".msh")
        return


    def addNodeData ():
        # "ElementNodeData":
        t1 = gmsh.view.add("Continuous")
        for step in range(0, 10):
            gmsh.view.addHomogeneousModelData(
                t1, step, "simple model", "NodeData",
                [1, 2, 3, 4],  # tags of nodes
                [10., 10., 12. + step, 13. + step])  # data, per node
        return


    def addElementNodeData ():
        # "ElementNodeData":
        t2 = gmsh.view.add("Discontinuous")
        for step in range(0, 10):
            gmsh.view.addHomogeneousModelData(
                t2, step, "simple model", "ElementNodeData",
                [1, 2],  # tags of elements
                [10., 10., 12. + step, 14., 15., 13. + step])  # data per element nodes
        return


    def addElementData ():
        # "ElementNodeData":
        t2 = gmsh.view.add("Discontinuous")
        for step in range(0, 10):
            gmsh.view.addHomogeneousModelData(
                t2, step, "simple model", "ElementData",
                [1, 2],  # tags of elements
                [10., 12. + step])  # data per element nodes
        return


    def finalize(self):
        if gmsh.isInitialized():
            gmsh.finalize()
        return


if __name__ == "__main__":
    names = [
        "section: 30x50",
        "material: steel",
        "section: 60x50",
        "mat: concrete  ",
        "alibabba",
        "myprop: 2",
        "myprop: 5",
        "section: 40x50"
    ]
    o = getAllPhysical(names)
    print (f"{o=}\n")
