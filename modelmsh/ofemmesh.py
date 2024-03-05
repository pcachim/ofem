import common
from dataclasses import dataclass
from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd
import meshio
import re
import gmsh
import sys

elemtypes = list(common.ofem_meshio.keys())

@dataclass
class OfemMesh:
    title: str
    points = pd.DataFrame(columns= ["tag", "x", "y", "z"])
    elements = pd.DataFrame(columns= ["tag", "type",
        "node1", "node2", "node3", "node4", "node5", "node6", "node7", "node8", "node9",
        "node10", "node11", "node12", "node13", "node14", "node15", "node16", "node17", "node18", 
        "node19", "node20", "node21", "node22", "node23", "node24", "node25", "node26", "noode27"])
    # "convversion from tags to id"
    _nodetag_to_id = {}
    _elemtag_to_id = {}
    # generall medh parameters
    _num_points: int = 0
    _num_elements: int = 0

    def _set_tags_to_id(self, base: int = 1):
        self._num_points = self.points.shape[0]
        self._nodetag_to_id = dict(zip(self.points["tag"].values, np.arange(base, self._num_points+base)))
        self._num_elements = self.elements.shape[0]   
        self._elemtag_to_id = dict(zip(self.elements["tag"].values, np.arange(base, self._num_elements+base)))
        return

    def _set_points_elems_id(self, base: int = 1):
        self._set_tags_to_id(base)     
        self.points["id"] = self.points["tag"].apply(lambda x: self._nodetag_to_id[x])
        self.elements["id"] = self.elements["tag"].apply(lambda x: self._elemtag_to_id[x])
        return 

    def _get_list_node_columns(self, elemtype: str):
        nnodes = int(re.search(r"\d+$", elemtype).group())
        nnodes = common.ofem_nnodes[elemtype]
        return [f"node{i}" for i in range(1, nnodes+1)]

    def save(self, filename: str, file_format: str = "ofem"):
        if file_format == "ofem":
            self._to_ofem(filename)
        elif file_format == "gmsh":
            self._to_gmsh(filename)
        elif file_format == "meshio":
            msh = self._to_meshio()
        elif file_format == "vtk":
            msh.write(filename, file_format="vtk", binary=False)
        else:
            raise ValueError(f"File format {file_format} not recognized")
        return

    def read_excel(self, filename: str):
        dfs = pd.read_excel(filename, sheet_name=None)
        
        # coordinates
        self.points = dfs["points"]
        self.points["tag"] = self.points["tag"].astype(str)
        self._num_points = self.points.shape[0]

        # elements
        self.elements = dfs["elements"]
        self.elements["tag"] = self.elements["tag"].astype(str)
        self._num_elements = self.elements.shape[0]
        self.elemlist = {k: self.elements[self.elements["type"] == k]["tag"].values for k in elemtypes}  

        return
    
    def read_ofem():
        pass
    
    def read_s2k():
        pass
    
    def _to_meshio(self):
        self._set_tags_to_id(base=0)
        points = self.points[["x", "y", "z"]].values
        # points = np.array(self.points[["x", "y", "z"]])
        print(f"points:\n{points}")
        elems = []
        for k, v in self.elemlist.items():
            if v.size == 0: continue

            k_elems = self.elements[self.elements["type"] == k]
            nnodes = int(re.search(r"\d+$", k).group())
            nlist = [f"node{i}" for i in range(1, nnodes+1)]
            # for col in nlist:
            #     k_elems[col] = k_elems[col].replace(to_replace=self.nodetag_to_id)
            k_elems = k_elems[nlist].replace(to_replace=self._nodetag_to_id)

            elems.append((common.ofem_meshio[k], np.array(k_elems[nlist]).astype(int).tolist()))
            print(f"elems2:\n{elems}")
            
        msh = meshio.Mesh(points,elems)
        return msh

    def _to_gmsh(self, filename: str):
        path = Path(filename)
        if path.suffix != ".msh":
            filename = path.with_suffix(".msh")
        self._set_points_elems_id(base=1)

        gmsh.initialize(sys.argv)
        gmsh.model.add(self.title)

        # Add nodes
        listofnodes = self.points["tag"].values
        coordlist = self.points[["x", "y", "z"]].values.ravel().tolist()
        entity = gmsh.model.addDiscreteEntity(0)
        gmsh.model.mesh.addNodes(0, entity, listofnodes, coordlist)

        # Add elements
        for elemtype in elemtypes:
            if self.elemlist[elemtype].size == 0:  continue

            gmsh_dim = common.ofem_gmsh_dim[elemtype]
            entity = gmsh.model.addDiscreteEntity(gmsh_dim)
            gmsh.model.setEntityName(gmsh_dim, entity, elemtype)
            gmsh_type = common.ofem_gmsh[elemtype]

            # select elements of type elemtype
            gmsh_elems = self.elements.loc[self.elements["type"] == elemtype]
            # create a list with the numbers of elements
            elems_list = np.array(gmsh_elems["id"]).astype(int).tolist()

            nlist = self._get_list_node_columns(elemtype)
            # create a list with the numbers of nodes of selected elements
            elems_nodes = gmsh_elems[nlist].astype(int).values.ravel().tolist()
            gmsh.model.mesh.addElementsByType(entity, gmsh_type, elems_list, elems_nodes)

        gmsh.write(filename)
        gmsh.finalize()
        return
    
    def add_node(self, tag: Union[int, str], x: float, y: float, z: float):
        tag = str(tag)
        if tag in self.points["tag"].values:
            raise ValueError(f"Node with tag {tag} already exists")
        node = pd.DataFrame({"tag": [tag], "x": [x], "y": [y], "z": [z]})
        self.points = pd.concat([self.points, node], ignore_index=True)
        return
    
    def add_nodes(self, tags: list, points: list):
        tags = list(map(str, tags))
        if len(tags) != len(points):
            raise ValueError(f"Number of tags and number of coordinates must be the same")
        for tag, coord in zip(tags, points):
            self.add_node(tag, *coord)
        return

    def add_element(self, tag: Union[int, str], elemtype: str, nodes: list):
        tag = str(tag)
        if tag in self.elements["tag"].values:
            raise ValueError(f"Element with tag {tag} already exists")
        if elemtype not in elemtypes:
            raise ValueError(f"Element type {elemtype} not recognized")
        nnodes = common.ofem_nnodes[elemtype]
        if len(nodes) != nnodes:
            raise ValueError(f"Element type {elemtype} requires {nnodes} nodes")
        node_values = self.points["tag"].values
        nodes = list(map(str, nodes))
        for node in nodes:
            if node not in node_values:
                raise ValueError(f"Node with tag {node} does not exist")

        element = pd.DataFrame({"tag": [tag], "type": [elemtype]})
        element = pd.concat([element, pd.DataFrame([nodes], columns=self._get_list_node_columns(elemtype))], axis=1)
        self.elements = pd.concat([self.elements, element], ignore_index=True)
        return

    def add_elements_by_type(self, elemtype: str, tags: list, nodes: list):
        tags = list(map(str, tags))
        if elemtype not in elemtypes:
            raise ValueError(f"Element type {elemtype} not recognized")
        nnodes = common.ofem_nnodes[elemtype]
        if len(tags) != len(nodes):
            raise ValueError(f"Number of tags and number of nodes must be the same")
        for tag, node in zip(tags, nodes):
            self.add_element(tag, elemtype, node)
        return

    @property
    def num_elements(self):
        return self._num_elements
    
    @property
    def num_points(self):
        return self._num_points
    
    @property
    def points(self):
        return self.points
    
    @property
    def elements(self):
        return self.elements


@dataclass
class OfemStructure:
    title: str
    mesh: OfemMesh = OfemMesh(title)
    # section types are: FRAME, SHELL, SPRING,
    _sections = pd.DataFrame(columns= ["name", "type", "material"])
    _supports = pd.DataFrame(columns= ["tag", "type", "props"])
    # material types are: GENERAL, CONCRETE, STEEL, TIMBER, SPRIN, SOIL
    _materials = pd.DataFrame(columns= ["name", "type", "props"])
    _elemsections = pd.DataFrame(columns= ["element", "section"])
    _nodesupports = pd.DataFrame(columns= ["node", "support"])

    def read_excel(self, filename: str):
        dfs = pd.read_excel(filename, sheet_name=None)

        # coordinates
        if "points" in dfs:
            self.mesh.points = dfs["points"]
            self.mesh.points["tag"] = self.mesh.points["tag"].astype(str)
            self.mesh._num_points = self.mesh.points.shape[0]

        # elements
        if "elements" in dfs:
            self.mesh.elements = dfs["elements"]
            self.mesh.elements["tag"] = self.mesh.elements["tag"].astype(str)
            self.mesh._num_elements = self.mesh.elements.shape[0]
            self.mesh.elemlist = {k: self.mesh.elements[self.mesh.elements["type"] == k]["tag"].values for k in elemtypes}

        # sections
        if "sections" in dfs:
            self._sections = dfs["sections"]
            
        if "elementsections" in dfs:
            self._elemsections = dfs["elementsections"]

        if "framesections" in dfs:
            self._framesections = dfs["framesections"]
            
        if "shellsections" in dfs:
            self._shellsections = dfs["shellsections"]

        if "springsections" in dfs:
            self._springsections = dfs["springsections"]

        # supports
        if "supports" in dfs:
            self._supports = dfs["supports"]

        # materials
        if "materials" in dfs:
            self._materials = dfs["materials"]

        return


if __name__ == "__main__":
    msh = OfemMesh("Demo mesh")
    msh.read_excel("demofile.xlsx")
    msh.add_node("100", 1.0, 2.0, 3.0)
    msh.add_element("100", "area3", [4, 6, 5])
    mshgmsh = msh._to_gmsh("lixo.msh")

    newmesh = msh._to_meshio()
    newmesh.write("lixo.vtk", file_format="vtk42", binary=False)
    #newmesh.write("lixo.msh", file_format="gmsh", binary=False)
    # kmesh = meshio.read("lixo.vtk")
    print(msh._num_points, msh._num_elements)
