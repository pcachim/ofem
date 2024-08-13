DEBUG = True

from . import common
from .common import Model, Entities
from .ofem.libofemc import OfemSolverFile
from . import ofem
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union
import numpy as np
import pandas as pd
import meshio, gmsh
import sys, os, io, json, zipfile, re
import timeit, logging, shutil

from . import adapters

# pd.options.mode.copy_on_write = True
elemtypes = list(common.ofem_meshio.keys())

NTABLES = 11

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
GROUPS = 10

elem_types = {
    1: "STRE2D",
    2: "STRA2D",
    3: "AXIS2D",
    4: "VOLUME",
    5: "SLAB2D",
    6: "SHELLC",
    7: "FRAM3D",
    8: "TRUS3D",
    9: "FLATSH",
    10: "FOUNDA",
    11: "INTF1D",
    12: "INTF2D",
    13: "FR2DBN",
    14: "FR2DTM",
    15: "FR3DCO",
    16: "TRUS2D",
}

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


def run_gmsh(s):

    path = Path(s)
    s = str(path.parent / (path.stem + ".msh"))

    gmsh.initialize(sys.argv)

    gmsh.option.setNumber("Mesh.Nodes", 1)
    gmsh.option.setNumber("Mesh.NodeSize", 8)
    gmsh.option.setNumber("Mesh.Lines", 1)
    gmsh.option.setNumber("Mesh.LineWidth", 5)
    gmsh.option.setNumber("Mesh.SurfaceFaces", 0)
    gmsh.option.setNumber("View.Visible", 0)
    gmsh.option.setNumber("Mesh.ColorCarousel", common.gmsh_colors['physical'])

    gmsh.open(s)
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()

    gmsh.finalize()


class xdfemMesh:
    
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
    
    def _set_tags_to_id(self, base: int = 1, tostr: bool = False):
        if tostr:
            self._nodetag_to_id = dict(zip(self._points["point"].values,  [str(i) for i in range(base, self.num_points+base)]))
            self._elemtag_to_id = dict(zip(self._elements["element"].values, [str(i) for i in range(base, self.num_elements+base)]))
        else:
            self._nodetag_to_id = dict(zip(self._points["point"].values,  np.arange(base, self.num_points+base)))
            self._elemtag_to_id = dict(zip(self._elements["element"].values, np.arange(base, self.num_elements+base)))
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

    def get_list_node_columns(self, elemtype: str):
        nnodes = common.ofem_nnodes[elemtype]
        return [f"node{i}" for i in range(1, nnodes+1)]

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

    def save(self, filename: str, file_format: str = None):
        if file_format == None:
            file_format = Path(filename).suffix
            if file_format == "":
                file_format = ".msh"
                filename += file_format

        if file_format == ".xdfem":
            self._to_ofem(filename)
        elif file_format == '.msh':
            self.write_gmsh(filename)
        elif file_format == ".vtk" or file_format == ".vtu":
            msh = self.to_meshio()
            msh.write(filename, file_format="vtk", binary=False)
        else:
            raise ValueError(f"File format {file_format} not recognized")
        return

    def save_excel(self, filename: str):
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

    def save_xdfem(self, filename: str): 
        path = Path(filename)
        if path.suffix != ".xdfem":
            raise ValueError(f"File {filename} is not a .xfem file")

        with zipfile.ZipFile(filename, 'r') as zip_file:
            with zip_file.open('mesh.json') as json_file:
                data = json.load(json_file)
                self.from_dict(data)

        self._dirtypoints = True
        self._dirtyelements = True
        return

    def set_points_elems_id(self, base: int = 1):
        self._set_tags_to_id(base)     
        self._points["id"] = self._points["point"].apply(lambda x: self._nodetag_to_id[x])
        self._elements["id"] = self._elements["element"].apply(lambda x: self._elemtag_to_id[x])
        self._dirtypoints = False
        self._dirtyelements = False
        return 

    def set_indexes(self):
        # if self._dirtyelements:
        self._elements['ielement'] = self._elements['element'].copy()
        self._elements.set_index('ielement', inplace=True)
        self._dirtyelements = False
        # if self._dirtypoints:
        ipoint = self._points['point'].copy()
        self._points.set_index(ipoint, inplace=True)
        self._dirtypoints = False

    def read(self, filename: str, file_format: str = None):
        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xlsx":
            self.save_excel(filename)
        elif file_format == ".xdfem":
            self.save_xdfem(filename)
        else:
            raise ValueError(f"File format {file_format} not recognized")
        return

    def to_dict(self):
        return {
            "points": self._points.to_dict(orient="records"), 
            "elements": self._elements.to_dict(orient="records"), 
        }

    def to_meshio(self):

        self._set_tags_to_id(base=0)
        points = self._points[["x", "y", "z"]].values.tolist()

        elems = []
        unique_elements = self._elements["type"].unique()
        for ielem in unique_elements:
            k_elems = self._elements[self._elements["type"] == ielem].copy()
            l_nodes = self.get_list_node_columns(ielem)

        ### tentar este método quando passa xfem para gmsh
            k_elems.loc[:,l_nodes] = k_elems.loc[:,l_nodes].replace(to_replace=self._nodetag_to_id).astype(str)
            elems.append((common.ofem_meshio[ielem], np.array(k_elems[l_nodes]).astype(int).tolist()))

        mesh = meshio.Mesh(
            points,
            elems)
        #     # Optionally provide extra data on points, cells, etc.
        #     point_data={"T": [0.3, -1.2, 0.5, 0.7, 0.0, -3.0]},
        #     # Each item in cell data must match the cells array
        #     cell_data={"a": [[0.1, 0.2], [0.4]]},
        # )

        return mesh

    def write_xdfem(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xdfem":
            filename = path.with_suffix(".xdfem")

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
        elemlist = self._elements['type'].unique()

        # Add elements
        for elemtype in elemlist:

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


class xdfemStruct:

    def __init__(self, title: str = "New Model"):
        self._title = title
        self._dirty = [False for i in range(NTABLES)]
        self._filename = None
        # GEOMETRY
        self._mesh: xdfemMesh = xdfemMesh(self._title)
        # MATERIALS AND SECTIONS
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
        # RESULTS
        self._results: xdfemData = xdfemData()
        # GROUPS
        self._groups = pd.DataFrame(columns= ["group", "point", "line", "area", "solid"])
        return

    def export_msh(self, filename: str, model: str = 'geometry', entities: str = 'sections'):
        """Writes a GMSH mesh file and opens it in GMSH

        Args:
            filename (str): the name of the file to be written
        """
        path = Path(filename)
        if path.suffix != ".msh":
            filename = str(path.parent / (path.stem + ".msh"))
        print(f"Writing file {filename}")

        # process options
        if model not in ['geometry', 'loads']:
            raise ValueError('model must be "geometry" or "loads"')

        if entities not in ['groups', 'types', 'sections', 'materials', 'elements']:
            raise ValueError('entities must be "types", "sections" or "materials"')

        if DEBUG:
            starttime = timeit.default_timer()
            logging.info(f"Processing elements ({self.mesh.num_elements})...")

        # initialize gmsh
        gmsh.initialize(sys.argv)

        modelname = Path(filename).stem
        gmsh.model.add(modelname)
        gmsh.model.setFileName(filename)
        
        if entities == 'elements':
            self.to_gmsh_entities(model, 'sections')
        else:
            self.to_gmsh(model, entities)
        attrs = gmsh.model.getAttribute("sections")
        # SAVE GEOMETRIC DATA
        gmsh.option.setNumber("Mesh.SaveAll", 0)
        gmsh.write(filename)

        if DEBUG:
            logging.debug(f"Execution time: {round((timeit.default_timer() - starttime)*1000,3)} ms")
            logging.debug("Processing GMSH intialization...")

        gmsh.finalize()

        # run_gmsh(filename)

        return

    def export_msh_results(self, filename, model: str = 'geometry', entities: str = 'sections',
                        displacements: bool = True, stresses_avg: bool = False, stresses_eln: bool = False):
        """Writes a GMSH mesh file and opens it in GMSH

        Args:
            filename (str): the name of the file to be written
        """
        path = Path(filename)
        # if path.suffix != ".msh":
        #     filename = str(path.parent / (path.stem + ".msh"))
        filename = str(path.parent / (path.stem + ".res.msh"))

        # process options
        if model not in ['geometry', 'loads']:
            raise ValueError('model must be "geometry" or "loads"')

        if entities not in ['types', 'sections', 'materials']:
            raise ValueError('entities must be "types", "sections" or "materials"')

        # initialize gmsh
        gmsh.initialize(sys.argv)

        modelname = Path(filename).stem
        gmsh.model.add(modelname)
        gmsh.model.setFileName(filename)

        self.to_gmsh(model, entities)

        gmsh.option.setNumber("Mesh.SaveAll", 1)
        gmsh.write(filename)

        for i, case in enumerate(self._loadcases.itertuples()):
            # DATA NODAL
            if displacements:
                values = self._results.items['displacements'].loc[self._results.items['displacements']['icomb'] == i+1]
                list_of_dof = [col for col in values.columns if col.startswith('disp')]
                for idof in list_of_dof:
                    view = gmsh.view.add(f'{case.case}: {idof}')
                    gmsh.view.addHomogeneousModelData(
                        view, 0, modelname, "NodeData", values["point"].values, values[idof].values)
                    gmsh.view.option.setNumber(view, "Visible", 0)
                    gmsh.view.write(view, filename, append=True)

            if stresses_avg:
                values = self._results.items['stresses_avg'].loc[self._results.items['stresses_avg']['icomb'] == i+1]
                unique_values = values['elem_type'].unique()
                list_of_dof = [col for col in values.columns if col.startswith('str')]
                for itype in unique_values:
                    for idof in list_of_dof:
                        view = gmsh.view.add(f'{case.case}: avg-{elem_types[itype]}-{idof}')
                        gmsh.view.addHomogeneousModelData(view, 0, modelname, "NodeData", values["point"].values, values[idof].values)
                        gmsh.view.option.setNumber(view, "Visible", 0)
                        gmsh.view.write(view, filename, append=True)

                # DATA ELEMENTS
            if stresses_eln:
                values = self._results.items['stresses_eln'].loc[self._results.items['stresses_eln']['icomb'] == i+1]
                list_of_dof = [col for col in values.columns if col.startswith('str')]
                elem_list = values[(values['node'] == 1) & (values['icomb'] == i+1)].copy()
                elem_list['element'] = elem_list["element"].apply(lambda x: self.mesh._elemtag_to_id[x])
                elem_list = elem_list['element'].values
                for idof in list_of_dof:
                    view = gmsh.view.add(f'{case.case}: eln-{idof}')
                    vlist = values[idof].values
                    gmsh.view.addHomogeneousModelData(
                        view, 0, modelname, "ElementNodeData", elem_list, vlist)
                    gmsh.view.option.setNumber(view, "Visible", 0)
                    gmsh.view.write(view, filename, append=True)

        # gmsh.fltk.run()
        gmsh.finalize()

        # mesh = meshio.read(filename)
        try:
            filename = str(path.parent / (path.stem + ".res.vtu"))  
            mesh = self.to_meshio()
            meshio.write(filename, mesh, file_format="vtu", binary=True)
        except:
            print(f"Could not write {filename}")

        return

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

    @staticmethod
    def import_sap2000(filename: str):
        return adapters.sap2000.Reader(filename).to_ofem_struct()

    @staticmethod
    def import_msh(filename: str):
        return adapters.msh.Reader(filename).to_xdfem_struct()

    def read_excel(self, filename: str):
        path = Path(filename)
        if path.suffix == ".xlsx":
            self.read_xdfem(filename)

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

        # groups
        if "groups" in dfs:
            self._groups = dfs["groups"]
            self._dirty[GROUPS] = True
        return

    def read_xdfem(self, filename: str): 
        path = Path(filename)
        if path.suffix != ".xdfem":
            raise ValueError(f"File {filename} is not a .xfem file")

        with zipfile.ZipFile(filename, 'r') as zip_file:
            with zip_file.open('struct.json') as json_file:
                data = json.load(json_file)
                self.from_dict(data)
            with zip_file.open('mesh.json') as json_file:
                data = json.load(json_file)
                self.mesh.from_dict(data)
            with zip_file.open('data.json') as json_file:
                data = json.load(json_file)
                self._results._from_dict(data)

        self._filename = path.parent / path.stem
        return

    def read(self, filename: str, file_format: str = None):
        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xlsx":
            self.read_excel(filename)
        elif file_format == ".xdfem":
            self.read_xdfem(filename)
        else:
            raise ValueError(f"File format {file_format} not recognized")
        return

    def save_xdfem(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xdfem":
            filename = path.with_suffix(".xdfem")

        self.mesh.write_xdfem(filename)

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

        self._results.write_xdfem(filename)

        self._filename = str(path.parent / path.stem)
        return

    def save_excel(self, filename: str):
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
            if not self._groups.empty:
                self._groups.to_excel(writer, sheet_name='groups', index=False)

            if 'displacements'in self._results.items.keys():
                self._results.items['displacements'].to_excel(writer, sheet_name='displacements', index=False)
            if 'reactions' in self._results.items.keys():
                self._results.items['reactions'].to_excel(writer, sheet_name='reactions', index=False)
            if 'stresses_avg' in self._results.items.keys():
                self._results.items['stresses_avg'].to_excel(writer, sheet_name='stresses_avg', index=False)
            if 'stresses_eln' in self._results.items.keys():
                self._results.items['stresses_eln'].to_excel(writer, sheet_name='stresses_eln', index=False)
            if 'stresses_gauss' in self._results.items.keys():
                self._results.items['stresses_gauss'].to_excel(writer, sheet_name='stresses_gauss', index=False)
        return

    def save(self, filename: str = None, file_format: str = None):
        if filename == None:
            if self._filename == None:
                raise ValueError(f"Filename not provided")
            if file_format == None or file_format == ".xdfem":
                filename = self._filename + ".xdfem"
                file_format = ".xdfem"
            elif file_format == ".xlsx":
                filename = self._filename + ".xlsx"
                file_format = ".xlsx"
            else:
                raise ValueError(f"File format {file_format} not recognized")

        path = Path(filename)
        
        if path.suffix == "" and file_format == None:
            raise ValueError(f"File format not recognized")

        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xlsx":
            self.save_excel(filename)
        elif file_format == ".xdfem":
            self.save_xdfem(filename)

            if DEBUG:
                logging.debug("\nCopying 'xfem' file to 'zip' file.\n")
                shutil.copyfile(filename, filename + ".zip")
        else:
            raise ValueError(f"File format {file_format} not recognized")

        # self._dirty = [False for i in range(NTABLES)]
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
    
    def regen():
        pass

    def solve(self):
        import uuid
        
        filename = (str(uuid.uuid4()) if self._filename is None else self._filename ) 

        self.to_ofem(filename + ".ofem")
        ofem.solve(filename + ".ofem")

        options = ofem.OfemOptions().get()
        codes = ofem.OutputOptions.all()
        ofem.results(filename + ".ofem", codes, **options)

        point_map = dict(zip(self.mesh.points['id'], self.mesh.points['point']))
        element_map = dict(zip(self.mesh.elements['id'], self.mesh.elements['element']))

        dt =  ofem.get_csv_from_ofem(filename, ofem.libofemc.DI_CSV)
        dt['point'] = dt['point'].map(point_map)
        self._results.add("displacements", dt)

        dt = ofem.get_csv_from_ofem(filename, ofem.libofemc.RE_CSV)
        dt['point'] = dt['point'].map(point_map)
        self._results.add("reactions", dt)

        dt = ofem.get_csv_from_ofem(filename, ofem.libofemc.AST_CSV)
        dt['point'] = dt['point'].map(point_map)
        self._results.add("stresses_avg", dt)

        dt = ofem.get_csv_from_ofem(filename, ofem.libofemc.EST_CSV)
        dt['element'] = dt['element'].map(element_map)
        dt['point'] = dt['point'].map(point_map)
        self._results.add("stresses_eln", dt)

        dt = ofem.get_csv_from_ofem(filename, ofem.libofemc.GST_CSV)
        dt['element'] = dt['element'].map(element_map)
        self._results.add("stresses_gauss", dt)

        if DEBUG:
            logging.debug("\nFinishing calculating results.\n")
            logging.debug("\nCopying 'xfem' file to 'zip' file.\n")
            shutil.copyfile(filename + ".ofem", filename + ".ofem" + ".zip")

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
            "loadcombinations": self._loadcombinations.to_dict(orient="records"),
            "groups": self._groups.to_dict(orient="records")
        }

    def to_meshio(self):

        self.mesh._set_tags_to_id(base=0)
        points = self.mesh.points.sort_values(by='id')[["x", "y", "z"]].values.tolist()

        elements = []
        unique_elements = self.mesh.elements["type"].unique()
        for ielem in unique_elements:
            k_elems = self.elements[self.elements["type"] == ielem].copy()
            l_nodes = self.mesh.get_list_node_columns(ielem)
        ### tentar este método quando passa xfem para gmsh
            k_elems.loc[:,l_nodes] = k_elems.loc[:,l_nodes].replace(to_replace=self.mesh._nodetag_to_id)
            elements.append((common.ofem_meshio[ielem], np.array(k_elems[l_nodes]).astype(int).tolist()))

        elem_data = {}
        elems = self.elements.copy()
        sec_dict = dict(zip(self.sections['section'], range(len(self.sections['section']))))
        elems.loc[:,'section'] = self.element_sections.loc[:,'element'].apply(
            lambda x: sec_dict[self.element_sections.at[x, 'section']]
            )

        elem_data['section'] = []
        for i, ielem in enumerate(unique_elements):
            kelems = elems.loc[elems["type"] == ielem, 'section']
            elem_data['section'].append(
                kelems.values.tolist()
            )
            
        point_data = {}
        for i, case in enumerate(self._loadcases.itertuples()):
            values = self._results.items['displacements'].loc[self._results.items['displacements']['icomb'] == i+1].copy()
            values.loc[:,'point'] = values.loc[:,'point'].replace(to_replace=self.mesh._nodetag_to_id)
            values = values.sort_values(by='point')
            list_of_dof = [col for col in values.columns if col.startswith('disp')]
            for idof in list_of_dof:
                key = f'case: {case.case} % {idof}'
                point_data[key] = values[idof].values

            values = self._results.items['stresses_avg'].loc[self._results.items['stresses_avg']['icomb'] == i+1]
            values.loc[:,'point'] = values.loc[:,'point'].replace(to_replace=self.mesh._nodetag_to_id)
            values = values.sort_values(by='point')
            unique_values = values['elem_type'].unique()
            list_of_dof = [col for col in values.columns if col.startswith('str')]
            for itype in unique_values:
                for idof in list_of_dof:
                    key = f'{elem_types[itype]} - case: {case.case} % {idof}'
                    point_data[key] = values[idof].values

            # values = self._results.items['stresses_eln'].loc[self._results.items['stresses_eln']['icomb'] == i+1]
            # list_of_dof = [col for col in values.columns if col.startswith('str')]
            # elem_list = values[(values['node'] == 1) & (values['icomb'] == i+1)].copy()
            # elem_list['element'] = elem_list["element"].apply(lambda x: self.mesh._elemtag_to_id[x])
            # elem_list = elem_list['element'].values
            # for idof in list_of_dof:
            #     view = gmsh.view.add(f'{case.case}: eln-{idof}')
            #     vlist = values[idof].values
            #     gmsh.view.addHomogeneousModelData(
            #         view, 0, modelname, "ElementNodeData", elem_list, vlist)
            #     gmsh.view.option.setNumber(view, "Visible", 0)
            #     gmsh.view.write(view, filename, append=True)

        mesh = meshio.Mesh(points, elements, cell_data=elem_data ,point_data=point_data, )
            # #cell_data=elem_data,
        #     # Optionally provide extra data on points, cells, etc.
        #     point_data={"T": [0.3, -1.2, 0.5, 0.7, 0.0, -3.0]},
        #     # Each item in cell data must match the cells array
        #     cell_data={"a": [[0.1, 0.2], [0.4]]},
        # )

        return mesh

    def to_gmsh_entities(self, model: str = 'geometry', entities: str = 'sections', meshsize = 0.8):

        self.set_indexes()
        self.mesh.set_points_elems_id(1)

        joints = self.mesh.points.copy()
        frames = self.mesh.elements.loc[self.mesh.elements['type'].isin(common.ofem_lines)].copy()
        for etype in frames['type'].unique():
            nlist = self.mesh.get_list_node_columns(etype)
            for col in nlist:
                frames[col] = joints.loc[frames[col].values, 'id'].values
            frames['nodes'] = frames[nlist].values.tolist()

        frames.loc[:,'section'] = self.element_sections.loc[:,'element'].apply(
            lambda x: self.element_sections.at[x, 'section']
            )
        frames.loc[:,'material'] = frames.loc[:,'section'].apply(
            lambda x: self.sections.at[x, 'material']
            )
        framesections = frames['section'].unique()
        framematerials = frames['material'].unique()

        areas = self.mesh.elements.loc[self.mesh.elements['type'].isin(common.ofem_areas)].copy()
        for col in areas.columns:
            if not col.startswith('node'):
                continue
            areas[col] = joints.loc[areas[col].values, 'id'].values
        areas.loc[:,'section'] = self.element_sections.loc[:,'element'].apply(
            lambda x: self.element_sections.at[x, 'section']
            )
        areas.loc[:,'material'] = areas.loc[:,'section'].apply(
            lambda x: self.sections.at[x, 'material']
            )
        areasections = areas['section'].unique()
        areamaterials = areas['material'].unique()

        # JOINTS
        # max_values = joints[['x', 'y', 'z']].max()
        # min_values = joints[['x', 'y', 'z']].max()
        
        supps = self.supports
        supps['point'] = supps['point'].astype(str)
        supps['joined'] = supps[['ux', 'uy', 'uz', 'rx', 'ry', 'rz']].apply(lambda x: ''.join(map(str, x)), axis=1)
        supp_types = supps['joined'].unique()
        supp_nodes = supps['point'].values.tolist()

        # add free nodes
        joints['point'] = joints['id'].astype(str)
        free_nodes = joints[~joints['point'].isin(supp_nodes)].copy()
        list_of_nodes = []
        for node in free_nodes.itertuples():
            gmsh.model.geo.addPoint(node.x, node.y, node.z, meshSize=meshsize, tag=node.id)
            list_of_nodes.append(node.id)
        gmsh.model.geo.synchronize()

        gmsh.model.geo.addPhysicalGroup(common.POINT, list_of_nodes, name="free nodes")

        # add nodes for each type of support
        for sup_type in supp_types:
            supp_nodes = supps.loc[supps['joined'] == sup_type, 'point'].values.tolist()
            free_nodes = joints.loc[joints['point'].isin(supp_nodes)].copy()
            list_of_nodes = []
            for node in free_nodes.itertuples():
                gmsh.model.geo.addPoint(node.x, node.y, node.z, meshSize=meshsize, tag=node.id)
                list_of_nodes.append(node.id)

            gmsh.model.geo.synchronize()
            gmsh.model.geo.addPhysicalGroup(common.POINT, list_of_nodes, name="sup: " + sup_type)
            
        phy = gmsh.model.getPhysicalGroups()

        # ELEMENTS - FRAMES
        logging.info(f"Processing frames ({self.mesh.num_elements})...")

        # Adds each element as separate entity grouped by physical sections
        for sec in framesections:
            secframes = pd.DataFrame(frames.loc[frames['section']==sec])

            list_of_frames = []
            for elem in secframes.itertuples():
                gmsh.model.geo.addLine(elem.node1, elem.node2, elem.id)                
                list_of_frames.append(elem.id)

            gmsh.model.geo.synchronize()
            gmsh.model.geo.addPhysicalGroup(common.CURVE, list_of_frames, name="sec: " + sec)

        # ELEMENTS - AREAS

        for sec in areasections:
            secareas = areas.loc[areas['section']==sec].copy()

            list_of_areas = []
            for i, elem in secareas.iterrows():
                etype = elem['type']
                nlist = self.mesh.get_list_node_columns(etype)
                line_bound = []
                for i in range(len(nlist)):
                    tag = gmsh.model.geo.addLine(elem[nlist[i]], elem[nlist[(i+1)%len(nlist)]])
                    line_bound.append(tag)
                
                bound = gmsh.model.geo.addCurveLoop(line_bound, tag=elem.id)
                gmsh.model.geo.addPlaneSurface([bound], tag=elem.id)
                list_of_areas.append(elem.id)

            gmsh.model.geo.synchronize()
            gmsh.model.geo.addPhysicalGroup(common.SURFACE, list_of_areas, name="sec: " + sec)

        # ATTRIBUTES
        attrbs = self.to_dict()
        for key in attrbs:
            s = [str(value) for value in attrbs[key]]
            gmsh.model.set_attribute(key, s)

        # data_list = self.supports.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        # gmsh.model.setAttribute("Supports", data_list)
        # data_list = self.sections.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        # gmsh.model.setAttribute("Sections", data_list)
        # data_list = self.materials.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        # gmsh.model.setAttribute("Materials", data_list)

        gmsh.model.geo.synchronize()
        # gmsh.model.mesh.generate(1)
        # gmsh.model.mesh.generate(2)
        return

    def to_gmsh(self, model: str = 'geometry', entities: str = 'sections'):

        self.set_indexes()
        self.mesh.set_points_elems_id(1)

        joints = self.mesh.points.copy()
        frames = self.mesh.elements.loc[self.mesh.elements['type'].isin(common.ofem_lines)].copy()
        for etype in frames['type'].unique():
            nlist = self.mesh.get_list_node_columns(etype)
            for col in nlist:
                frames[col] = joints.loc[frames[col].values, 'id'].values
            frames['nodes'] = frames[nlist].values.tolist()

        frames.loc[:,'section'] = self.element_sections.loc[:,'element'].apply(
            lambda x: self.element_sections.at[x, 'section']
            )
        frames.loc[:,'material'] = frames.loc[:,'section'].apply(
            lambda x: self.sections.at[x, 'material']
            )
        framesections = frames['section'].unique()
        framematerials = frames['material'].unique()

        areas = self.mesh.elements.loc[self.mesh.elements['type'].isin(common.ofem_areas)].copy()
        for col in areas.columns:
            if not col.startswith('node'):
                continue
            areas[col] = joints.loc[areas[col].values, 'id'].values
        areas.loc[:,'section'] = self.element_sections.loc[:,'element'].apply(
            lambda x: self.element_sections.at[x, 'section']
            )
        areas.loc[:,'material'] = areas.loc[:,'section'].apply(
            lambda x: self.sections.at[x, 'material']
            )
        areasections = areas['section'].unique()
        areamaterials = areas['material'].unique()

        # JOINTS
        # max_values = joints[['x', 'y', 'z']].max()
        # min_values = joints[['x', 'y', 'z']].max()
        
        supps = self.supports
        supps['point'] = supps['point'].astype(str)
        supps['joined'] = supps[['ux', 'uy', 'uz', 'rx', 'ry', 'rz']].apply(lambda x: ''.join(map(str, x)), axis=1)
        supp_types = supps['joined'].unique()
        supp_nodes = supps['point'].values.tolist()

        # add free nodes
        joints['point'] = joints['id'].astype(str)
        free_nodes = joints[~joints['point'].isin(supp_nodes)].copy()
        free_nodes['coord'] = free_nodes[['x', 'y', 'z']].values.tolist()
        ient = gmsh.model.addDiscreteEntity(common.POINT)
        gmsh.model.setEntityName(common.CURVE, ient, 'free nodes')
        gmsh.model.mesh.addNodes(common.POINT, ient, free_nodes['id'].values, free_nodes['coord'].explode().to_list())

        # add nodes for each type of support
        for sup_type in supp_types:
            supp_nodes = supps.loc[supps['joined'] == sup_type, 'point'].values.tolist()
            free_nodes = joints.loc[joints['point'].isin(supp_nodes)].copy()
            free_nodes['coord'] = free_nodes[['x', 'y', 'z']].values.tolist()
            ient = gmsh.model.addDiscreteEntity(common.POINT)
            gmsh.model.setEntityName(common.CURVE, ient, 'sup: ' + sup_type)
            gmsh.model.mesh.addNodes(common.POINT, ient, free_nodes['id'].values, free_nodes['coord'].explode().to_list())

            gmsh.model.addPhysicalGroup(common.POINT, [ient], name="sup: " + sup_type)

        # ELEMENTS - FRAMES
        logging.info(f"Processing frames ({self.mesh.num_elements})...")

        if entities == 'sections':
            for sec in framesections:
                framesl = pd.DataFrame(frames.loc[frames['section']==sec])
                line = gmsh.model.addDiscreteEntity(common.CURVE)
                gmsh.model.setEntityName(common.CURVE, line, sec)

                for etype in framesl['type'].unique():
                    nlist = self.mesh.get_list_node_columns(etype)
                    frames2 = framesl.loc[framesl['type'] == etype].copy()
                    frames2['nodes'] = frames2[nlist].values.tolist()
                    gmsh.model.mesh.addElementsByType(line, common.ofem_gmsh[etype], frames2['id'].to_list(), 
                            frames2['nodes'].explode().to_list())

                gmsh.model.addPhysicalGroup(common.CURVE, [line], name="sec: " + sec)

        elif entities == 'elements':
            # Adds each element as separate entity grouped by physical sections
            for sec in framesections:
                secframes = pd.DataFrame(frames.loc[frames['section']==sec])

                list_of_frames = []
                for elem in secframes.itertuples():
                    etype = elem.type
                    line = gmsh.model.addDiscreteEntity(common.CURVE)
                    gmsh.model.setEntityName(common.CURVE, line, elem.element)
                    nlist = self.mesh.get_list_node_columns(etype)
                    frames2 = secframes.loc[frames['element'] == elem.element].copy()
                    frames2['nodes'] = frames2[nlist].values.tolist()
                    
                    gmsh.model.mesh.addElementsByType(line, common.ofem_gmsh[etype], frames2['id'].to_list(), 
                            frames2['nodes'].explode().to_list())

                    list_of_frames.append(line)

                gmsh.model.addPhysicalGroup(common.CURVE, list_of_frames, name="sec: " + sec)

        elif entities == 'materials':
            for mat in framematerials:
                framesl = frames.loc[frames['material']==mat].copy()
                line = gmsh.model.addDiscreteEntity(common.CURVE)
                gmsh.model.setEntityName(common.CURVE, line, mat)
                lst = framesl['id'].to_list()
                gmsh.model.mesh.addElementsByType(line, common.ofem_gmsh['line2'], lst, framesl['nodes'].explode().to_list())

                gmsh.model.addPhysicalGroup(common.CURVE, [line], name="frame: " + mat)

        elif entities == 'types':
            line = gmsh.model.addDiscreteEntity(common.CURVE)
            gmsh.model.setEntityName(common.CURVE, line, 'Line2')
            gmsh.model.mesh.addElementsByType(line, common.ofem_gmsh['line2'], frames['id'].to_list(), frames['nodes'].explode().to_list())
        else:
            raise ValueError('entities must be "types", "sections" or "elements"')

        # ELEMENTS - AREAS

        if entities == 'sections':
            for sec in areasections:
                areasl = areas.loc[areas['section']==sec].copy()
                surf = gmsh.model.addDiscreteEntity(common.SURFACE)
                gmsh.model.setEntityName(common.SURFACE, surf, sec)
                
                for etype in areasl['type'].unique():
                    nlist = self.mesh.get_list_node_columns(etype)
                    areas3 = areasl.loc[areasl['type'] == etype].copy()
                    areas3['nodes'] = areas3[nlist].values.tolist()
                    gmsh.model.mesh.addElementsByType(surf, common.ofem_gmsh[etype], areas3['id'].to_list(), 
                            areas3['nodes'].explode().to_list())

                gmsh.model.addPhysicalGroup(common.SURFACE, [surf], name="sec: " + sec)

        elif entities == 'elements':
            for elem in areas.itertuples():
                surf = gmsh.model.addDiscreteEntity(common.SURFACE)
                gmsh.model.setEntityName(common.SURFACE, surf, elem.element)

                etype = elem.type
                nlist = self.mesh.get_list_node_columns(etype)
                areas3 = areas.loc[areas['element'] == elem.element].copy()
                areas3['nodes'] = areas3[nlist].values.tolist()
                gmsh.model.mesh.addElementsByType(surf, common.ofem_gmsh[etype], areas3['id'].to_list(), 
                        areas3['nodes'].explode().to_list())

                gmsh.model.addPhysicalGroup(common.SURFACE, [surf], name="elm: " + elem.element)

        elif entities == 'materials':

            for mat in areamaterials:
                areasl = areas.loc[areas['material']==mat].copy()
                surf = gmsh.model.addDiscreteEntity(common.SURFACE)
                gmsh.model.setEntityName(common.SURFACE, surf, mat)

                for etype in areasl['type'].unique():
                    nlist = self.mesh.get_list_node_columns(etype)
                    areas3 = areasl.loc[areasl['type'] == etype].copy()
                    areas3['nodes'] = areas3[nlist].values.tolist()
                    gmsh.model.mesh.addElementsByType(surf, common.ofem_gmsh[etype], areas3['id'].to_list(), 
                            areas3['nodes'].explode().to_list())

                # areas3 = areasl.loc[areasl['type'] == 'area3'].copy()
                # areas3['nodes'] = areas3[['node1', 'node2', 'node3']].values.tolist()
                # gmsh.model.mesh.addElementsByType(surf, common.ofem_gmsh['area3'], areas3['id'].to_list(), 
                #         areas3['nodes'].explode().to_list())

                # areas3 = areasl.loc[areasl['type'] == 'area4'].copy()
                # areas3['nodes'] = areas3[['node1', 'node2', 'node3', 'node4']].values.tolist()
                # gmsh.model.mesh.addElementsByType(surf, common.ofem_gmsh['area4'], areas3['id'].to_list(), 
                #         areas3['nodes'].explode().to_list())

                gmsh.model.addPhysicalGroup(common.SURFACE, [surf], name="area: " + mat)

        elif entities == 'types':
            areas3 = areas.loc[areas['type'] == 'area3'].copy()
            if not areas3.empty:
                areas3['nodes'] = areas3[['node1', 'node2', 'node3']].values.tolist()
                surf = gmsh.model.addDiscreteEntity(common.SURFACE)
                gmsh.model.setEntityName(common.SURFACE, surf, 'Triangle3')
                gmsh.model.mesh.addElementsByType(surf, common.ofem_gmsh['area3'], areas3['id'].to_list(), 
                        areas3['nodes'].explode().to_list())

            areas3 = areas.loc[areas['type'] == 'area4'].copy()
            if not areas3.empty:
                areas3['nodes'] = areas3.loc[:,['node1', 'node2', 'node3', 'node4']].values.tolist()
                surf = gmsh.model.addDiscreteEntity(common.SURFACE)
                gmsh.model.setEntityName(common.SURFACE, surf, 'Quadrangle4')
                gmsh.model.mesh.addElementsByType(surf, common.ofem_gmsh['area4'], areas3['id'].to_list(), 
                        areas3['nodes'].explode().to_list())
        else:
            raise ValueError('entities must be "types", "sections" or "elements"')

        # ATTRIBUTES
        gmsh.model.setAttribute("Supports", self.supports['point'].values.tolist())
        data_list = self.supports.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        gmsh.model.setAttribute("Supports", data_list)
        data_list = self.sections.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        gmsh.model.setAttribute("Sections", data_list)
        data_list = self.materials.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        gmsh.model.setAttribute("Materials", data_list)

        return

    def to_ofem(self, mesh_file: str):
        """Writes an ofem file

        Args:
            mesh_file (str): the name of the file to be written
        """
        ndime = 3

        path = Path(mesh_file)

        jobname = str(path.parent / (path.stem + ".ofem"))
        ofem_file = OfemSolverFile(jobname, overwrite=True)
        print (f"Writing file {jobname}...")

        # nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(2, includeBoundary=True)
        # coordlist = dict(zip(nodeTags, np.arange(len(nodeTags))))
        # nodelist = dict(zip(nodeTags, np.arange(1, len(nodeTags)+1)))
        # listnode = {v: k for k, v in nodelist.items()}
        # # coords = np.array(nodeCoords).reshape(-1, 3)
        # # sorted_dict_by_keys = {key: coordlist[key] for key in sorted(coordlist)}
        # eleTypes, eleTags, eleNodes = gmsh.model.mesh.getElements(2)
        # elemlist = dict(zip(np.arange(1, 1+len(eleTags[0])), eleTags[0]))

        # prepare the database for elments and nooes base 1
        self.mesh.set_points_elems_id(1)
        self.set_indexes()

        nelems = self.mesh.num_elements
        npoints = self.mesh.num_points
        ncases = self.num_load_cases
        # materials
        nmats = self.num_materials
        mat_types = dict(self.materials['type'].value_counts())
        mat_map = dict(zip(self.materials['material'].tolist(), range(1, nmats+1)))
        # sections
        nsections = self.num_sections
        sec_types = dict(self.element_sections['section'].value_counts())
        sec_list = self.sections['section'].tolist()
        count = 0
        section_map = {}
        element_secs = {}
        iel = 0
        for elem in self.elements.itertuples():
            ielem = elem.element
            sec = self.element_sections.loc[self.element_sections['element'] == ielem, 'section'].values[0]
            mat = self.sections.loc[self.sections['section'] == sec, 'material'].values[0]
            nnode = common.ofem_nnodes[elem.type]
            key = (sec, nnode)
            if key not in section_map:
                count += 1  
                section_map[(sec, nnode)] = count
            iel += 1
            ielement = elem.id
            element_secs[ielem] = [ielement, section_map[(sec, nnode)], nnode, mat_map[mat]]
        # supports
        nspecnodes = self.num_supports
        # element types
        ntypes = dict(self.elements['type'].value_counts())
        for i, k in enumerate(dict(ntypes.items())):
            ntypes[k] = i+1
        nselp = len(ntypes)
        ndime = 3
        ele_types = [common.ofem_femix[n] for n in ntypes.keys()]

        gldatname = str(path.parent / (path.stem + ".gldat"))
        with open(gldatname, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write(self._title + "\n")

            file.write("\n")
            file.write("### Main parameters\n")
            file.write("%5d # nelem (n. of elements in the mesh)\n" % nelems)
            file.write("%5d # npoin (n. of points in the mesh)\n" % npoints)
            file.write("%5d # nvfix (n. of points with fixed degrees of freedom)\n" % nspecnodes)
            file.write("%5d # ncase (n. of load cases)\n" % ncases)
            file.write("%5d # nselp (n. of sets of element parameters)\n" % nselp)
            file.write("%5d # nmats (n. of sets of material properties)\n" % nmats)
            file.write("%5d # nspen (n. of sets of element nodal properties)\n" % nsections)
            file.write("%5d # nmdim (n. of geometric dimensions)\n" % 3)
            file.write("%5d # nnscs (n. of nodes with specified coordinate systems)\n" % 0)
            file.write("%5d # nsscs (n. of sets of specified coordinate systems)\n" % 0)
            file.write("%5d # nncod (n. of nodes with constrained d.o.f.)\n" % 0)
            file.write("%5d # nnecc (n. of nodes with eccentric connections)\n" % 0)

            file.write("\n")
            file.write("### Sets of element parameters\n")
            for i in range(nselp):
                file.write("# iselp\n")
                file.write(" %6d\n" % (i+1))
                file.write("# element parameters\n")
                file.write("%5d # ntype (n. of element type)\n" % ele_types[i][0])
                file.write("%5d # nnode (n. of nodes per element)\n" % ele_types[i][1])
                file.write("%5d # ngauq (n. of Gaussian quadrature) (stiffness)\n" % ele_types[i][3])
                file.write("%5d # ngaus (n. of Gauss points in the formulation) (stiffness)\n" % ele_types[i][4])
                file.write("%5d # ngstq (n. of Gaussian quadrature) (stresses)\n" % ele_types[i][5])
                file.write("%5d # ngstr (n. of Gauss points in the formulation) (stresses)\n" % ele_types[i][6])

            file.write("\n")
            file.write("### Sets of material properties\n")
            for mat in self.materials.itertuples():
                matn = mat.material
                imat = mat_map[matn]
                mtype = mat.type.lower()
                if mtype == "isotropic":
                    file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
                    file.write("# imats         young        poiss        dense        alpha\n")
                    file.write("  %5d  %16.8f %16.8f %16.8f %16.8f\n" % 
                        (imat, mat.young, mat.poisson, mat.weight, mat.thermal))
                elif mtype == "spring":
                    file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
                    file.write("# imats         stifn        stift-1        stift-2\n")
                    file.write("# imats         subre\n")
                    file.write("  %5d  %10.3f %10.3f %10.3f %10.3f\n" % 
                        (i+1,
                        self.materials['k'][i], 0.0, 0.0, 0.0))
                else:
                    raise ValueError("Material type not recognized")

            file.write("\n")
            file.write("### Sets of element nodal properties\n")
            for key, ispen in section_map.items():
                secname = key[0]
                nnode = key[1]
                section = self.sections.loc[secname]
                sec_type = section.type.lower()
                file.write("# ispen\n")
                file.write(" %6d\n" % ispen)
                if sec_type == "area":
                    file.write("# inode       thick\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d     %16.8f\n" % (inode, section['thick']))
                elif sec_type == "line":
                    file.write(
                        "# inode       barea        binet        bin2l        bin3l        bangl(deg)\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d     %16.8f  %16.8f  %15.8f  %16.8f %16.8f\n" % 
                            (inode, section["area"], section["torsion"],
                            section["inertia2"], section["inertia3"], section["angle"]))
                else:
                    raise ValueError("Section type not recognized")
            
            file.write("\n")
            file.write("### Element parameter index, material properties index, element nodal\n")
            file.write("### properties index and list of the nodes of each element\n")
            file.write("# ielem ielps matno ielnp       lnods ...\n")
            for element, values in element_secs.items():
                ielem = values[0]
                ielnp = values[1]
                nnode = values[2]
                matno = values[3]
                elemen = self.mesh.elements.loc[element]
                etype = elemen.type
                ielps = ntypes[etype] 
                file.write(" %6d %5d %5d %5d    " % (ielem, ielps, matno, ielnp))
                if False:
                    nodecolumnlist = self.mesh.get_list_node_columns(etype)
                    nodelist = elemen[ nodecolumnlist ]
                    for inode in range(nnode):
                        inode = nodecolumnlist[inode]
                        inode = nodelist[inode]
                        lnode = self.mesh.points.at[inode, 'id']
                        # file.write(" %8d" % eleNodes[0][count])
                        file.write(" %8d" % lnode)
                else:
                    nodelist = elemen[ self.mesh.get_list_node_columns(etype) ]
                    if len(nodelist) == 2:
                        nodea = self.mesh.points.at[nodelist['node1'], 'id'] 
                        nodeb = self.mesh.points.at[nodelist['node2'], 'id']
                        if nodea > nodeb:
                            nodea, nodeb = nodeb, nodea 
                        file.write(" %8d %8d" % (nodea, nodeb))
                    else:
                        for inode in nodelist:
                            knode = self.mesh.points.at[inode, 'id']  
                            file.write(" %8d" % knode)
                file.write("\n")

            file.write("\n")
            file.write("### Coordinates of the points\n")
            file.write("# ipoin            coord-x            coord-y            coord-z\n")
            icount = 1
            for point in self.mesh.points.itertuples():
                if icount != point.id:
                    raise ValueError("Point id not in sequence")

                if ndime == 2:
                    file.write(" %6d    %16.8lf   %16.8lf\n" % 
                        (point.id, point.x, point.y))
                else:
                    file.write(" %6d    %16.8lf   %16.8lf   %16.8lf\n" % 
                        (point.id, point.x, point.y, point.z))
                icount += 1

            file.write("\n")
            file.write("### Points with fixed degrees of freedom and fixity codes (1-fixed0-free)\n")
            file.write("# ivfix  nofix       ifpre ...\n")
            count = 1
            for fix in self.supports.itertuples():
                point = self.mesh.points.loc[fix.point].id
                file.write(" %6d %6d      " % (count, point))
                if ndime == 2:
                    file.write("%6d %6d\n" % (fix.ux, fix.uy, 0))
                else:
                    file.write("%6d %6d %6d %6d %6d %6d\n" % (fix.ux, fix.uy, fix.uz, fix.rx, fix.ry, fix.rz))
                count += 1
                
            # LOADCASES - preparing the load cases

            cases = self.get_cases()

            # LOADCASES - writing the load cases
            for i, case in enumerate(cases.keys()):
                ngrav = 1 if cases[case]["grav"] > 0 else 0
                nface = len(cases[case]["area"])
                nplod = len(cases[case]["point"])
                nudis = len(cases[case]["line"])
                ntemp = 0
                nepoi = 0
                nprva = 0
                nedge = 0

                file.write("\n")
                file.write("# ===================================================================\n")

                file.write("\n")
                file.write("### Load case n. %8d\n" % cases[case]["index"])

                file.write("\n")
                file.write("### Title of the load case\n")
                file.write(f"{case}\n")

                file.write("\n")
                file.write("### Load parameters\n")
                file.write("%5d # nplod (n. of point loads in nodal points)\n" % nplod)
                file.write("%5d # ngrav (gravity load flag: 1-yes0-no)\n" % ngrav)
                file.write("%5d # nedge (n. of edge loads) (F.E.M. only)\n" % nedge)
                file.write("%5d # nface (n. of face loads) (F.E.M. only)\n" % nface)
                file.write("%5d # ntemp (n. of points with temperature variation) (F.E.M. only)\n" % ntemp)
                file.write("%5d # nudis (n. of uniformly distributed loads (3d frames and trusses only)\n"
                            % nudis)
                file.write("%5d # nepoi (n. of element point loads) (3d frames and trusses only)\n" % nepoi)
                file.write("%5d # nprva (n. of prescribed and non zero degrees of freedom)\n" % nprva)

                # GRAVITY LOAD
                file.write("\n")
                file.write("### Gravity load (gravity acceleration)\n")
                file.write("### (global coordinate system)\n")
                file.write("#      gravi-x      gravi-y     gravi-z\n")
                if ngrav == 1:
                    file.write("    0.00000000   0.00000000  %10.8lf\n" % (cases[case]["grav"]))

                # POINT LOADS
                file.write("\n")
                file.write("### Point loads in nodal points\n")
                file.write("### (global coordinate system)\n")
                file.write("# iplod  lopop    pload-x    pload-y    pload-z");
                file.write("   pload-tx   pload-ty   pload-tz\n");
                count = 1
                for poin, values in cases[case]["point"].items():
                    file.write(" %5d %5d  " % (count, self.points.at[str(poin), 'id']))
                    file.write(" %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f" % 
                            (values[0], values[1], values[2], values[3], values[4], values[5]))
                    file.write("\n")
                    count += 1

                # FACE LOADS
                file.write("\n")
                file.write("### Face load (loaded element, loaded points and load value)\n")
                file.write("### (local coordinate system)\n")
                count = 1
                for elem, values in cases[case]["area"].items():
                    file.write("# iface  loelf\n")
                    # lixo = self.elements['element'].tolist()
                    file.write(" %6d %6d\n" % (count, self.elements.at[str(elem), 'id']))
                    file.write("# lopof     prfac-s1   prfac-s2    prfac-n  prfac-ms2  prfac-ms1\n")      
                    etype = self.elements.loc[elem].type
                    nodelist = self.elements.loc[str(elem), self.mesh.get_list_node_columns(etype)]
                    for i, inode in enumerate(nodelist):
                        file.write(" %6d" % self.mesh.points.at[inode , 'id'])
                        file.write("  %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f\n" % 
                            (values[0], values[1], values[2], 0.0, 0.0, 0.0))
                    count += 1

                # LINE LOADS
                file.write("\n")
                file.write("### Uniformly distributed load in 3d frame ")
                file.write("or truss elements (loaded element\n")
                file.write("### and load value) (local coordinate system)\n")
                file.write("# iudis  loelu    udisl-x    udisl-y    udisl-z  ")
                file.write(" udisl-tx   udisl-ty   udisl-tz\n")
                count = 1
                for elem, values in cases[case]["line"].items():
                    file.write(" %5d %5d  " % (count, self.elements.at[str(elem), 'id']))
                    file.write(" %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f\n" % 
                        (values[0], values[1], values[2], values[3], 0.0, 0.0))
                    count += 1

                # TEMPERATURE VARIATION
                file.write("\n")
                file.write("### Thermal load (loaded point and temperature variation)\n")
                file.write("# itemp  lopot     tempn\n")

                # PRESCRIBED VARIABLES
                file.write("\n")
                file.write("### Prescribed variables (point, degree of freedom and prescribed value)\n")
                file.write("### (global coordinate system)\n")
                file.write("# iprva  nnodp  ndofp    prval\n")

            file.write("\n")
            file.write("END_OF_FILE\n")
        
        # add the file .gldat to the ofem file
        ofem_file.add(gldatname)


        # # LOAD COMBINATIONS

        # combos = self.get_combos()
        # cmdatname = str(path.parent / (path.stem + ".cmdat"))

        # with open(cmdatname, 'w') as file:

        #     file.write("### Main title of the problem\n")
        #     file.write(self.title + "\n")

        #     file.write("### Number of combinations\n")
        #     file.write("%6d # ncomb (number of combinations)\n\n" % len(combos))

        #     for i, combo in enumerate(combos.keys()):
        #         file.write("### Combination title\n")
        #         file.write(combo + "\n")
        #         file.write("### Combination number\n")
        #         file.write("# combination n. (icomb) and number of load cases in combination (ncase)\n")
        #         file.write("# icomb    lcase\n")
        #         file.write(" %6d   %6d\n" % (i+1, len(combos[combo]['coefs'])))
        #         file.write("### Coeficients\n")
        #         file.write("# load case number (icase) and load coefficient (vcoef)\n")
        #         file.write("# icase      vcoef\n")
        #         for icase, coef in combos[combo]['coefs'].items():
        #             file.write(" %6d  %10.3f\n" % (cases[icase]['index'], coef))
        #         file.write("\n")

        #     file.write("END_OF_FILE\n")

        # ofem_file.add(cmdatname)

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
            self._mesh = mesh
        return

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._mesh._title = title

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
    
    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, groups):
        self._groups = groups
        return

    @property
    def file_name(self):
        return self._filename

    @property
    def title(self):
        return self._title

    @property
    def file_name(self):
        return self._filename
        
    @file_name.setter
    def file_name(self, filename: str):
        path = Path(filename)
        self._filename = str(path.parent / path.stem)
        return

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


class xdfemData:
    def __init__(self) -> None:
        self._collection = {}

    def add(self, name: str, data: pd.DataFrame):
        """_summary_

        Args:
            name (str): _description_
            data (pd.DataFrame): _description_
        """
        self._collection[name] = data
        return

    def remove(self, name: str):
        if name in self._collection.keys():
            self._collection.pop(name)
        return

    def read_xdfem(self, filename: str): 
        path = Path(filename)
        if path.suffix != ".xdfem":
            raise ValueError(f"File {filename} is not a .xfem file")

        with zipfile.ZipFile(filename, 'r') as zip_file:
            with zip_file.open('data.json') as json_file:
                data = json.load(json_file)
                self._from_dict(data)

        self._dirty = [True for i in range(NTABLES)]
        return

    def read(self, filename: str, file_format: str = None):
        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xdfem":
            self.read_xdfem(filename)
        else:
            raise ValueError(f"File format {file_format} not recognized")
        return

    def save(self, filename: str, file_format: str = None):
        path = Path(filename)
        
        if path.suffix == "" and file_format == None:
            raise ValueError(f"File format not recognized")

        if file_format == None:
            file_format = Path(filename).suffix

        if file_format == ".xlsx":
            self.write_excel(filename)
        elif file_format == ".xdfem":
            self.write_xdfem(filename)
        else:
            raise ValueError(f"File format {file_format} not recognized")

        return

    def write_excel(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xlsx":
            filename = path.with_suffix(".xlsx")

        with pd.ExcelWriter(filename) as writer:
            for key, df in self._collection.items():
                df.to_excel(writer, sheet_name=key, index=False)

        return

    def write_xdfem(self, filename: str):
        path = Path(filename)
        if path.suffix != ".xdfem":
            filename = path.with_suffix(".xdfem")

        files = self._to_dict()
        json_data = json.dumps(files, indent=2).replace('NaN', 'null')
        # with open(filename+'.json', 'w') as f:
        #     f.write(json_data)

        # Create an in-memory buffer
        json_buffer = io.BytesIO(json_data.encode('utf-8'))
        # Reset buffer position to the beginning
        json_buffer.seek(0)
        # Create a ZIP file in-memory and add the JSON buffer
        if path.exists():
            replace_bytesio_in_zip(filename, 'data.json', json_buffer.read().decode('utf-8'))
        else:
            with zipfile.ZipFile(filename, 'w') as zip_file:
                zip_file.writestr('data.json', json_buffer.read().decode('utf-8'))    

        return
    
    def _to_dict(self):
        return {
            key: df.to_dict(orient="records") for key, df in self._collection.items()
        }

    def _from_dict(self, ofem_dict: dict):
        for key, value in ofem_dict.items():
            json_buffer = io.BytesIO(json.dumps(value).encode())
            json_buffer.seek(0)
            self._collection[key] = pd.read_json(json_buffer, orient='records')
        return

    @property
    def items(self):
        return self._collection
