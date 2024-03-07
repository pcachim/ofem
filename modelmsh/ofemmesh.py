from . import common
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd
import meshio, gmsh
import sys, io, json, zipfile, re

elemtypes = list(common.ofem_meshio.keys())

@dataclass
class OfemMesh:
    title: str
    _points = pd.DataFrame(columns= ["tag", "x", "y", "z"])
    _elements = pd.DataFrame(columns= ["tag", "type", "node1", "node2"])
    # "convversion from tags to id"
    _nodetag_to_id = {}
    _elemtag_to_id = {}
    # generall medh parameters
    _num_points: int = 0
    _num_elements: int = 0

    def _set_tags_to_id(self, base: int = 1):
        self._num_points = self._points.shape[0]
        self._nodetag_to_id = dict(zip(self._points["tag"].values, np.arange(base, self._num_points+base)))
        self._num_elements = self._elements.shape[0]   
        self._elemtag_to_id = dict(zip(self._elements["tag"].values, np.arange(base, self._num_elements+base)))
        return

    def _set_points_elems_id(self, base: int = 1):
        self._set_tags_to_id(base)     
        self._points["id"] = self._points["tag"].apply(lambda x: self._nodetag_to_id[x])
        self._elements["id"] = self._elements["tag"].apply(lambda x: self._elemtag_to_id[x])
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
        self._points = dfs["points"]
        self._points["tag"] = self._points["tag"].astype(str)
        self._num_points = self._points.shape[0]

        # elements
        self._elements = dfs["elements"]
        self._elements["tag"] = self._elements["tag"].astype(str)
        self._num_elements = self._elements.shape[0]
        self.elemlist = {k: self._elements[self._elements["type"] == k]["tag"].values for k in elemtypes}  

        return
    
    def read_ofem():
        pass
    
    def read_s2k():
        pass
    
    def _to_meshio(self):
        self._set_tags_to_id(base=0)
        points = self._points[["x", "y", "z"]].values
        # points = np.array(self.points[["x", "y", "z"]])
        print(f"points:\n{points}")
        elems = []
        for k, v in self.elemlist.items():
            if v.size == 0: continue

            k_elems = self._elements[self._elements["type"] == k]
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
        listofnodes = self._points["tag"].values
        coordlist = self._points[["x", "y", "z"]].values.ravel().tolist()
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
            gmsh_elems = self._elements.loc[self._elements["type"] == elemtype]
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
        if tag in self._points["tag"].values:
            raise ValueError(f"Node with tag {tag} already exists")
        node = pd.DataFrame({"tag": [tag], "x": [x], "y": [y], "z": [z]})
        self._points = pd.concat([self._points, node], ignore_index=True)
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
        if tag in self._elements["tag"].values:
            raise ValueError(f"Element with tag {tag} already exists")
        if elemtype not in elemtypes:
            raise ValueError(f"Element type {elemtype} not recognized")
        nnodes = common.ofem_nnodes[elemtype]
        if len(nodes) != nnodes:
            raise ValueError(f"Element type {elemtype} requires {nnodes} nodes")
        node_values = self._points["tag"].values
        nodes = list(map(str, nodes))
        for node in nodes:
            if node not in node_values:
                raise ValueError(f"Node with tag {node} does not exist")

        element = pd.DataFrame({"tag": [tag], "type": [elemtype]})
        element = pd.concat([element, pd.DataFrame([nodes], columns=self._get_list_node_columns(elemtype))], axis=1)
        self._elements = pd.concat([self._elements, element], ignore_index=True)
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
        return self._points
    
    @points.setter
    def points(self, points):
        self._points = points
    
    @property
    def elements(self):
        return self._elements

    @elements.setter
    def elements(self, elements):    
        self._elements = elements


@dataclass
class OfemStruct:
    title: str
    _mesh: OfemMesh = field(init=False)
    # section types are: FRAME, SHELL, SPRING,
    _sections = pd.DataFrame(columns= ["section", "type", "material"])
    _supports = pd.DataFrame(columns= ["point", "ux", "uy", "uz", "rx", "ry", "rz"])
    # material types are: GENERAL, CONCRETE, STEEL, TIMBER, SPRIN, SOIL
    _materials = pd.DataFrame(columns= ["material", "type", "props"])
    _elemsections = pd.DataFrame(columns= ["element", "section"])

    def __post_init__(self):
        # Initialize field2 with the value of field1
        self._mesh: OfemMesh = OfemMesh(self.title)

    def read_excel(self, filename: str):
        path = Path(filename)
        if path.suffix == ".xfem":
            self.read_xfem(filename)

        dfs = pd.read_excel(filename, sheet_name=None)

        # coordinates
        if "points" in dfs:
            self.mesh._points = dfs["points"]
            self.mesh._points["tag"] = self.mesh._points["tag"].astype(str)
            self.mesh._num_points = self.mesh._points.shape[0]

        # elements
        if "elements" in dfs:
            self.mesh._elements = dfs["elements"]
            self.mesh._elements["tag"] = self.mesh._elements["tag"].astype(str)
            self.mesh._num_elements = self.mesh._elements.shape[0]
            self.mesh.elemlist = {k: self.mesh._elements[self.mesh._elements["type"] == k]["tag"].values for k in elemtypes}

        # sections
        if "sections" in dfs:
            self._sections = dfs["sections"]
            
        if "elementsections" in dfs:
            self._elemsections = dfs["elementsections"]

        # supports
        if "supports" in dfs:
            self._supports = dfs["supports"]

        # materials
        if "materials" in dfs:
            self._materials = dfs["materials"]

        return

    def write_excel(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xlsx":
            filename = path.with_suffix(".xlsx")
    
        with pd.ExcelWriter(filename) as writer:
            # Write each DataFrame to a different sheet
            self.mesh._points.to_excel(writer, sheet_name='points', index=False)
            self.mesh._elements.to_excel(writer, sheet_name='elements', index=False)
            self._sections.to_excel(writer, sheet_name='sections', index=False)
            self._elemsections.to_excel(writer, sheet_name='elementsections', index=False)
            # self._supports.to_excel(writer, sheet_name='supports', index=False)
            self._materials.to_excel(writer, sheet_name='materials', index=False)
        return

    def write_xfem(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xfem":
            filename = path.with_suffix(".xfem")

        files = self.to_dict()
        json_data = json.dumps(files, indent=2).replace('NaN', 'null')
        with open(filename+'.json', 'w') as f:
            f.write(json_data)

        # Create an in-memory buffer
        json_buffer = io.BytesIO(json_data.encode('utf-8'))
        # Reset buffer position to the beginning
        json_buffer.seek(0)
        # Create a ZIP file in-memory and add the JSON buffer
        with zipfile.ZipFile(filename, 'w') as zip_file:
                zip_file.writestr(path.stem+'.json', json_buffer.read().decode('utf-8'))        
        return
    
    def read_xfem(self, filename: str): 
        path = Path(filename)
        if path.suffix != ".xfem":
            raise ValueError(f"File {filename} is not a .xfem file")

        with zipfile.ZipFile(filename, 'r') as zip_file:
            with zip_file.open(path.stem+'.json') as json_file:
                data = json.load(json_file)
                self.from_dict(data)
        return

    def to_dict(self):
        return {
            "points": self.mesh._points.to_dict(orient="records"), 
            "elements": self.mesh._elements.to_dict(orient="records"), 
            "sections": self._sections.to_dict(orient="records"),
            "elementsections": self._elemsections.to_dict(orient="records"),
            "supports": self._supports.to_dict(orient="records"),
            "materials": self._materials.to_dict(orient="records")
        }

    def from_dict(self, data: dict):
        self.mesh._points = pd.DataFrame(data["points"])
        self.mesh._elements = pd.DataFrame(data["elements"])
        self._sections = pd.DataFrame(data["sections"])
        self._elemsections = pd.DataFrame(data["elementsections"])
        self._supports = pd.DataFrame(data["supports"])
        self._materials = pd.DataFrame(data["materials"])
        return

    @property
    def mesh(self):
        return self._mesh
    
    @mesh.setter
    def mesh(self, mesh):
        self._mesh = mesh
    
    # @property
    # def title(self):
    #     return self._title
    
    # @title.setter
    # def title(self, title):
    #     self._title = title
        
    @property
    def points(self):
        return self._mesh.points
    
    @points.setter
    def points(self, points):
        self._mesh.points = points
    
    @property
    def elements(self):
        return self._mesh.elements
    
    @elements.setter
    def elements(self, elements):
        self._mesh.elements = elements
    
    @property
    def sections(self):
        return self._sections
    
    @sections.setter
    def sections(self, sections):
        self._sections = sections
        
    @property
    def supports(self):
        return self._supports
    
    @supports.setter
    def supports(self, supports):
        self._supports = supports
    
    @property
    def materials(self):
        return self._materials
    
    @materials.setter
    def materials(self, materials):
        self._materials = materials
    
    @property
    def element_sections(self):
        return self._elemsections
    
    @element_sections.setter
    def element_sections(self, elemsections):
        self._elemsections = elemsections
    
    @property
    def node_supports(self):
        return self._nodesupports
    
    @node_supports.setter
    def node_supports(self, nodesupports):
        self._nodesupports = nodesupports
    


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
