import meshio
import gmsh
import openpyxl
import numpy as np
import pandas as pd
import copy
import zipfile
import json
import logging
import timeit
from numpy.typing import ArrayLike
from pathlib import Path
from .common import *

class ofem_handler:

    def __init__(self):
        self._points: pd.DataFrame = pd.DataFrame(columns=['tag', 'numtag', 'x', 'y', 'z'])
        self.points: dict = {}
        self._elements: pd.DataFrame = pd.DataFrame(columns=['tag', 'numtag', 'type', 'nnodes', 'nodes', 'section', 'group'])
        self._info: dict = {}
        self._specialnodes: pd.DataFrame  = pd.DataFrame(columns=['tag', 'node', 'fixed'])
        self._types: list = []
        self._framesections: list = []
        self._areasections: list = []
        self._materials: list = []
        self._pointloads: list = []
        self._frameloads: list = []
        self._arealoads: list = []
        self._solidloads: list = []
        self._combinations: list = []
        self_gmsh = None

    def add_points(self, newpoints: dict):
        self.points.update(newpoints)
        return

    def read_mesh(self, mesh_file):
        self._mesh = meshio.read(mesh_file)
        return self._mesh

    def write_mesh(self, mesh_file, mesh):
        # Prepare some data
        data: dict = {
            "common_name": "Brongersma's short-tailed python",
            "scientific_name": "Python brongersmai",
            "length": 290
        }

        with zipfile.ZipFile("compressed_data.zip", mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file: 
            # Dump JSON data
            dumped_JSON: str = json.dumps(data, ensure_ascii=False, indent=4)
            # Write the JSON data into `data.json` *inside* the ZIP file
            zip_file.writestr("data.json", data=dumped_JSON)
            # Test integrity of compressed archive
            zip_file.testzip()

        return mesh_file

    def import_mesh(self, mesh_file: str, mesh_format: str="gmsh"):
        path = Path(mesh_file)
        file = path.stem
        sufffix = path.suffix.lower()

        if mesh_format == "gmsh" or sufffix == ".msh":
            # gmsh.initialize()
            # self._gmsh = gmsh.open(mesh_file)
            mesh = meshio.read(mesh_file)

            self._points = pd.DataFrame(mesh.points, np.arange(len(mesh.points)), ['x', 'y', 'z'])
            self._points['tag'] = np.arange(len(mesh.points))
            self._info['npoints'] = len(self._points)

            #self._elements: pd.DataFrame = pd.DataFrame(columns=['nodes', 'dtype'])
            isection = 0
            imaterial = 0
            for m in mesh.cells:
                if m.type == 'vertex':
                    newrow = pd.DataFrame({'node': list(m.data)})
                    self._specialnodes = pd.concat([self._specialnodes, newrow])
                else:
                    newrow = pd.DataFrame({'nodes': list(m.data)})
                    newrow['dtype'] = m.type
                    newrow['section type'] = meshio_sections[m.type]
                    newrow['type'] = meshio_femix[m.type][0]
                    newrow['nnodes'] = meshio_femix[m.type][1]
                    newrow['nodals'] = meshio_femix[m.type][2]
                    newrow['gtype'] = int(meshio_gmsh[m.type])
                    newrow['group'] = 'all'

                    if meshio_femix[m.type][2] != 0:     
                        isection += 1
                        ksection = isection
                        self._sections.append(meshio_sections[m.type])
                    else:
                        ksection = -1
                        
                    if m.type == 'line':
                        for row in newrow.itertuples():
                            node1 = row.nodes[0]
                            node2 = row.nodes[1]
                            if node1 > node2:
                                newrow.at[row.Index, 'nodes'][0] = node2 
                                newrow.at[row.Index, 'nodes'][1] = node1
                    
                    newrow['section'] = ksection
                    imaterial += 1
                    self._materials.append(meshio_sections[m.type])
                    newrow['material'] = imaterial
                    self._types.append(meshio_femix[m.type])
                    self._elements = pd.concat([self._elements, newrow])

            self._specialnodes['tag'] = np.arange(1, len(self._specialnodes)+1)
            self._elements['tag'] = np.arange(1, len(self._elements)+1)
            self._elements['group'] = 'all'
            self._elements[['gtype', 'nodals']] = self._elements[['gtype', 'nodals']].astype('int32')
            print (self._elements)

            self._info['filename'] = mesh_file
            self._info['foldername']  = path.parent
            self._info['jobname']  = path.stem
            self._info['title'] = file
            self._info['nelems'] = len(self._elements)
            self._info['nsections'] = isection
            self._info['nmats'] = imaterial
            self._info['nspecnodes'] = len(self._specialnodes)

            # gmsh.finalize()
        return

    @property
    def npoints(self):
        return self._info['npoints']
    
    @property
    def nelems(self):
        return self._info['nelems']
    
    @property
    def nsections(self):
        return self._info['nsections']
    
    @property
    def nmats(self):
        return self._info['nmats']
    
    @property
    def nspecnodes(self):
        return self._info['nspecnodes']

    def get_mesh(self):
        return self._mesh

    def set_mesh(self, mesh):
        self._mesh = mesh
        return self._mesh

    def get_mesh_points(self):
        return self._mesh.points

    def get_mesh_cells(self):
        return self._mesh.cells
    
    def read_gmsh(self, mesh_file: str):
        pass

    def read_excel(self, mesh_file: str):
        pass

    def read_json(self, mesh_file: str):
        pass

    def read_gldat(self, mesh_file: str):
        pass

    def to_gmsh(self, mesh_file: str):
        """Writes a GMSH mesh file

        Args:
            mesh_file (str): the name of the file to be written
        """
        file = Path(mesh_file)
        if file.suffix.lower() != ".msh":
            mesh_file = file.with_suffix('').resolve() + ".msh"

        # initialize gmsh
        gmsh.initialize()
        
        gmsh.model.add(self._info['title'])

        # joints = self._points
        # elems = self._elements
        # areas = self._areas
        # groups = self._groups
        
        # try:
        #     sect = self.s2kDatabase['Frame Props 01 - General'.upper()]
        # except:
        #     sect = self.s2kDatabase['Frame Section Properties 01 - General'.upper()]
        # sectassign = self.s2kDatabase['Frame Section Assignments'.upper()]
        # areasect = self.s2kDatabase['Area Section Properties'.upper()]
        # areaassign = self.s2kDatabase['Area Section Assignments'.upper()]
        # groups = self.s2kDatabase['Groups 1 - Definitions'.upper()]
        # groupsassign = self.s2kDatabase['Groups 2 - Assignments'.upper()]
        
        # logging.basicConfig(level=logging.DEBUG)
        # logging.debug("Writing GMSH file: %s", mesh_file)
            
        # # prepares the GMSH model
        # njoins = joints.shape[0]
        # logging.info(f"Processing nodes ({njoins})...")
        # ijoins = np.arange(1, njoins+1)
        # joints.insert(0, "JoinTag", ijoins, False)
        # joints['Joint'] = joints['Joint'].map(str)
        # joints['Joint2'] = joints.loc[:, 'Joint']
        # joints.set_index('Joint', inplace=True)
        # joints['coord'] = joints.apply(lambda x: np.array([x['XorR'], x['Y'], x['Z']]),axis=1) 
        # lst1 = joints['coord'].explode().to_list()

        # line = gmsh.model.addDiscreteEntity(POINT)
        # gmsh.model.mesh.addNodes(POINT, line, ijoins, lst1)

        # nelems = elems.shape[0]
        # logging.info(f"Processing frames ({nelems})...")
        # elems.insert(1, "ElemTag", np.arange(1, nelems+1), False)
        # elems.insert(2, "Section", sectassign['AnalSect'].values, False)
        # elems[['Frame', 'JointI', 'JointJ']] = elems[['Frame', 'JointI', 'JointJ']].astype(str)
        
        # elems['Nodes'] = elems.apply(
        #     lambda row: rename_elem_nodes(joints, row['ElemTag'], row["JointI"],row["JointJ"]), 
        #     axis=1
        #     )

        # starttime = timeit.default_timer()

        # nelems = areas.shape[0]
        # logging.info(f"Processing ares ({nelems})...")
        # areas.insert(1, "ElemTag", np.arange(1, nelems+1), False)
        # areas.insert(2, "Section", areaassign['Section'].values, False)
        # areas[['Area','Joint1','Joint2','Joint3','Joint4']] = areas[['Area','Joint1','Joint2','Joint3','Joint4']].astype(str)
        # areas['Node1'] = joints.loc[areas['Joint1'].values, 'JoinTag'].values
        # areas['Node2'] = joints.loc[areas['Joint2'].values, 'JoinTag'].values
        # areas['Node3'] = joints.loc[areas['Joint3'].values, 'JoinTag'].values
        # areas['Node4'] = areas.apply(lambda row: 'nan' if row['Joint4'] == 'nan' else joints.at[row['Joint4'], 'JoinTag'], axis=1)

        # areas['Nodes'] = areas.apply(lambda x:[x['Node1'], x['Node2'], x['Node3']] 
        #         if x['Joint4'] == 'nan' else [x['Node1'], x['Node2'], x['Node3'], x['Node4']], axis=1)
        
        # areas.apply(
        #     lambda x: rename_area_nodes(x['ElemTag'],x["Nodes"]), 
        #     axis=1
        #     )

        # logging.debug(f"Execution time: {round((timeit.default_timer() - starttime)*1000,3)} ms")
        # logging.debug("Processing groups...")

        # for row in groups.itertuples():
        #     group = getattr(row, 'GroupName')
        #     lst = groupsassign.loc[(groupsassign['ObjectType']=='Frame') & (groupsassign['GroupName']==group)]['ObjectLabel'].values
        #     if len(lst) > 0:
        #         lst2 = elems[elems['Frame'].isin(lst)]['ElemTag'].values
        #         gmsh.model.addPhysicalGroup(LINE, lst2, name="Group: " + group)            
            
        #     lst = groupsassign.loc[(groupsassign['ObjectType']=='Area') & (groupsassign['GroupName']==group)]['ObjectLabel'].values
        #     if len(lst) > 0:
        #         lst2 = areas[areas['Area'].isin(lst)]['ElemTag'].values
        #         gmsh.model.addPhysicalGroup(SURFACE, lst2, name="Group: " + group)

        # logging.debug("Processing frame sections...")

        # for row in sect.itertuples():
        #     sec = getattr(row, 'SectionName')
        #     lst = elems.loc[elems['Section']==sec]['ElemTag'].values
        #     gmsh.model.addPhysicalGroup(LINE, lst, name="Frame section: " + sec)

        # logging.debug("Processing area sections...")

        # for row in areasect.itertuples():
        #     sec = getattr(row, 'Section')
        #     lst = areas.loc[areas['Section']==sec]['ElemTag'].values
        #     gmsh.model.addPhysicalGroup(SURFACE, lst, name="Area section: " + sec)

        # logging.debug("Processing FEM meshn...")
        
        # if not automesh:
        #     gmsh.model.add("FEM mesh")
        #     # prepares the GMSH model
        #     njoins = coordsauto.shape[0]
        #     logging.info(f"Processing nodes ({njoins})...")
        #     point = gmsh.model.addDiscreteEntity(POINT)
        #     gmsh.model.mesh.addNodes(POINT, point, ijoins, lst1)

        # logging.debug("Processing GMSH intialization...")

        # gmsh.option.setNumber("Mesh.SaveAll", 1)
        # gmsh.option.setNumber("Mesh.Lines", 1)
        # gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
        # gmsh.option.setNumber("Mesh.LineWidth", 5)
        # gmsh.option.setNumber("Mesh.ColorCarousel", 2)

        # #size = gmsh.model.getBoundingBox(-1, -1)
        # gmsh.write("filename")

        # # # Launch the GUI to see the results:
        # # if '-nopopup' not in sys.argv:
        # #     gmsh.fltk.run()

        # gmsh.finalize()
        return

    def to_meshio(self, mesh):
        meshio.write("mesh.vtk", mesh)
        return "mesh.vtk"

    def to_excel(self, mesh):
        df = pd.DataFrame(mesh.points)
        df.to_excel("mesh.xlsx")
        return "mesh.xlsx"

    def to_json(self, mesh):
        df = pd.DataFrame(mesh.points)
        df.to_json("mesh.json")
        return

    def to_gldat(self, mesh_file: str):
        """Writes a femix .gldat mesh file

        Args:
            mesh_file (str): the name of the file to be written
        """
        ndime = 3
        
        path = Path(mesh_file)
        if path.suffix.lower() != ".gldat":
            mesh_file = path.with_suffix('').resolve() + ".gldat"

        with open(mesh_file, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write("Main title - Units (F,L)\n")

            file.write("\n")
            file.write("### Main parameters\n")
            file.write("%5d # nelem (n. of elements in the mesh)\n" % self.nelems)
            file.write("%5d # npoin (n. of points in the mesh)\n" % self.npoints)
            file.write("%5d # nvfix (n. of points with fixed degrees of freedom)\n" % self.nspecnodes)
            file.write("%5d # ncase (n. of load cases)\n" % 1)
            file.write("%5d # nselp (n. of sets of element parameters)\n" % self.nmats)
            file.write("%5d # nmats (n. of sets of material properties)\n" % self.nmats)
            file.write("%5d # nspen (n. of sets of element nodal properties)\n" % self.nsections)
            file.write("%5d # nmdim (n. of geometric dimensions)\n" % ndime)
            file.write("%5d # nnscs (n. of nodes with specified coordinate systems)\n" % 0)
            file.write("%5d # nsscs (n. of sets of specified coordinate systems)\n" % 0)
            file.write("%5d # nncod (n. of nodes with constrained d.o.f.)\n" % 0)
            file.write("%5d # nnecc (n. of nodes with eccentric connections)\n" % 0)

            file.write("\n")
            file.write("### Sets of element parameters\n")
            for iselp in range(self.nmats):
                file.write("# iselp\n")
                file.write(" %6d\n" % (iselp+1))
                file.write("# element parameters\n")
                file.write("%5d # ntype (n. of element type)\n" % self._types[iselp][0])
                file.write("%5d # nnode (n. of nodes per element)\n" % self._types[iselp][1])
                file.write("%5d # ngauq (n. of Gaussian quadrature) (stiffness)\n" % self._types[iselp][3])
                file.write("%5d # ngaus (n. of Gauss points in the formulation) (stiffness)\n" % self._types[iselp][4])
                file.write("%5d # ngstq (n. of Gaussian quadrature) (stresses)\n" % self._types[iselp][5])
                file.write("%5d # ngstr (n. of Gauss points in the formulation) (stresses)\n" % self._types[iselp][6])

            file.write("\n")
            file.write("### Sets of material properties\n")
            file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
            file.write("###  Modulus of subgrade reaction, normal and shear stifness)\n")
            for imats in range(self.nmats):
                ntype=self._types[imats][0]
                if (ntype == 10):
                    file.write("# imats         subre\n")
                    file.write("  %5d        1.0e+7\n" % (imats+1))
                elif (ntype == 11 or ntype == 12):
                    file.write("# imats         stift        stifn\n")
                    file.write("  %5d        1.0e+2       1.0e+9\n" % (imats+1))
                else:
                    file.write("# imats         young        poiss        dense        alpha\n")
                    file.write("  %5d       29.0e+6         0.20          2.5       1.0e-5\n" % (imats+1))

            file.write("\n")
            file.write("### Sets of element nodal properties\n")
            for ispen in range(self.nsections):
                ntype = self._types[ispen][0]
                nnode = self._types[ispen][1]

                file.write("# ispen\n")
                file.write(" %6d\n" % (ispen+1))
                if (ntype == 1 or ntype == 5 or ntype == 6 or 
                    ntype == 9 or ntype == 11 or ntype == 12):
                    file.write("# inode       thick\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d        0.25\n" % inode)
                elif (ntype == 7):
                    file.write("# inode       barea        binet        bin2l        bin3l        bangl(deg)\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d        0.01       1.0e-3      1.0e-3        1.0e-4     0.0\n" % inode)
                elif (ntype == 13 or ntype == 14):
                    file.write("# inode       barea        biner\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d        0.01       1.0e-3\n" % inode)
                elif (ntype == 15):
                    file.write("# inode        barea        binet        bin2l        bin3l        eccen(deg)\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d        0.01       1.0e-3      1.0e-3        1.0e-4    -0.2\n" % inode)
                elif (ntype == 8 or ntype == 16):
                    file.write("# inode        barea\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d        0.25\n" % inode)

            file.write("\n")
            file.write("### Element parameter index, material properties index, element nodal\n")
            file.write("### properties index and list of the nodes of each element\n")
            file.write("# ielem ielps matno ielnp       lnods ...\n")
            for elem in self._elements.itertuples():
                file.write(" %6d %5d %5d " % (elem.tag, elem.material, elem.material))
                if (elem.nodals == 1):
                    file.write(" %5d    " % elem.section)
                else:
                    file.write("          ")
                for inode in elem.nodes:
                    file.write(" %8d" % (inode+1))
                file.write("\n")

            file.write("\n")
            file.write("### Coordinates of the points\n")
            if (ndime == 2):
                file.write("# ipoin            coord-x            coord-y\n")
            else:
                file.write("# ipoin            coord-x            coord-y            coord-z\n")

            for ipoin in self._points.itertuples():
                file.write(" %6d    %16.8lf   %16.8lf   %16.8lf\n" % (ipoin.tag+1, ipoin.x, ipoin.y, ipoin.z))

            file.write("\n")
            file.write("### Points with fixed degrees of freedom and fixity codes (1-fixed0-free)\n")
            file.write("# ivfix  nofix       ifpre ...\n")
            for ivfix in self._specialnodes.itertuples():
                file.write(" %6d %6d          1 1 1 1 1 1\n" % (ivfix.tag, ivfix.node[0]+1))

            file.write("\n")
            file.write("### Sets of specified coordinate systems\n")
            file.write("# isscs\n")
            file.write("# ivect    vect1    vect2    vect3\n")

            file.write("\n")
            file.write("### Nodes with specified coordinate systems\n")
            file.write("# inscs inosp itycs\n")

            file.write("\n")
            file.write("### Nodes with linear constraints\n")
            file.write("# incod\n")
            file.write("# csnod csdof nmnod\n")
            file.write("# imnod cmnod cmdof  wedof\n")

            file.write("\n")
            file.write("### Nodes with eccentric connections\n")
            file.write("# inecc  esnod   emnod    eccen...\n")

            file.write("\n")
            file.write("# ===================================================================\n")

            file.write("\n")
            file.write("### Load case n. %8d\n" % 1)

            file.write("\n")
            file.write("### Title of the load case\n")
            file.write("First load case title (gravity)\n")

            file.write("\n")
            file.write("### Load parameters\n")
            file.write("%5d # nplod (n. of point loads in nodal points)\n" % 0)
            file.write("%5d # ngrav (gravity load flag: 1-yes0-no)\n" % 1)
            file.write("%5d # nedge (n. of edge loads) (F.E.M. only)\n" % 0)
            file.write("%5d # nface (n. of face loads) (F.E.M. only)\n" % 0)
            file.write("%5d # ntemp (n. of points with temperature variation) (F.E.M. only)\n" % 0)
            file.write("%5d # nudis (n. of uniformly distributed loads " % 0)
            file.write("(3d frames and trusses only)\n")
            file.write("%5d # nepoi (n. of element point loads) (3d frames and trusses only)\n" % 0)
            file.write("%5d # nprva (n. of prescribed and non zero degrees of freedom)\n" % 0)

            file.write("\n")
            file.write("### Point loads in nodal points (loaded point and load value)\n")
            file.write("### (global coordinate system)\n")
            file.write("### ntype =          1,2,3\n")
            file.write("# iplod  lopop    pload-x  pload-y\n")
            file.write("### ntype =            4,8\n")
            file.write("# iplod  lopop    pload-x  pload-y  pload-z\n")
            file.write("### ntype =              5\n")
            file.write("# iplod  lopop    pload-z pload-tx pload-ty\n")
            file.write("### ntype =      4,6,7,8,9\n")
            file.write("# iplod  lopop    pload-x  pload-y  pload-z")
            file.write(" pload-tx pload-ty pload-tz\n")
            file.write("### ntype =          13,14\n")
            file.write("# iplod  lopop    pload-x  pload-y pload-tz\n")

            file.write("\n")
            file.write("### Gravity load (gravity acceleration)\n")
            file.write("### (global coordinate system)\n")
            file.write("### ntype = 1,2,3,13,14,16\n")
            file.write("#      gravi-x      gravi-y\n")
            file.write("### ntype =              5\n")
            file.write("#      gravi-z\n")
            file.write("### ntype =   4,6,7,8,9,15\n")
            file.write("#      gravi-x      gravi-y      gravi-z\n")
            file.write("      0.00000000E+00  0.00000000E+00  -9.8100000E+00\n")

            file.write("\n")
            file.write("### Edge load (loaded element, loaded points and load value)\n")
            file.write("### (local coordinate system)\n")
            file.write("# iedge  loele\n")
            file.write("### ntype = 1,2,3,13,14\n")
            file.write("# lopoe       press-t   press-n\n")
            file.write("### ntype =           4\n")
            file.write("# lopoe       press-t   press-nt   press-nn\n")
            file.write("# lopon ...\n")
            file.write("### ntype =           5\n")
            file.write("# lopoe       press-n   press-mb   press-mt\n")
            file.write("### ntype =         6,9\n")
            file.write("# lopoe       press-t   press-nt   press-nn")
            file.write("   press-mb   press-mt\n")

            file.write("\n")
            file.write("### Face load (loaded element, loaded points and load value)\n")
            file.write("### (local coordinate system)\n")
            file.write("# iface  loelf\n")
            file.write("### ntype = 1,2,3\n")
            file.write("# lopof      prfac-s1   prfac-s2\n")
            file.write("### ntype =     4\n")
            file.write("# lopof      prfac-s1   prfac-s2    prfac-n\n")
            file.write("### ntype =     5\n")
            file.write("# lopof       prfac-n   prfac-mb   prfac-mt\n")
            file.write("### ntype =   6,9\n")
            file.write("# lopof      prfac-s1   prfac-s2    prfac-n")
            file.write("  prfac-ms2  prfac-ms1\n")

            file.write("\n")
            file.write("### Uniformly distributed load in 3d frame ")
            file.write("or truss elements (loaded element\n")
            file.write("### and load value) (local coordinate system)\n")
            file.write("### ntype =     7\n")
            file.write("# iudis  loelu    udisl-x    udisl-y    udisl-z  ")
            file.write(" udisl-tx   udisl-ty   udisl-tz\n")
            file.write("### ntype =     8\n")
            file.write("# iudis  loelu    udisl-x    udisl-y    udisl-z\n")

            file.write("\n")
            file.write("### Element point load in 3d frame or truss ")
            file.write("elements (loaded element, distance\n")
            file.write("### to the left end and load value) ")
            file.write("(global coordinate system)\n")
            file.write("### ntype =     7\n")
            file.write("# iepoi loelp   xepoi   epoil-x  epoil-y  epoil-z")
            file.write(" epoil-tx epoil-ty epoil-tz\n")
            file.write("### ntype =     8\n")
            file.write("# iepoi loelp   xepoi   epoil-x  epoil-y  epoil-z\n")

            file.write("\n")
            file.write("### Thermal load (loaded point and temperature variation)\n")
            file.write("# itemp  lopot     tempn\n")

            file.write("\n")
            file.write("### Prescribed variables (point, degree of freedom and prescribed value)\n")
            file.write("### (global coordinate system)\n")
            file.write("# iprva  nnodp  ndofp    prval\n")

            file.write("\n")
            file.write("END_OF_FILE\n")

        return

    def copy(self):
        return copy.deepcopy(self)
