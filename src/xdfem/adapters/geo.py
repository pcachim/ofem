import gmsh
import numpy as np
import pandas as pd
import shutil, os
from pathlib import Path
import json, io
import zipfile
from .. import common
from .. import xfemmesh
from .. import replace_bytesio_in_zip

dim_types = {
    0: 'point',
    1: 'line',
    2: 'area',
    3: 'solid',
}

class xdgeo:
    
    def __init__(self, filename: str):
        self.tables = {}  # SAP2000 S2K file database
        path = Path(filename)
        self._filename = str(path.parent / path.stem)
        self._path = path.parent
        if not path.suffix == ".xdgeo":
            raise ValueError("File extension not supported")

        self._filename = str(path.parent / path.stem)

        self._attributes = {}
        # Extracts the .json file from .xdgeo file
        fname = str(self._filename + ".xdgeo")
        with zipfile.ZipFile(fname, 'r') as zip_file:
            with zip_file.open('attributes.json') as json_file:
                self._attributes = json.load(json_file)

            # Extract the geometry.geo file
            zip_file.extract(str("geometry.geo"), self._path)

        # Opens the .geo file in gmsh
        gmsh.initialize()
        fname = str(path.parent / "geometry.geo")
        gmsh.open(fname)

        # Deletes the .geo file
        os.remove(fname)
        
        # gmsh.fltk.run()
        return

    @property
    def attributes(self):
        return self._attributes
    
    def to_gmsh_geo(self, model: xfemmesh.xdfemStruct, meshsize: float = 100000):
        """Writes a .xdgeo file with each mesh element as an entity. 
        If the file exists, replace the contents of the file. If the file does not exists, creates a new one

        Args:
            model (xfemmesh.xdfemStruct): the structural model
            meshsize (float, optional): a number that specifies the mesh size.
        """

        model.set_indexes()
        model.mesh.set_points_elems_id(1)

        joints = model.mesh.points.copy()
        frames = model.mesh.elements.loc[model.mesh.elements['type'].isin(common.ofem_lines)].copy()
        for etype in frames['type'].unique():
            nlist = model.mesh.get_list_node_columns(etype)
            for col in nlist:
                frames[col] = joints.loc[frames[col].values, 'id'].values
            frames['nodes'] = frames[nlist].values.tolist()

        frames.loc[:,'section'] = model.element_sections.loc[:,'element'].apply(
            lambda x: model.element_sections.at[x, 'section']
            )
        frames.loc[:,'material'] = frames.loc[:,'section'].apply(
            lambda x: model.sections.at[x, 'material']
            )
        framesections = frames['section'].unique()
        framematerials = frames['material'].unique()

        areas = model.mesh.elements.loc[model.mesh.elements['type'].isin(common.ofem_areas)].copy()
        for col in areas.columns:
            if not col.startswith('node'):
                continue
            areas[col] = joints.loc[areas[col].values, 'id'].values
        areas.loc[:,'section'] = model.element_sections.loc[:,'element'].apply(
            lambda x: model.element_sections.at[x, 'section']
            )
        areas.loc[:,'material'] = areas.loc[:,'section'].apply(
            lambda x: model.sections.at[x, 'material']
            )
        areasections = areas['section'].unique()
        areamaterials = areas['material'].unique()

        # JOINTS
        # max_values = joints[['x', 'y', 'z']].max()
        # min_values = joints[['x', 'y', 'z']].max()
        
        supps = model.supports
        supps['point'] = supps['point'].astype(str)
        supps['joined'] = supps[['ux', 'uy', 'uz', 'rx', 'ry', 'rz']].apply(lambda x: ''.join(map(str, x)), axis=1)
        supp_types = supps['joined'].unique()
        supp_nodes = supps['point'].values.tolist()

        joins_name_id = joints.set_index('point')['id'].to_dict()
        joins_name_id = [{key: value} for key, value in joins_name_id.items()]

        # add free nodes
        joints['point'] = joints['id'].astype(str)
        free_nodes = joints[~joints['point'].isin(supp_nodes)].copy()
        list_of_nodes = []
        for node in free_nodes.itertuples():
            gmsh.model.geo.addPoint(node.x, node.y, node.z, meshSize=meshsize, tag=node.id)
            list_of_nodes.append(node.id)
            gmsh.model.geo.synchronize()
            gmsh.model.mesh.addNodes(common.POINT, node.id, [node.id], [node.x, node.y, node.z])

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
                gmsh.model.mesh.addNodes(common.POINT, node.id, [node.id], [node.x, node.y, node.z])

            gmsh.model.geo.addPhysicalGroup(common.POINT, list_of_nodes, name="sup: " + sup_type)
            
        # phy = gmsh.model.getPhysicalGroups()

        # ELEMENTS - FRAMES
        logging.info(f"Processing frames ({model.mesh.num_elements})...")

        # Adds each element as separate entity grouped by physical sections
        frames_dict = frames.set_index('element')['id'].to_dict()
        for sec in framesections:
            secframes = pd.DataFrame(frames.loc[frames['section']==sec])

            list_of_frames = []
            for elem in secframes.itertuples():
                tag = gmsh.model.geo.addLine(elem.node1, elem.node2, elem.id)                
                gmsh.model.geo.synchronize()
                list_of_frames.append(elem.id)

                etype = elem.type
                gmsh.model.mesh.addElementsByType(tag, common.ofem_gmsh[etype], [elem.id], elem.nodes)

            gmsh.model.addPhysicalGroup(common.CURVE, list_of_frames, name="sec: " + sec)

        # ELEMENTS - AREAS

        areas_dict = areas.set_index('element')['id'].to_dict()
        for sec in areasections:
            secareas = areas.loc[areas['section']==sec].copy()

            list_of_areas = []
            for i, elem in secareas.iterrows():
                etype = elem['type']
                nlist = model.mesh.get_list_node_columns(etype)
                line_bound = []
                for i in range(len(nlist)):
                    tag = gmsh.model.geo.addLine(elem[nlist[i]], elem[nlist[(i+1)%len(nlist)]])
                    line_bound.append(tag)
                
                bound = gmsh.model.geo.addCurveLoop(line_bound, tag=elem.id)
                gmsh.model.geo.addPlaneSurface([bound], tag=elem.id)
                
                # new 
                gmsh.model.geo.synchronize()
                gmsh.model.mesh.addElementsByType(bound, common.ofem_gmsh[etype], [elem.id], elem[nlist].values.tolist()  )

                list_of_areas.append(elem.id)

            gmsh.model.geo.synchronize()
            gmsh.model.addPhysicalGroup(common.SURFACE, list_of_areas, name="sec: " + sec)

        elems_name_id = frames_dict | areas_dict
        elems_name_id = [{key: value} for key, value in elems_name_id.items()]
        
        # ATTRIBUTES
        attrbs = model.to_dict()
        for key in attrbs:
            s = [str(value) for value in attrbs[key]]
            gmsh.model.set_attribute(key, s)

        s = [str(value) for value in joins_name_id]
        gmsh.model.set_attribute("joints_name_id", s)
        s = [str(value) for value in elems_name_id]
        gmsh.model.set_attribute("elements_name_id", s)

        # data_list = model.supports.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        # gmsh.model.setAttribute("Supports", data_list)
        # data_list = model.sections.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        # gmsh.model.setAttribute("Sections", data_list)
        # data_list = model.materials.apply(lambda row: ', '.join(map(str, row)), axis=1).tolist()
        # gmsh.model.setAttribute("Materials", data_list)

        gmsh.model.geo.synchronize()
        # gmsh.model.mesh.generate(1)
        # gmsh.model.mesh.generate(2)
        # gmsh.fltk.run()

        # SAVE geo
        filename = self._filename + ".xdgeo"
        gmsh.write("geometry.geo_unrolled")
        shutil.copy("geometry.geo_unrolled", "geometry.geo")
        os.remove("geometry.geo_unrolled")

        files = self._to_dict()
        json_data = json.dumps(files, indent=2).replace('NaN', 'null')

        # Create an in-memory buffer
        json_buffer = io.BytesIO(json_data.encode('utf-8'))
        # Reset buffer position to the beginning
        json_buffer.seek(0)
        # Create a ZIP file in-memory and add the JSON buffer
        if path.exists():
            replace_bytesio_in_zip(filename, 'geometry.geo', json_buffer.read().decode('utf-8'))
        else:
            with zipfile.ZipFile(filename, 'w') as zip_file:
                zip_file.write(filename, 'geometry.geo')    

        return

    def to_xdfem(self, meshsize: float = 100000) -> xfemmesh.xdfemStruct:
        """Reads a .xdgeo geometry file and converts it to a xdfemstruct model.

        Args:
            meshsize (float, optional): a number that specifies the mesh size.
        Returns:
            xfemmesh.xdfemStruct: the structural model
        """
        model = xfemmesh.xdfemStruct()

        return model

    def to_xdgeo(self):
        
        # Read general mesh information
        nodeTags = gmsh.model.mesh.getNodes()
        elementTypes, elementTags, elementNodeTags = gmsh.model.mesh.getElements()
        physicalGroups = gmsh.model.getPhysicalGroups()
        attributes = gmsh.model.getAttributeNames()

        self.ofem = xfemmesh.xdfemStruct(gmsh.model.get_file_name())
        self.ofem.file_name = self._filename

        # NAMES and IDs
        elements_name_id = {}
        for d in gmsh.model.get_attribute("elements_name_id"):
            elements_name_id.update(json.loads(d.replace("'", "\"")))
        joints_name_id = {}
        for d in gmsh.model.get_attribute("joints_name_id"):
            joints_name_id.update(json.loads(d.replace("'", "\"")))

        # POINTS
        coordinates = {
            "point": nodeTags[0],
            "id": nodeTags[0],
            "x": nodeTags[1][0::3],
            "y": nodeTags[1][1::3],
            "z": nodeTags[1][2::3]
        }
        self.ofem.points = pd.DataFrame(coordinates)
        self.ofem.points['point'] = self.ofem.points["id"].copy().astype(str)
        if len(joints_name_id) > 0:
            joins_id_name = {int(value): str(key) for key, value in joints_name_id.items()}
            self.ofem.points['point'] = self.ofem.points['id'].map(joins_id_name)
        else:
            joints_name_id = dict(zip(coordinates['point'], coordinates['id']))
            joins_id_name = {int(value): str(key) for key, value in joints_name_id.items()}
            
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
            elements["id"] = np.array(elementTags[i])
            df = pd.DataFrame(elements)

            cols = ["element"] + [col for col in df.columns if col.startswith('node')]
            df[cols] = df[cols].astype(str)
            df.loc[:, 'element'] = common.ofem_basic[ofem_etype] + '-' + df.loc[:,['element']]
            df['type'] = ofem_etype
            self.ofem.elements = pd.concat([self.ofem.elements, df])

        self.ofem.elements["element"] = self.ofem.elements["element"].astype(str)
        if len(elements_name_id) > 0:
            elements_id_name = {int(value): str(key) for key, value in elements_name_id.items()}
            self.ofem.elements['element'] = self.ofem.elements['id'].map(elements_id_name)
        else:
            elements_name_id = dict(zip(self.ofem.elements['element'].values, self.ofem.elements['id'].values))
            elements_id_name = {int(value): str(key) for key, value in elements_name_id.items()}
        
        joints_name_id = {str(key): int(value) for key, value in joints_name_id.items()}
        elements_name_id = {str(key): int(value) for key, value in elements_name_id.items()}
        
        # SECTIONS, SUPPORTS, GROUPS
        for phys in physicalGroups:
            dim = phys[0]
            tag = phys[1]
            physName = gmsh.model.getPhysicalName(dim, tag)
            if physName.startswith("sec:") and dim > 0:
                secName = physName.split(":")[1].strip()
                entities = gmsh.model.get_entities_for_physical_group(dim, tag)
                elements = [gmsh.model.mesh.getElements(dim, i) for i in entities]
                elements = [np.array(elements[i][1]) for i in range(len(elements))]
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

            if physName.startswith("grp:"):
                pass
                grpName = physName.split(":")[1].strip()
                # digit_list = [int(digit) for digit in supCode]
                entities = gmsh.model.get_entities_for_physical_group(dim, tag)

                elements = [gmsh.model.mesh.getElements(dim, i) for i in entities]
                elements = [np.array(elements[i][1]) for i in range(len(elements))]
                elements = np.concatenate(elements, axis=None).tolist()
                df = pd.DataFrame({dim_types[dim]: elements})
                df[dim_types[dim]] = df[dim_types[dim]].astype(str)
                df['group'] = grpName
                df.loc[:, 'element'] = common.gmsh_ofem_types[dim] + '-' + df.loc[:,[dim_types[dim]]]
                self.ofem.groups = pd.concat([self.ofem.groups, df])

                points = [gmsh.model.mesh.getNodes(dim, i) for i in entities]
                points = [np.array(points[i][0]) for i in range(len(points))]
                df = pd.DataFrame({'point': np.array(points).flatten()})
                df['point'] = df['point'].astype(str)
                df['group'] = grpName
                self.ofem.groups = pd.concat([self.ofem.groups, df])

        # SECTION PROPERTIES
        if "sections" in attributes:
            sections = gmsh.model.get_attribute("sections")
            _list = []
            for sec in sections:
                s = sec.replace("'", "\"")
                s = s.replace("nan", "0.0")
                # if not s.startswith('"'):
                #         s = f'"{s}"'
                _list.append(json.loads(s))
            # _list = [json.loads(sec.replace("'", "\"")) for sec in sections]

            json_buffer = io.BytesIO(json.dumps(_list).encode())
            json_buffer.seek(0)
            df = pd.read_json(json_buffer, orient='records')
            self.ofem.sections = pd.concat([self.ofem.sections, df])
        
        # MATERIAL PROPERTIES
        if "materials" in attributes:
            materials = gmsh.model.get_attribute("materials")
            _list = [json.loads(sec.replace("'", "\"")) for sec in materials]

            json_buffer = io.BytesIO(json.dumps(_list).encode())
            json_buffer.seek(0)
            df = pd.read_json(json_buffer, orient='records')
            self.ofem.materials = pd.concat([self.ofem.materials, df])

        # LOAD CASES
        if "loadcases" in attributes:
            loadCases = gmsh.model.get_attribute("loadcases")
            _list = [json.loads(sec.replace("'", "\"")) for sec in loadCases]

            json_buffer = io.BytesIO(json.dumps(_list).encode())
            json_buffer.seek(0)
            df = pd.read_json(json_buffer, orient='records')
            self.ofem.load_cases = pd.concat([self.ofem.load_cases, df])
        
        # POINT LOADS
        if "pointloads" in attributes:
            pointLoads = gmsh.model.get_attribute("pointloads")
            _list = [json.loads(sec.replace("'", "\"")) for sec in pointLoads]

            json_buffer = io.BytesIO(json.dumps(_list).encode())
            json_buffer.seek(0)
            df = pd.read_json(json_buffer, orient='records')
            self.ofem.point_loads = pd.concat([self.ofem.point_loads, df])

        # LINE LOADS
        ### buscar os elementos na tabela de entidades
        if "lineloads" in attributes:
            lineLoads = gmsh.model.get_attribute("lineloads")
            _list = [json.loads(sec.replace("'", "\"")) for sec in lineLoads]

            for i, sec in enumerate(_list):
                tag = elements_name_id[sec['element']]
#                 tag = int(sec['element'])
                elems = gmsh.model.mesh.getElements(1, tag)[1][0].tolist()
                df = pd.DataFrame({'element': elems})
                df["element"] = df["element"].astype(str)
                df['direction'] = 'local'
                df.loc[:, 'element'] = common.gmsh_ofem_types[1] + '-' + df.loc[:,['element']]
                for key in ['loadcase', 'fx', 'fy', 'fz', 'mx']:
                    df[key] = sec[key]                
                self.ofem.line_loads = pd.concat([self.ofem.line_loads, df])

        # AREA LOADS
        if "arealoads" in attributes:
            areaLoads = gmsh.model.get_attribute("arealoads")
            _list = [json.loads(sec.replace("'", "\"")) for sec in areaLoads]
            
            for i, sec in enumerate(_list):
                tag = elements_name_id[sec['element']]
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
        #     group_name = f'ent: {dim}:{tag}'
        #     type_name = common.gmsh_ofem_types[dim]
            
        #     elementTypes, elementTags, nodeTags = gmsh.model.mesh.getElements(dim, tag)

        #     df = pd.DataFrame({type_name: np.array(elementTags[i])})
        #     df[type_name] = df[type_name].astype(str)
        #     if dim > 0:
        #         df.loc[:, type_name] = type_name + '-' + df.loc[:,[type_name]]
        #     df['group'] = group_name
            
        #     self.ofem.groups = pd.concat([self.ofem.groups, df])

        return self.ofem


        filename = self._filename
        gmsh.write(str(filename) + ".geo_unrolled")
        shutil.copy(str(filename) + ".geo_unrolled", str(filename) + ".geo")
        os.remove(str(filename) + ".geo_unrolled")

        path = Path(filename)
        if path.suffix != ".xdfem":
            filename = path.with_suffix(".xdfem")

        files = self._to_dict()
        json_data = json.dumps(files, indent=2).replace('NaN', 'null')

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