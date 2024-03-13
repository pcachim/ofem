from . import common
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd
import meshio, gmsh
import sys, os, io, json, zipfile, re

# pd.options.mode.copy_on_write = True
elemtypes = list(common.ofem_meshio.keys())

NTABLES = 10

SECTIONS = 0
SUPPORTS = 1
MATERIALS = 2
ELEMSECTIONS = 3
POINTLOADS = 4
LINELOADS = 5
AREALOADS = 6
SOLIDLOADS = 7
LOADCASES = 8
LOADCOMBINATIONS = 9

def replace_bytesio_in_zip(zip_path, target_filename, new_contents):
    # Create a temporary filename for the new ZIP file
    temp_zip_path = zip_path + ".temp"

    # Open the existing ZIP file in read mode
    with zipfile.ZipFile(zip_path, 'r') as existing_zip:
        # Open the new ZIP file in write mode
        with zipfile.ZipFile(temp_zip_path, 'w') as new_zip:
            # Iterate through the existing files
            for item in existing_zip.infolist():
                # Skip the target file
                if item.filename != target_filename:
                    # Copy the existing file to the new ZIP file
                    data = existing_zip.read(item.filename)
                    new_zip.writestr(item, data)

            # Add the new file to the ZIP file
            new_zip.writestr(target_filename, new_contents)

    # Replace the original ZIP file with the temporary one
    os.replace(temp_zip_path, zip_path)


class OfemMesh:
    
    def __init__(self, title: str):
        self.title = title
        self._dirtypoints: bool = False
        self._dirtyelements: bool = False
        self._points = pd.DataFrame(columns= ["point", "x", "y", "z"])
        self._elements = pd.DataFrame(columns= ["element", "type", "node1", "node2"])
        # "convversion from tags to id"
        self._nodetag_to_id = {}
        self._elemtag_to_id = {}
        return
    
    def _set_tags_to_id(self, base: int = 1):
        self._nodetag_to_id = dict(zip(self._points["point"].values, np.arange(base, self.num_points+base)))
        self._elemtag_to_id = dict(zip(self._elements["element"].values, np.arange(base, self.num_elements+base)))
        return

    def set_points_elems_id(self, base: int = 1):
        self._set_tags_to_id(base)     
        self._points["id"] = self._points["point"].apply(lambda x: self._nodetag_to_id[x])
        self._elements["id"] = self._elements["element"].apply(lambda x: self._elemtag_to_id[x])
        self._dirtypoints = False
        self._dirtyelements = False
        return 

    def get_list_node_columns(self, elemtype: str):
        nnodes = int(re.search(r"\d+$", elemtype).group())
        nnodes = common.ofem_nnodes[elemtype]
        return [f"node{i}" for i in range(1, nnodes+1)]

    def set_indexes(self):
        # if self._dirtyelements:
        self._elements['ielement'] = self._elements['element'].copy()
        self._elements.set_index('ielement', inplace=True)
        self._dirtyelements = False
        # if self._dirtypoints:
        ipoint = self._points['point'].copy()
        self._points.set_index(ipoint, inplace=True)
        self._dirtypoints = False

    def save(self, filename: str, file_format: str = "xfem"):
        if file_format == "xfem":
            self._to_ofem(filename)
        elif file_format == "gmsh":
            self.write_gmsh(filename)
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
        self._points["point"] = self._points["point"].astype(str)

        # elements
        self._elements = dfs["elements"]
        self._elements["element"] = self._elements["element"].astype(str)
        self.elemlist = {k: self._elements[self._elements["type"] == k]["element"].values for k in elemtypes}  

        self._dirtypoints = True
        self._dirtyelements = True
        return

    def read_xfem(self, filename: str): 
        path = Path(filename)
        if path.suffix != ".xfem":
            raise ValueError(f"File {filename} is not a .xfem file")

        with zipfile.ZipFile(filename, 'r') as zip_file:
            with zip_file.open('mesh.json') as json_file:
                data = json.load(json_file)
                self.from_dict(data)

        self._dirtypoints = True
        self._dirtyelements = True
        return

    def read(self, filename: str, file_format: str = None):
        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xlsx":
            self.read_excel(filename)
        elif file_format == ".xfem":
            self.read_xfem(filename)
        else:
            raise ValueError(f"File format {file_format} not recognized")
        return

    def to_dict(self):
        return {
            "points": self._points.to_dict(orient="records"), 
            "elements": self._elements.to_dict(orient="records"), 
        }

    def from_dict(self, ofem_dict: dict):
        json_buffer = io.BytesIO(json.dumps(ofem_dict["points"]).encode())
        json_buffer.seek(0)
        self._points = pd.read_json(json_buffer, orient='records')
        self._dirtypoints = True
        json_buffer = io.BytesIO(json.dumps(ofem_dict["elements"]).encode())
        json_buffer.seek(0)
        self._elements = pd.read_json(json_buffer, orient='records')
        self._dirtyelements = True
        return

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

    def write_xfem(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xfem":
            filename = path.with_suffix(".xfem")

        files = self.to_dict()
        json_data = json.dumps(files, indent=2).replace('NaN', 'null')

        json_buffer = io.BytesIO(json_data.encode('utf-8'))
        json_buffer.seek(0)
        
        if path.exists():
            replace_bytesio_in_zip(filename, 'mesh.json', json_buffer.read().decode('utf-8'))   
        else:
            with zipfile.ZipFile(filename, 'w') as zip_file:
                zip_file.writestr('mesh.json', json_buffer.read().decode('utf-8')) 

        return

    def write_gmsh(self, filename: str):
        path = Path(filename)
        if path.suffix != ".msh":
            filename = path.with_suffix(".msh")
        self.set_points_elems_id(base=1)

        gmsh.initialize(sys.argv)
        gmsh.model.add(self.title)

        # Add nodes
        listofnodes = self._points["point"].values
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

            nlist = self.get_list_node_columns(elemtype)
            # create a list with the numbers of nodes of selected elements
            elems_nodes = gmsh_elems[nlist].astype(int).values.ravel().tolist()
            gmsh.model.mesh.addElementsByType(entity, gmsh_type, elems_list, elems_nodes)

        gmsh.write(filename)
        gmsh.finalize()
        return
    
    def add_node(self, tag: Union[int, str], x: float, y: float, z: float):
        tag = str(tag)
        if tag in self._points["point"].values:
            raise ValueError(f"Node with tag {tag} already exists")
        node = pd.DataFrame({"point": [tag], "x": [x], "y": [y], "z": [z]})
        self._points = pd.concat([self._points, node], ignore_index=True)
        self._dirtypoints = True
        return

    def add_nodes(self, tags: list, points: list):
        tags = list(map(str, tags))
        if len(tags) != len(points):
            raise ValueError(f"Number of tags and number of coordinates must be the same")
        for tag, coord in zip(tags, points):
            self.add_node(tag, *coord)
        self._dirtypoints = True
        return

    def add_element(self, tag: Union[int, str], elemtype: str, nodes: list):
        tag = str(tag)
        if tag in self._elements["element"].values:
            raise ValueError(f"Element with tag {tag} already exists")
        if elemtype not in elemtypes:
            raise ValueError(f"Element type {elemtype} not recognized")
        nnodes = common.ofem_nnodes[elemtype]
        if len(nodes) != nnodes:
            raise ValueError(f"Element type {elemtype} requires {nnodes} nodes")
        node_values = self._points["point"].values
        nodes = list(map(str, nodes))
        for node in nodes:
            if node not in node_values:
                raise ValueError(f"Node with tag {node} does not exist")

        element = pd.DataFrame({"element": [tag], "type": [elemtype]})
        element = pd.concat([element, pd.DataFrame([nodes], columns=self.get_list_node_columns(elemtype))], axis=1)
        self._elements = pd.concat([self._elements, element], ignore_index=True)
        self._dirtyelements = True
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
        self._dirtyelements = True
        return

    @property
    def dirty(self):
        return self._dirtypoints and self._dirtyelements
    @property
    def num_elements(self):
        return self._elements.shape[0]
    
    @property
    def num_points(self):
        return self._points.shape[0]

    @property
    def points(self):
        if self._dirtypoints:
            self.set_indexes()
        return self._points
    
    @points.setter
    def points(self, points):
        self._points = points
        self._dirtypoints = True
        return
    
    @property
    def elements(self):
        if self._dirtyelements: 
            self.set_indexes()
        return self._elements

    @elements.setter
    def elements(self, elements):    
        self._elements = elements
        self._dirtyelements = True
        return

    def get_normals(self, convention: str = "") -> dict:
        """
            convention (str, optional): Defaults to "ofempy". 
            can be "ofempy", "sap2000" or "femix".
        """
        convention = convention.lower()
        if convention == "femix":
            return self.get_normals_femix()
        # elif convention == "sap2000" or convention == "ofempy":
        else:
            return self.get_normals_sap2000()

    def get_normals_sap2000(self):
        if self._dirty:
            self.set_indexes()
        normals = {}
        for elem in self._elements.itertuples():
            if str(elem.type).startswith("line"):
                node1 = self._points.loc[elem.node1]
                node2 = self._points.loc[elem.node2]
                v1 = np.array([node2.x - node1.x, node2.y - node1.y, node2.z - node1.z])
                v1 = v1/np.linalg.norm(v1)
                v3 = np.cross(v1, [0, 0, 1])
                n3 = np.linalg.norm(v3)
                v3 = [0, np.sign(v1[2]), 0] if abs(n3) < 1.0e-10 else v3/n3
                v2 = np.cross(v3, v1)
            elif str(elem.type).startswith("area"):
                node1 = self._points.loc[elem.node1]
                node2 = self._points.loc[elem.node2]
                node3 = self._points.loc[elem.node3] if elem.type == 'area3' else self._points.loc[elem.node4] 
                v1 = np.array([node2.x - node1.x, node2.y - node1.y, node2.z - node1.z])
                v2 = np.array([node3.x - node1.x, node3.y - node1.y, node3.z - node1.z])
                v3 = np.cross(v1, v2)
                v3 = v3/np.linalg.norm(v3)

                v1 = np.cross([0, 0, 1], v3)
                n1 = np.linalg.norm(v1)
                v1 = [1, 0, 0] if abs(n1) < 1.0e-10 else v1
                v1 = v1/np.linalg.norm(v1)
                v2 = np.cross(v3, v1)
            elif str(elem.type).startswith("solid"):
                v1 = np.array([1, 0, 0])
                v2 = np.array([0, 1, 0])
                v3 = np.array([0, 0, 1])
            elif str(elem.type).startswith("point"):
                v1 = np.array([1, 0, 0])
                v2 = np.array([0, 1, 0])
                v3 = np.array([0, 0, 1])
            else:
                raise ValueError('element type not recognized')
            
            normals[elem.element] = [v1, v2, v3]
        return normals

    def get_normals_femix(self):
        self.set_indexes()
        normals = {}
        for elem in self._elements.itertuples():
            if str(elem.type).startswith("line"):
                node1 = self._points.loc[elem.node1]
                node2 = self._points.loc[elem.node2]
                v1 = np.array([node2.x - node1.x, node2.y - node1.y, node2.z - node1.z])
                v1 = v1/np.linalg.norm(v1)
                v3 = np.cross(v1, [0, 1, 0])
                n3 = np.linalg.norm(v3)
                v3 = [-np.sign(v1[2]), 0, 0] if abs(n3) < 1.0e-10 else v3/n3
                v2 = np.cross(v3, v1)
            elif str(elem.type).startswith("area"):
                node1 = self._points.loc[elem.node1]
                node2 = self._points.loc[elem.node2]
                node3 = self._points.loc[elem.node3] if elem.type == 'area3' else self._points.loc[elem.node4] 
                v1 = np.array([node2.x - node1.x, node2.y - node1.y, node2.z - node1.z])
                v2 = np.array([node3.x - node1.x, node3.y - node1.y, node3.z - node1.z])
                v3 = np.cross(v1, v2)
                v3 = v3/np.linalg.norm(v3)

                v1 = np.cross([0, 1, 0], v3)
                n1 = np.linalg.norm(v1)
                v1 = np.cross(v3, [1, 0, 0]) if abs(n1) < 1.0e-10 else v1
                v1 = v1/np.linalg.norm(v1)
                v2 = np.cross(v3, v1)
            elif str(elem.type).startswith("solid"):
                v1 = np.array([1, 0, 0])
                v2 = np.array([0, 1, 0])
                v3 = np.array([0, 0, 1])
            elif str(elem.type).startswith("point"):
                v1 = np.array([1, 0, 0])
                v2 = np.array([0, 1, 0])
                v3 = np.array([0, 0, 1])
            else:
                raise ValueError('element type not recognized')
            
            normals[elem.element] = [v1, v2, v3]
        return normals


class OfemStruct:

    def __init__(self, title: str):
        self.title = title
        self._dirty = [False for i in range(NTABLES)]
        # GEOMETRY
        self._mesh: OfemMesh = OfemMesh(self.title)
        self._results = {'node': [], 'element': [], 'elementnode': []}
        # MATERIALS
        self._sections = pd.DataFrame(columns= ["section", "type", "material"])
        self._supports = pd.DataFrame(columns= ["point", "ux", "uy", "uz", "rx", "ry", "rz"])
        self._materials = pd.DataFrame(columns= ["material", "type"])
        self._elemsections = pd.DataFrame(columns= ["element", "section"])
        # LOADS
        self._loadcases = pd.DataFrame(columns= ["loadcase", "type", "title"])
        self._loadcombinations = pd.DataFrame(columns= ["combination", "type", "title"])
        self._pointloads = pd.DataFrame(columns= ["point", "loadcase", "fx", "fy", "fz", "mx", "my", "mz"])
        self._lineloads = pd.DataFrame(columns= ["element", "loadcase", 'direction', "fx", "fy", "fz", "mx"])
        self._arealoads = pd.DataFrame(columns= ["element", "loadcase", 'direction', "px", "py", "pz"])
        self._solidloads = pd.DataFrame(columns= ["element", "loadcase", "fx", "fy", "fz", "mx", "my", "mz"])
        return

    def set_indexes(self):
        if self._dirty[SECTIONS]:
            self._sections['isection'] = self._sections['section'].copy()
            self._sections.set_index('isection', inplace=True)
            self._dirty[SECTIONS] = False
        if self._dirty[SUPPORTS]:
            self._supports['isupport'] = self._supports['point'].copy()
            self._supports.set_index('isupport', inplace=True)
            self._dirty[SUPPORTS] = False
        if self._dirty[MATERIALS]:
            self._materials['imaterial'] = self._materials['material'].copy()
            self._materials.set_index('imaterial', inplace=True)
            self._dirty[MATERIALS] = False
        if self._dirty[ELEMSECTIONS]:
            self._elemsections['ielement'] = self._elemsections['element'].copy()
            self._elemsections.set_index('ielement', inplace=True)
            self._dirty[ELEMSECTIONS] = False
        if self._dirty[POINTLOADS]:
            self._pointloads['ipoint'] = self._pointloads['point'].copy()
            self._pointloads.set_index('ipoint', inplace=True)
            self._dirty[POINTLOADS] = False
        if self._dirty[LINELOADS]:
            self._lineloads['ielement'] = self._lineloads['element'].copy()
            self._lineloads.set_index('ielement', inplace=True)
            self._dirty[LINELOADS] = False
        if self._dirty[AREALOADS]:
            self._arealoads['ielement'] = self._arealoads['element'].copy()
            self._arealoads.set_index('ielement', inplace=True)
            self._dirty[AREALOADS] = False
        if self._dirty[SOLIDLOADS]:
            self._solidloads['ielement'] = self._solidloads['element'].copy()
            self._solidloads.set_index('ielement', inplace=True)
            self._dirty[SOLIDLOADS] = False
        if self._dirty[LOADCASES]:
            self._loadcases['iloadcase'] = self._loadcases['loadcase'].copy()
            self._loadcases.set_index('iloadcase', inplace=True)
            self._dirty[LOADCASES] = False
        if self._dirty[LOADCOMBINATIONS]:
            self._loadcombinations['icombination'] = self._loadcombinations['combination'].copy()
            self._loadcombinations.set_index('icombination', inplace=True)
            self._dirty[LOADCOMBINATIONS] = False

        self.mesh.set_indexes()
        return

    def read_excel(self, filename: str):
        path = Path(filename)
        if path.suffix == ".xfem":
            self.read_xfem(filename)

        dfs = pd.read_excel(filename, sheet_name=None)

        # coordinates
        if "points" in dfs:
            self.mesh._points = dfs["points"]
            self.mesh._points["point"] = self.mesh._points["point"].astype(str)

        # elements
        if "elements" in dfs:
            self.mesh._elements = dfs["elements"]
            self.mesh._elements["element"] = self.mesh._elements["element"].astype(str)
            self.mesh.elemlist = {k: self.mesh._elements[self.mesh._elements["type"] == k]["element"].values for k in elemtypes}

        # sections
        if "sections" in dfs:
            self._sections = dfs["sections"]
            self._dirty[SECTIONS] = True
            
        if "elementsections" in dfs:
            self._elemsections = dfs["elementsections"]
            self._dirty[ELEMSECTIONS] = True

        # supports
        if "supports" in dfs:
            self._supports = dfs["supports"]
            self._dirty[SUPPORTS] = True

        # materials
        if "materials" in dfs:
            self._materials = dfs["materials"]
            self._dirty[MATERIALS] = True

        # point loads
        if "pointloads" in dfs:
            self._pointloads = dfs["pointloads"]
            self._dirty[POINTLOADS] = True
            
        # line loads
        if "lineloads" in dfs:
            self._lineloads = dfs["lineloads"]
            self._dirty[LINELOADS] = True
            
        # area loads
        if "arealoads" in dfs:
            self._arealoads = dfs["arealoads"]
            self._dirty[AREALOADS] = True   
            
        # solid loads
        if "solidloads" in dfs:
            self._solidloads = dfs["solidloads"]
            self._dirty[SOLIDLOADS] = True
        
        # load cases
        if "loadcases" in dfs:
            self._loadcases = dfs["loadcases"]
            self._dirty[LOADCASES] = True   
        
        # load combinations
        if "loadcombinations" in dfs:
            self._loadcombinations = dfs["loadcombinations"]
            self._dirty[LOADCOMBINATIONS] = True

        return

    def write_excel(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xlsx":
            filename = path.with_suffix(".xlsx")

        with pd.ExcelWriter(filename) as writer:
            # Write each DataFrame to a different sheet
            self.mesh._points.to_excel(writer, sheet_name='points', index=False)
            self.mesh._elements.to_excel(writer, sheet_name='elements', index=False)
            if not self._sections.empty:
                self._sections.to_excel(writer, sheet_name='sections', index=False)
            if not self._elemsections.empty:
                self._elemsections.to_excel(writer, sheet_name='elementsections', index=False)
            if not self._materials.empty:
                self._materials.to_excel(writer, sheet_name='materials', index=False)
            if not self._supports.empty:
                self._supports.to_excel(writer, sheet_name='supports', index=False)
            if not self._loadcases.empty:
                self._loadcases.to_excel(writer, sheet_name='loadcases', index=False)
            if not self._loadcombinations.empty:
                self._loadcombinations.to_excel(writer, sheet_name='loadcombinations', index=False)
            if not self._pointloads.empty:
                self._pointloads.to_excel(writer, sheet_name='pointloads', index=False)
            if not self._lineloads.empty:
                self._lineloads.to_excel(writer, sheet_name='lineloads', index=False)
            if not self._arealoads.empty:
                self._arealoads.to_excel(writer, sheet_name='arealoads', index=False)
            if not self._solidloads.empty:
                self._solidloads.to_excel(writer, sheet_name='solidloads', index=False)
        return

    def write_xfem(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xfem":
            filename = path.with_suffix(".xfem")

        self.mesh.write_xfem(filename)

        files = self.to_dict()
        json_data = json.dumps(files, indent=2).replace('NaN', 'null')
        # with open(filename+'.json', 'w') as f:
        #     f.write(json_data)

        # Create an in-memory buffer
        json_buffer = io.BytesIO(json_data.encode('utf-8'))
        # Reset buffer position to the beginning
        json_buffer.seek(0)
        # Create a ZIP file in-memory and add the JSON buffer
        if path.exists():
            replace_bytesio_in_zip(filename, 'struct.json', json_buffer.read().decode('utf-8'))
        else:
            with zipfile.ZipFile(filename, 'w') as zip_file:
                zip_file.writestr('struct.json', json_buffer.read().decode('utf-8'))    
            
        return
    
    def save(self, filename: str, file_format: str = None):
        path = Path(filename)
        
        if path.suffix == "" and file_format == None:
            raise ValueError(f"File format not recognized")

        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xlsx":
            self.write_excel(filename)
        elif file_format == ".xfem":
            self.write_xfem(filename)
        else:
            raise ValueError(f"File format {file_format} not recognized")

        # self._dirty = [False for i in range(NTABLES)]
        return

    def read_xfem(self, filename: str): 
        path = Path(filename)
        if path.suffix != ".xfem":
            raise ValueError(f"File {filename} is not a .xfem file")

        with zipfile.ZipFile(filename, 'r') as zip_file:
            with zip_file.open('struct.json') as json_file:
                data = json.load(json_file)
                self.from_dict(data)
            with zip_file.open('mesh.json') as json_file:
                data = json.load(json_file)
                self.mesh.from_dict(data)

        return

    def read(self, filename: str, file_format: str = None):
        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xlsx":
            self.read_excel(filename)
        elif file_format == ".xfem":
            self.read_xfem(filename)
        else:
            raise ValueError(f"File format {file_format} not recognized")
        return

    def to_dict(self):
        return {
            "sections": self._sections.to_dict(orient="records"),
            "elementsections": self._elemsections.to_dict(orient="records"),
            "supports": self._supports.to_dict(orient="records"),
            "materials": self._materials.to_dict(orient="records"),
            "pointloads": self._pointloads.to_dict(orient="records"),
            "lineloads": self._lineloads.to_dict(orient="records"),
            "arealoads": self._arealoads.to_dict(orient="records"),
            "solidloads": self._solidloads.to_dict(orient="records"),
            "loadcases": self._loadcases.to_dict(orient="records"),
            "loadcombinations": self._loadcombinations.to_dict(orient="records")
        }

    def from_dict(self, ofem_dict: dict):
        self._dirty = [False for i in range(NTABLES)]

        json_buffer = io.BytesIO(json.dumps(ofem_dict["sections"]).encode())
        json_buffer.seek(0)
        self._sections = pd.read_json(json_buffer, orient='records')
        if not self._sections.empty:
            self._dirty[SECTIONS] = True
        
        json_buffer = io.BytesIO(json.dumps(ofem_dict["elementsections"]).encode())
        json_buffer.seek(0)
        self._elemsections = pd.read_json(json_buffer, orient='records')
        if not self._elemsections.empty:
            self._dirty[ELEMSECTIONS] = True
        
        json_buffer = io.BytesIO(json.dumps(ofem_dict["supports"]).encode())
        json_buffer.seek(0)
        self._supports = pd.read_json(json_buffer, orient='records')
        if not self._supports.empty:
            self._dirty[SUPPORTS] = True
        
        json_buffer = io.BytesIO(json.dumps(ofem_dict["materials"]).encode())
        json_buffer.seek(0)
        self._materials = pd.read_json(json_buffer, orient='records')
        if not self._materials.empty:
            self._dirty[MATERIALS] = True
        
        json_buffer = io.BytesIO(json.dumps(ofem_dict["pointloads"]).encode())
        json_buffer.seek(0)
        self._pointloads = pd.read_json(json_buffer, orient='records')
        if not self._pointloads.empty:
            self._dirty[POINTLOADS] = True
        
        json_buffer = io.BytesIO(json.dumps(ofem_dict["lineloads"]).encode())
        json_buffer.seek(0)
        self._lineloads = pd.read_json(json_buffer, orient='records')
        if not self._lineloads.empty:
            self._dirty[LINELOADS] = True
    
        json_buffer = io.BytesIO(json.dumps(ofem_dict["arealoads"]).encode())
        json_buffer.seek(0)
        self._arealoads = pd.read_json(json_buffer, orient='records')
        if not self._arealoads.empty:
            self._dirty[AREALOADS] = True
        
        json_buffer = io.BytesIO(json.dumps(ofem_dict["solidloads"]).encode())
        json_buffer.seek(0)
        self._solidloads = pd.read_json(json_buffer, orient='records')
        if not self._solidloads.empty:
            self._dirty[SOLIDLOADS] = True
        
        json_buffer = io.BytesIO(json.dumps(ofem_dict["loadcases"]).encode())
        json_buffer.seek(0)
        self._loadcases = pd.read_json(json_buffer, orient='records')
        if not self._loadcases.empty:
            self._dirty[LOADCASES] = True
    
        json_buffer = io.BytesIO(json.dumps(ofem_dict["loadcombinations"]).encode())
        json_buffer.seek(0)
        self._loadcombinations = pd.read_json(json_buffer, orient='records')
        if not self._loadcombinations.empty: 
            self._dirty[LOADCOMBINATIONS] = True

        return

    @property
    def mesh(self):
        return self._mesh
    
    @mesh.setter
    def mesh(self, mesh):
        if False:
            self._mesh = mesh
            self._mesh._dirtyelements = True
            self._mesh._dirtypoints = True
        else: 
            self.mesh = mesh
        return
    
    # @property
    # def title(self):
    #     return self._mesh._title
    
    # @title.setter
    # def title(self, title):
    #     self._mesh._title = title
        
    @property
    def points(self):
        return self._mesh.points
    
    @points.setter
    def points(self, points):
        self._mesh.points = points
        self._mesh._dirtypoints = True
    
    @property
    def elements(self):
        return self._mesh.elements
    
    @elements.setter
    def elements(self, elements):
        self._mesh.elements = elements
        self._mesh._dirtyelements = True

    @property
    def sections(self):
        return self._sections
    
    @sections.setter
    def sections(self, sections):
        self._sections = sections
        self._dirty[SECTIONS] = True
        
    @property
    def supports(self):
        return self._supports
    
    @supports.setter
    def supports(self, supports):
        self._supports = supports
        self._dirty[SUPPORTS] = True
    
    @property
    def materials(self):
        return self._materials
    
    @materials.setter
    def materials(self, materials):
        self._materials = materials
        self._dirty[MATERIALS] = True
    
    @property
    def element_sections(self):
        return self._elemsections
    
    @element_sections.setter
    def element_sections(self, elemsections):
        self._elemsections = elemsections
        self._dirty[ELEMSECTIONS] = True

    @property
    def point_loads(self):
        return self._pointloads
    
    @point_loads.setter
    def point_loads(self, pointloads):
        self._pointloads = pointloads
        self._dirty[POINTLOADS] = True
    
    @property
    def line_loads(self):
        return self._lineloads
    
    @line_loads.setter
    def line_loads(self, lineloads):
        self._lineloads = lineloads
        self._dirty[LINELOADS] = True

    @property
    def area_loads(self):
        return self._arealoads

    @area_loads.setter
    def area_loads(self, arealoads):
        self._arealoads = arealoads
        self._dirty[AREALOADS] = True

    @property
    def solid_loads(self):
        return self._solidloads

    @solid_loads.setter
    def solid_loads(self, solidloads):
        self._solidloads = solidloads
        self._dirty[SOLIDLOADS] = True

    @property
    def load_cases(self):
        return self._loadcases
    
    @load_cases.setter
    def load_cases(self, loadcases):
        self._loadcases = loadcases
        self._dirty[LOADCASES] = True

    @property
    def load_combinations(self):
        return self._loadcombinations

    @load_combinations.setter
    def load_combinations(self, loadcombinations):
        self._loadcombinations = loadcombinations
        self._dirty[LOADCOMBINATIONS] = True
    
    def get_combos(self):
        combos = {k: {"type": "", "coefs": {}} for k in self._loadcombinations['combo'].unique().tolist()}
        for k in combos.keys():
            for combo in self._loadcombinations[self._loadcombinations['combo'] == k].itertuples():
                if combo.type is not None:
                    combos[k]["type"] = combo.type
                combos[k]["coefs"][combo.case] = combo.coef
            # combo = self._loadcombinations[self._loadcombinations['combination'] == k]
            # combos[k] = {k: v for k, v in zip(combo['loadcase'], combo['coef'])}          
        return combos
    
    def get_cases(self):
        ### falta implementar a direção

        cases = {
            k: {"index": 0, "name": "", "type": "dead", "point": {}, "line": {}, "area": {}, 
                "temp": {}, "grav": {}, "displ": {}} 
            for k in self._loadcases['case'].unique().tolist()}

        for i, k in enumerate(cases.keys()):
            case = self._loadcases[self._loadcases['case'] == k].iloc[0]
            cases[k]["name"] = case.case
            cases[k]["type"] = case.type
            cases[k]["index"] = i + 1
            # go through gravity loads
            cases[k]["grav"] = -case.gravity if case.gravity is not None else 0
            # go through point loads
            if not self._pointloads.empty:
                for load in self._pointloads[self._pointloads['loadcase'] == k].itertuples():
                    if not load.point in cases[k]["point"]:
                        cases[k]["point"][load.point] = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                    cases[k]["point"][load.point] += np.array([load.fx, load.fy, load.fz, load.mx, load.my, load.mz])
            # go through line loads
            if not self._lineloads.empty:
                for load in self._lineloads[self._lineloads['loadcase'] == k].itertuples():
                    if not load.element in cases[k]["line"]:
                        cases[k]["line"][load.element] = np.array([0.0, 0.0, 0.0, 0.0])
                    cases[k]["line"][load.element] += np.array([load.fx, load.fy, load.fz, load.mx])
            # go through area loads
            if not self._arealoads.empty:
                for load in self._arealoads[self._arealoads['loadcase'] == k].itertuples():
                    if not load.element in cases[k]["area"]:
                        cases[k]["area"][load.element] = np.array([0.0, 0.0, 0.0])
                    cases[k]["area"][load.element] += np.array([load.px, load.py, load.pz])

        return cases

    @property
    def num_materials(self):
        return self._materials.shape[0]
    
    @property
    def num_sections(self):
        return self._sections.shape[0]
    
    @property
    def num_supports(self):
        return self._supports.shape[0]
    
    @property
    def num_load_cases(self):
        return self._loadcases.shape[0]


class OfemData:
    def __init__(self) -> None:
        self._point_data = pd.DataFrame(
            columns = ['point', 'tag', 'type', 'value', 'v1', 'v2', 'v3'])
        self._element_data = pd.DataFrame(
            columns = ['element', 'tag', 'type', 'value'])
        self._element_node_data = pd.DataFrame(
            columns = ['element', 'tag', 'type', 'value', 'node1', 'node2'])

    def read_xfem(self, filename: str): 
        path = Path(filename)
        if path.suffix != ".xfem":
            raise ValueError(f"File {filename} is not a .xfem file")

        with zipfile.ZipFile(filename, 'r') as zip_file:
            with zip_file.open('data.json') as json_file:
                data = json.load(json_file)
                self.from_dict(data)

        self._dirty = [True for i in range(NTABLES)]
        return

    def read(self, filename: str, file_format: str = None):
        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xlsx":
            self.read_excel(filename)
        elif file_format == ".xfem":
            self.read_xfem(filename)
        else:
            raise ValueError(f"File format {file_format} not recognized")
        return

    def to_dict(self):
        return {
            "point_data": self._point_data.to_dict(orient="records"), 
            "element_data": self._element_data.to_dict(orient="records"), 
            "element_node_data": self._element_node_data.to_dict(orient="records"),
        }

    def from_dict(self, ofem_dict: dict):
        json_buffer = io.BytesIO(json.dumps(ofem_dict["point_data"]).encode())
        json_buffer.seek(0)
        self.mesh._points = pd.read_json(json_buffer, orient='records')
        json_buffer = io.BytesIO(json.dumps(ofem_dict["element_data"]).encode())
        json_buffer.seek(0)
        self.mesh._elements = pd.read_json(json_buffer, orient='records')
        json_buffer = io.BytesIO(json.dumps(ofem_dict["element_node_data"]).encode())
        json_buffer.seek(0)
        self._sections = pd.read_json(json_buffer, orient='records')
        return

    @property
    def point_data(self):
        return self._point_data

    @point_data.setter
    def point_data(self, pointdata):
        self._point_data = pd.concat(self._point_data, pointdata)
        return

    @property
    def element_data(self):
        return self._point_data

    @element_data.setter
    def element_data(self, elementdata):
        self._element_data = pd.concat(self._element_data, elementdata)
        return

    @property
    def element_node_data(self):
        return self._point_data

    @element_node_data.setter
    def element_node_data(self, elementnodedata):
        self._element_node_data = pd.concat(self._element_node_data, elementnodedata)
        return