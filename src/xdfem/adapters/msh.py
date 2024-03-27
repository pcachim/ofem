import gmsh
import numpy as np
import pandas as pd
import pathlib
from pathlib import Path
import json, io
from .. import common
from .. import xfemmesh

class Reader:

    def __init__(self, filename: str):
        self.tables = {}  # SAP2000 S2K file database
        path = pathlib.Path(filename)
        self._filename = str(path.parent / path.stem)
        if not path.suffix == ".msh":
            raise ValueError("File extension not supported")
        
        self._filename = str(path.parent / path.stem)
        gmsh.initialize()
        self._msh = gmsh.open(self._filename + ".msh")
        return

    def to_ofem_struct(self):
        
        # Read general mesh information
        nodeTags = gmsh.model.mesh.getNodes()
        elementTypes, elementTags, elementNodeTags = gmsh.model.mesh.getElements()
        physicalGroups = gmsh.model.getPhysicalGroups()
        attributes = gmsh.model.getAttributeNames()

        self.ofem = xfemmesh.xfemStruct(gmsh.model.get_file_name())
        self.ofem.file_name = self._filename
        
        # POINTS
        coordinates = {
            "point": nodeTags[0],
            "x": nodeTags[1][0::3],
            "y": nodeTags[1][1::3],
            "z": nodeTags[1][2::3]
        }
        self.ofem.points = pd.DataFrame(coordinates)
        self.ofem.points["point"] = self.ofem.points["point"].astype(str)

        # ELEMENTS
        for i, etype in enumerate(elementTypes):
            if etype not in common.gmsh_ofem:
                raise ValueError("Element type not supported")
            
            if etype == 15: # 'point'
                continue
            
            ofem_etype = common.gmsh_ofem[etype]
            ofem_nnodes = common.ofem_nnodes[ofem_etype]
            nelem = len(elementTags[i])
            elements = {f"node{j+1}": elementNodeTags[i][j::ofem_nnodes] for j in range(0, ofem_nnodes)}
            elements["element"] = np.array(elementTags[i])
            df = pd.DataFrame(elements)
            # df["element"] = df["element"].astype(str)
            cols = ["element"] + [col for col in df.columns if col.startswith('node')]
            df[cols] = df[cols].astype(str)
            df.loc[:, 'element'] = common.ofem_basic[ofem_etype] + '-' + df.loc[:,['element']]
            df['type'] = ofem_etype
            self.ofem.elements = pd.concat([self.ofem.elements, df])

        # SECTIONS, SUPPORTS
        for phys in physicalGroups:
            dim = phys[0]
            tag = phys[1]
            physName = gmsh.model.getPhysicalName(dim, tag)
            if physName.startswith("sec:") and dim > 0:
                secName = physName.split(":")[1].strip()
                entities = gmsh.model.get_entities_for_physical_group(dim, tag)
                elements = [gmsh.model.mesh.getElements(dim, i) for i in entities]
                elements =[np.array(elements[i][1]) for i in range(len(elements))]
                elements = np.concatenate(elements, axis=None).tolist()
                df = pd.DataFrame({'element': elements})
                df['element'] = df['element'].astype(str)
                df['section'] = secName
                df.loc[:, 'element'] = common.gmsh_ofem_types[dim] + '-' + df.loc[:,['element']]
                self.ofem.element_sections = pd.concat([self.ofem.element_sections, df])
                ### verificar com vários tipos de elementos e entities

            if physName.startswith("sup:"):
                supCode = physName.split(":")[1].strip()
                digit_list = [int(digit) for digit in supCode]
                entities = gmsh.model.get_entities_for_physical_group(dim, tag)
                points = [gmsh.model.mesh.getNodes(dim, i) for i in entities]
                points = [np.array(points[i][0]) for i in range(len(points))]
                df = pd.DataFrame({'point': np.array(points).flatten()})
                df['point'] = df['point'].astype(str)
                df.loc[:, ['ux', 'uy', 'uz', 'rx', 'ry', 'rz']] = digit_list
                self.ofem.supports = pd.concat([self.ofem.supports, df])
                ### verrificar se há nós repetidos

        # SECTION PROPERTIES
        if "Sections" in attributes:
            sections = gmsh.model.get_attribute("Sections")
            _list = [json.loads(sec.replace("'", "\"")) for sec in sections]

            json_buffer = io.BytesIO(json.dumps(_list).encode())
            json_buffer.seek(0)
            df = pd.read_json(json_buffer, orient='records')
            self.ofem.sections = pd.concat([self.ofem.sections, df])
        
        # MATERIAL PROPERTIES
        if "Materials" in attributes:
            materials = gmsh.model.get_attribute("Materials")
            _list = [json.loads(sec.replace("'", "\"")) for sec in materials]

            json_buffer = io.BytesIO(json.dumps(_list).encode())
            json_buffer.seek(0)
            df = pd.read_json(json_buffer, orient='records')
            self.ofem.materials = pd.concat([self.ofem.materials, df])

        # LOAD CASES
        if "LoadCases" in attributes:
            loadCases = gmsh.model.get_attribute("LoadCases")
            _list = [json.loads(sec.replace("'", "\"")) for sec in loadCases]

            json_buffer = io.BytesIO(json.dumps(_list).encode())
            json_buffer.seek(0)
            df = pd.read_json(json_buffer, orient='records')
            self.ofem.load_cases = pd.concat([self.ofem.load_cases, df])
        
        # POINT LOADS
        if "PointLoads" in attributes:
            pointLoads = gmsh.model.get_attribute("PointLoads")
            _list = [json.loads(sec.replace("'", "\"")) for sec in pointLoads]

            json_buffer = io.BytesIO(json.dumps(_list).encode())
            json_buffer.seek(0)
            df = pd.read_json(json_buffer, orient='records')
            self.ofem.point_loads = pd.concat([self.ofem.point_loads, df])

        # LINE LOADS
        ### buscar os elementos na tabela de entidades
        if "LineLoads" in attributes:
            lineLoads = gmsh.model.get_attribute("LineLoads")
            _list = [json.loads(sec.replace("'", "\"")) for sec in lineLoads]
            
            for i, sec in enumerate(_list):
                tag = int(sec['element'])
                elems = gmsh.model.mesh.getElements(1, tag)[1][0].tolist()
                df = pd.DataFrame({'element': elems})
                df["element"] = df["element"].astype(str)
                df['direction'] = 'local'
                df.loc[:, 'element'] = common.gmsh_ofem_types[1] + '-' + df.loc[:,['element']]
                for key in ['loadcase', 'fx', 'fy', 'fz', 'mx']:
                    df[key] = sec[key]                
                self.ofem.line_loads = pd.concat([self.ofem.line_loads, df])

        # AREA LOADS
        if "AreaLoads" in attributes:
            areaLoads = gmsh.model.get_attribute("AreaLoads")
            _list = [json.loads(sec.replace("'", "\"")) for sec in areaLoads]
            
            for i, sec in enumerate(_list):
                tag = int(sec['element'])
                elems = gmsh.model.mesh.getElements(2, tag)[1][0].tolist()
                df = pd.DataFrame({'element': elems})
                df["element"] = df["element"].astype(str)
                df['direction'] = 'local'
                df.loc[:, 'element'] = common.gmsh_ofem_types[2] + '-' + df.loc[:,['element']]
                for key in ['loadcase', 'px', 'py', 'pz']:
                    df[key] = sec[key]                
                self.ofem.area_loads = pd.concat([self.ofem.area_loads, df])

        # GROUPS
        # entities = gmsh.model.getEntities()
        # for ent in entities:
        #     dim = ent[0]
        #     tag = ent[1]
        #     name = gmsh.model.getEntityName(dim, tag)
        #     if name.startswith("grp:"):
        #         grpName = name.split(":")[1].strip()
        #         entities = gmsh.model.get_entities_for_group(tag)
        #         elements = [gmsh.model.mesh.getElements(dim, i) for i in entities]
        #         elements =[np.array(elements[i][1]) for i in range(len(elements))]
        #         elements = np.concatenate(elements, axis=None).tolist()
        #         df = pd.DataFrame({'element': elements})
        #         df['element'] = df['element'].astype(str)
        #         df['group'] = grpName
        #         df.loc[:, 'element'] = common.gmsh_ofem_types[dim] + '-' + df.loc[:,['element']]
        #         self.ofem.groups = pd.concat([self.ofem.groups, df])
        #         ### verificar com vários tipos de elementos e entities
        return self.ofem
