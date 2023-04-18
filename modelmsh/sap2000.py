
import meshio
import gmsh
import openpyxl
import numpy as np
import pandas as pd
import pathlib
from pathlib import Path
import sys
import logging
import timeit
import copy
from ._common import *

# Element type
POINT = 15
FRAME2 = 1
FRAME3 = 8
TRIANGLE3 = 2
TRIANGLE6 = 9
QUADRANGLE4 = 3
QUADRANGLE8 = 16
QUADRANGLE9 = 10
HEXAHEDRON8 = 5
HEXAHEDRON20 = 17
HEXAHEDRON27 = 12
PYRAMID5 = 6
PYRAMID13 = 18

# Dimension
POINT = 0
LINE = 1
CURVE = 1
SURFACE = 2
VOLUME = 3


colors = {
    "elements": 1,
    "sections": 2,
    "types": 0
    }


def add_area_nodes2(surf, itype, elem, nodes):
        gmsh.model.mesh.addElementsByType(surf, itype, [elem], nodes)


def add_area_nodes(elem, node1, node2, node3, node4):
    surf = gmsh.model.addDiscreteEntity(SURFACE)
    if (node4 == 'nan'):
        gmsh.model.mesh.addElementsByType(surf, TRIANGLE3, [elem], [node1, node2, node3])
    else:
        gmsh.model.mesh.addElementsByType(surf, QUADRANGLE4, [elem], [node1, node2, node3, node4])
    return


def read_line(s: str, s0, cont: bool=False) -> dict:

    if cont:
        s = s0 + s
    t = s

    variables = {}
    s = " ".join(s.strip().split())
    if len(s) == 0:
        variables["type"] = "empty"
        return variables
    
    if (s[len(s)-1] == '_'):
        variables['type'] = "cont"
        variables['previous'] = t.strip()[0:len(t)-2] + ' '
        return variables

# teste 

    if s[0:4].lower() == "file":
        variables["type"] = "empty"
        return variables
    
    if s[0:5].lower() == "table":
        variables["type"] = "table"
        # result = re.search('\"(.*)\"', " ".join(s[7:].split()))
        # variables["title"] = result.group()
        variables["title"] = " ".join(s[7:].split(r'"')).strip()
        return variables

    start = 0
    variables["type"] = "values"
    variables["values"] = {}
    wlist = []
    words = " ".join(s.split("=")).split()
    iterate = False
    jo = ""
    for w in words:
        if iterate:
            if w[len(w)-1] == r'"':
                jo += w[0:len(w)-1]
                iterate = False
                wlist.append(jo)
            else:
                jo += w + ' '
        else:
            if w[0] == r'"':
                iterate = True
                jo += w[1:] + ' '
            else:
                wlist.append(w)
    
    size = len(wlist) - 1
    for i in range(0, size, 2):
        variables["values"][wlist[i]] = wlist[i+1]

    return variables


def rename_area_nodes(elem, nodes):
    surf = gmsh.model.addDiscreteEntity(SURFACE)
    if len(nodes) == 3:
        gmsh.model.mesh.addElementsByType(surf, TRIANGLE3, [elem], nodes)
    else:
        gmsh.model.mesh.addElementsByType(surf, QUADRANGLE4, [elem], nodes)
    return


def add_elem_nodes(joints, elem, node1, node2):
    surf = gmsh.model.addDiscreteEntity(CURVE)
    lst =  [joints.at[node1, "JoinTag"],
            joints.at[node2, "JoinTag"]]
    gmsh.model.mesh.addElementsByType(surf, FRAME2, [elem], lst)
    return lst


def read_s2k(filename: str) -> dict:
    """_summary_

    Args:
        filename (str): the name of the file to be read

    Returns:
        dict: a dictionary with the tables of the s2k file
    """    
    s2k = {}
    f = open(filename, 'r')
    tabletitle = ""
    cont = False
    previous = ""
    for line in f:
        l = read_line(line, previous, cont)
        if l["type"] == "empty": 
            cont = False
            continue
        elif l["type"] == "cont": 
            cont = True
            previous = l["previous"]
            continue
        elif l["type"] == "table":
            cont = False
            tabletitle = l["title"]
            s2k[tabletitle] = []
            continue
        else:
            cont = False
            s2k[tabletitle].append(l["values"])
    f.close()

    for s in s2k:
        s2k[s.upper()] = pd.DataFrame(s2k[s])

    return s2k


def read_excel(self, filename: str) -> dict:
    """Reads a SAP2000 excel file

    Args:
        filename (str): the name of the file to be read
        out (str, optional): specifies if the return value is a pandas dataframe or a xl objecct. Defaults to 'pandas'.

    Returns:
        *varies*: the database of the SAP2000 excel file as a pandas dataframe or a xl object
    """

    s2k = pd.read_excel(filename, sheet_name=None, skiprows=lambda x: x in [0, 2])
    for df in s2k:
        s2k[df.upper()] = s2k[df]

    # if out.lower() == 'openpyxl' or out.lower() == 'xl':
    #     xlsx = openpyxl.load_workbook(filename)
    # else:
    #     xlsx = self.s2kDatabase
        
    return s2k

class sap2000_handler:
    
    def __init__(self, filename: str):
        self.s2k = {}  # SAP2000 S2K file database
        path = pathlib.Path(filename)
        if path.suffix == ".s2k":
            self.s2k = read_s2k(filename)
        elif path.suffix == ".xlsx":
            self.s2k = read_excel(filename)
        else:
            raise ValueError("File extension not supported")
        
        self._filename = str(path.parent / path.stem)

        if not self._check_input("geometry"):
            raise ValueError("Input file is not a SAP2000 file")

    def _check_input(self, model: str) -> bool:
        try:
            joints = self.s2k['JOINT COORDINATES']
        except:
            print("You must export table 'Joint Coordinates' from SAP2000\n")
            return False
        self._njoins = joints.shape[0]
        self.pn = dict(zip(self.joints['Joint'], np.arange(1, self.njoins+1)))
        self.joints['Joint'] = joints['Joint'].astype(str)
        # print(self.s2k['JOINT COORDINATES'].head())

        try:
            elems = self.s2k['CONNECTIVITY - FRAME']
            if model == 'mesh':
                try:
                    lnodesframe = self.s2k["OBJECTS AND ELEMENTS - FRAMES"]
                    self._nframes = self.lnodesframe.shape[0]
                except:
                    print("You must export table 'OBJECTS AND ELEMENTS - FRAMES' from SAP2000\n")
                    return False
            else:
                self._nframes = self.frames.shape[0]
            
            if not 'FRAME SECTION PROPERTIES 01 - GENERAL' in self.s2k:
                self.s2k['FRAME SECTION PROPERTIES 01 - GENERAL'] = self.s2k.pop('FRAME PROPS 01 - GENERAL')
            
            if not 'MATERIAL PROPERTIES 02 - BASIC MECHANICAL PROPERTIES' in self.s2k:
                self.s2k['MATERIAL PROPERTIES 02 - BASIC MECHANICAL PROPERTIES'] = self.s2k.pop('MatProp 02 - Basic Mech Props'.upper())
        except:
            self._nframes = 0

        # sectassign = self.s2k['Frame Section Assignments'.upper()]
        # logging.info(f"Processing frames ({self.nframes})...")
        # self.frames["ElemTag"] = np.arange(1, self.nframes+1)
        # self.frames["Section"] = sectassign['AnalSect'].values
        # self.frames[['Frame', 'JointI', 'JointJ']] = self.frames[['Frame', 'JointI', 'JointJ']].astype(str)
        
        # self.frames['Nodes'] = self.frames.apply(
        #     lambda row: rename_elem_nodes(joints, row['ElemTag'], row["JointI"],row["JointJ"]), 
        #     axis=1
        #     )

        try:
            self._nareas = self.s2k['CONNECTIVITY - AREA'].shape[0]
            if model == 'mesh':
                try:
                    self._nareas = self.s2k["OBJECTS AND ELEMENTS - AREAS"].shape[0]
                except:
                    print("You must export table 'OBJECTS AND ELEMENTS - AREAS' from SAP2000\n")
                    return False
        except:
            self._nareas = 0
            
        self._nelems = self._nframes + self._nareas
        if self._nelems == 0:
            print("No elements found in the input file\n")
            return False


        # a = joints.loc[areas['Joint1'].values, 'JoinTag'].values
        # b = joints.loc[areas['Joint2'].values, 'JoinTag'].values
        # c = joints.loc[areas['Joint3'].values, 'JoinTag'].values
        # d = areas['Joint4'].values
        # self.lframe1 = np.stack((a, b, c), axis=1)
        # self.lframe2 = np.where(d == 'nan', [a, b, c], [a, b, c])
        

        # areas['Nodes'] = areas.apply(lambda x:[x['Node1'], x['Node2'], x['Node3']] 
        #          if x['Joint4'] == 'nan' else [x['Node1'], x['Node2'], x['Node3'], x['Node4']], axis=1)
        
        try:
            self._mats = self.s2k['MATERIAL PROPERTIES 02 - BASIC MECHANICAL PROPERTIES']
            self._nmats = self._mats.shape[0]
        except:
            print("You must export table 'MATERIAL PROPERTIES 02 - BASIC MECHANICAL PROPERTIES' from SAP2000\n")
            return False

        try:
            self._sections = self.s2k['FRAME SECTION PROPERTIES 01 - GENERAL']
            self._nsections = self._mats.shape[0]
        except:
            print("You must export table 'FRAME SECTION PROPERTIES 01 - GENERAL' from SAP2000\n")
            return False

        return True

    @property
    def nelems(self):
        return self._nelems

    @property
    def nareas(self):
        return self._nareas
    
    @property
    def nframes(self):
        return self._nframes
    
    @property
    def njoins(self):
        return self._njoins
    
    @property
    def nmats(self):
        return self._nmats
        
    @property
    def nsections(self):
        return self._nsections
        
    @property
    def nspecnodes(self):
        return 0
        
    @property
    def joints(self):
        return self.s2k['JOINT COORDINATES']
    
    @property
    def frames(self):
        return self.s2k['CONNECTIVITY - FRAME']
    
    @property
    def areas(self):
        return self.s2k['CONNECTIVITY - AREA']
    
    @property
    def mats(self):
        return self._mats
    
    @property
    def sections(self):
        return self._sections


    def get_table(self, tabletitle):
        tabletitle = ""
        try:
            return self.s2k[tabletitle]
        except KeyError as error:
            return None


    def to_femix(self):
        """Writes a femix .gldat mesh file

        Args:
            mesh_file (str): the name of the file to be written
        """
        
        filename = self._filename + ".gldat"

        nelems = self.s2k['Connectivity - Frame'.upper()].shape[0]
        nelems += self.s2k['Connectivity - Area'.upper()].shape[0]
        sect = self.sections
        nsections = sect.shape[0]
        areasect = self.s2k['Area Section Properties'.upper()]
        nsections += areasect.shape[0]

        ndime = 3

        with open(filename, 'w') as file:

            # JOINTS
            njoins = self._njoins
            ijoins = np.arange(1, njoins+1)
            joints = self.joints
            joints["JoinTag"] = ijoins
            joints['Joint'] = joints['Joint'].astype(str)
            joints.set_index('Joint', inplace=True)
            joints['coord'] = joints[['XorR', 'Y', 'Z']].values.tolist()
            # ELEMENTS - FRAMES
            nelems = self.nframes
            elems = self.frames
            elems["ElemTag"] =  np.arange(1, self.nframes+1)
            elems[['Frame', 'JointI', 'JointJ']] = elems[['Frame', 'JointI', 'JointJ']].astype(str)
            elems['Node1'] = joints.loc[elems['JointI'].values, 'JoinTag'].values
            elems['Node2'] = joints.loc[elems['JointJ'].values, 'JoinTag'].values
            elems['Nodes'] = elems[['Node1', 'Node2']].values.tolist()

            matlist = []
            seclist = self.s2k['FRAME SECTION ASSIGNMENTS']['AnalSect'].unique()
            for row in self.sections.itertuples():
                # sec = getattr(row, 'SectionName')
                if getattr(row, 'SectionName') in seclist:
                    mat = getattr(row, 'Material')
                    if not mat in matlist:
                        matlist.append(mat)

            nselp = 0
            lselp = []
            if self.nframes > 0: 
                nselp += 1
                lselp.append(s2k_femix['frame'])
            if self.areas['Joint4'].isnull().values.all(): 
                nselp+=1 # only 3 node elements
                lselp.append(s2k_femix['triangle'])
            else:
                if self.areas['Joint4'].isnull().values.any(): 
                    nselp+=1 # some 3 node elements
                    lselp.append(s2k_femix['triangle'])
                nselp += 1 # some 4 node elements
                lselp.append(s2k_femix['quad'])

            file.write("### Main title of the problem\n")
            file.write("Main title - Units (F,L)\n")

            file.write("\n")
            file.write("### Main parameters\n")
            file.write("%5d # nelem (n. of elements in the mesh)\n" % self.nelems)
            file.write("%5d # npoin (n. of points in the mesh)\n" % self.njoins)
            file.write("%5d # nvfix (n. of points with fixed degrees of freedom)\n" % self.nspecnodes)
            file.write("%5d # ncase (n. of load cases)\n" % 1)
            file.write("%5d # nselp (n. of sets of element parameters)\n" % nselp)
            file.write("%5d # nmats (n. of sets of material properties)\n" % len(matlist))
            file.write("%5d # nspen (n. of sets of element nodal properties)\n" % len(seclist))
            file.write("%5d # nmdim (n. of geometric dimensions)\n" % ndime)
            file.write("%5d # nnscs (n. of nodes with specified coordinate systems)\n" % 0)
            file.write("%5d # nsscs (n. of sets of specified coordinate systems)\n" % 0)
            file.write("%5d # nncod (n. of nodes with constrained d.o.f.)\n" % 0)
            file.write("%5d # nnecc (n. of nodes with eccentric connections)\n" % 0)

            file.write("\n")
            file.write("### Sets of element parameters\n")
            for iselp in range(nselp):
                file.write("# iselp\n")
                file.write(" %6d\n" % (iselp+1))
                file.write("# element parameters\n")
                file.write("%5d # ntype (n. of element type)\n" % lselp[iselp][0])
                file.write("%5d # nnode (n. of nodes per element)\n" % lselp[iselp][1])
                file.write("%5d # ngauq (n. of Gaussian quadrature) (stiffness)\n" % lselp[iselp][3])
                file.write("%5d # ngaus (n. of Gauss points in the formulation) (stiffness)\n" % lselp[iselp][4])
                file.write("%5d # ngstq (n. of Gaussian quadrature) (stresses)\n" % lselp[iselp][5])
                file.write("%5d # ngstr (n. of Gauss points in the formulation) (stresses)\n" % lselp[iselp][6])

            file.write("\n")
            file.write("### Sets of material properties\n")
            file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
            file.write("###  Modulus of subgrade reaction, normal and shear stifness)\n")
            for imats, value in enumerate(matlist):
                ntype=9 #self._types[imats][0]
                if (ntype == 10):
                    file.write("# imats         subre\n")
                    file.write("  %5d        1.0e+7\n" % (imats+1))
                elif (ntype == 11 or ntype == 12):
                    file.write("# imats         stift        stifn\n")
                    file.write("  %5d        1.0e+2       1.0e+9\n" % (imats+1))
                else:
                    row = self.mats.loc[self.mats['Material'] == value]
                    young = float(row['E1'])
                    poiss = float(row['U12'])
                    dense = float(row['UnitMass'])
                    alpha = float(row['A1'])
                    file.write("# imats         young        poiss        dense        alpha\n")
                    file.write("  %5d     %s     %s     %s     %s\n" % (imats+1, young, poiss, dense, alpha))

            file.write("\n")
            file.write("### Sets of element nodal properties\n")
            for ispen, value in enumerate(lselp):
                ntype = value[0]
                nnode = value[1]

                file.write("# ispen\n")
                file.write(" %6d\n" % (ispen+1))
                if (ntype == 9):
                    file.write("# inode       thick\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d        0.25\n" % inode)
                elif (ntype == 7):
                    file.write("# inode       barea        binet        bin2l        bin3l        bangl(deg)\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d        0.01       1.0e-3      1.0e-3        1.0e-4     0.0\n" % inode)

            file.write("\n")
            file.write("### Element parameter index, material properties index, element nodal\n")
            file.write("### properties index and list of the nodes of each element\n")
            file.write("# ielem ielps matno ielnp       lnods ...\n")
            for elem in self.elements.itertuples():
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

            for ipoin in self.joints.itertuples():
                file.write(" %6d    %16.8lf   %16.8lf   %16.8lf\n" % (ipoin.tag+1, ipoin.xorr, ipoin.y, ipoin.z))

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


    def to_msh(self, model: str = 'geometry', entities: str = 'types', physicals: str = ''):
        """Writes a GMSH mesh file and opens it in GMSH

        Args:
            filename (str): the name of the file to be written
        """
        filename = self._filename + ".msh"
        listsectionframes = None
        listsectionareas = None
        
        # process options
        if model not in ['geometry', 'mesh']:
            raise ValueError('model must be "geometry" or "mesh"')
        elif entities not in ['types', 'sections', 'elements']:
            raise ValueError('entities must be "types", "sections" or "elements"')
        elif physicals not in ['sections', '']:
            if entities != 'sections' or entities != 'elements':    
                raise ValueError('entities must be "sections" or "elements" if physical is "sections"')
            raise ValueError('physicals must be "sections" or ""')
        
        if not self._check_input(filename):
            raise ValueError('Filename id nt in correct format')
        
        # initialize gmsh
        gmsh.initialize(sys.argv)
        
        gmsh.model.add(pathlib.Path(filename).stem)
        gmsh.model.setFileName(filename)

        joints = self.s2k['Joint Coordinates'.upper()]
        elems = self.s2k['Connectivity - Frame'.upper()]
        areas = self.s2k['Connectivity - Area'.upper()]
        sect = self.s2k['Frame Props 01 - General'.upper()]
        sectassign = self.s2k['Frame Section Assignments'.upper()]
        areasect = self.s2k['Area Section Properties'.upper()]
        areaassign = self.s2k['Area Section Assignments'.upper()]
        groups = self.s2k['Groups 1 - Definitions'.upper()]
        groupsassign = self.s2k['Groups 2 - Assignments'.upper()]
        
        logging.basicConfig(level=logging.DEBUG)
        logging.info("Writing GMSH file: %s", filename)
        
        # JOINTS
        njoins = joints.shape[0]
        logging.debug(f"Processing nodes ({njoins})...")
        ijoins = np.arange(1, njoins+1)
        joints.insert(0, "JoinTag", ijoins, False)
        joints['Joint'] = joints['Joint'].astype(str)
        joints['Joint2'] = joints['Joint'] #joints.loc[:, 'Joint']
        joints.set_index('Joint', inplace=True)
        joints['coord'] = joints[['XorR', 'Y', 'Z']].values.tolist()

        ient = gmsh.model.addDiscreteEntity(POINT)
        gmsh.model.mesh.addNodes(POINT, ient, ijoins, joints['coord'].explode().to_list())

        # ELEMENTS - FRAMES
        nelems = elems.shape[0]
        logging.info(f"Processing frames ({nelems})...")
        elems.insert(1, "ElemTag", np.arange(1, nelems+1), False)
        elems.insert(2, "Section", sectassign['AnalSect'].values, False)
        elems[['Frame', 'JointI', 'JointJ']] = elems[['Frame', 'JointI', 'JointJ']].astype(str)
        elems['Node1'] = joints.loc[elems['JointI'].values, 'JoinTag'].values
        elems['Node2'] = joints.loc[elems['JointJ'].values, 'JoinTag'].values
        elems['Nodes'] = elems[['Node1', 'Node2']].values.tolist()
        
        if entities== 'elements':
            elems['Nodes'] = elems.apply(
                lambda row: add_elem_nodes(joints, row['ElemTag'], row["JointI"],row["JointJ"]), 
                axis=1
                )
        elif entities == 'sections':
            for row in sect.itertuples():
                sec = getattr(row, 'SectionName')
                framesl = pd.DataFrame(elems.loc[elems['Section']==sec])
                line = gmsh.model.addDiscreteEntity(CURVE)
                gmsh.model.setEntityName(CURVE, line, sec)
                lst = framesl['ElemTag'].to_list()
                gmsh.model.mesh.addElementsByType(line, FRAME2, lst, framesl['Nodes'].explode().to_list())

                if physicals == 'sections':
                    gmsh.model.addPhysicalGroup(CURVE, [line], name="section: " + sec)

        elif entities == 'types':
            line = gmsh.model.addDiscreteEntity(CURVE)
            gmsh.model.setEntityName(CURVE, line, 'Line2')
            gmsh.model.mesh.addElementsByType(line, FRAME2, elems['ElemTag'].to_list(), elems['Nodes'].explode().to_list())
        else:
            raise ValueError('entities must be "types", "sections" or "elements"')

        # ELEMENTS - AREAS
        starttime = timeit.default_timer()
        logging.info(f"Processing ares ({nelems})...")
        nelems = self._nareas
        areas["ElemTag"] = np.arange(1, nelems+1)
        areas["Section"] = areaassign['Section'].values
        areas[['Area','Joint1','Joint2','Joint3','Joint4']] = areas[['Area','Joint1','Joint2','Joint3','Joint4']].astype(str)
        areas['Node1'] = joints.loc[areas['Joint1'].values, 'JoinTag'].values
        areas['Node2'] = joints.loc[areas['Joint2'].values, 'JoinTag'].values
        areas['Node3'] = joints.loc[areas['Joint3'].values, 'JoinTag'].values
        areas['Node4'] = areas.apply(lambda row: 'nan' if row['Joint4'] == 'nan' else joints.at[row['Joint4'], 'JoinTag'], axis=1)

        logging.debug(f"Execution time: {round((timeit.default_timer() - starttime)*1000,3)} ms")
        if entities == 'elements':  
            starttime = timeit.default_timer()
            np.vectorize(add_area_nodes, otypes=[np.ndarray])(areas['ElemTag'].values,
                    areas['Node1'].values, areas['Node2'].values, areas['Node3'].values, areas['Node4'].values)
            logging.debug(f"Execution time for adding to model: {round((timeit.default_timer() - starttime)*1000,3)} ms")

        elif entities == 'sections':
            for row in areasect.itertuples():
                sec = getattr(row, 'Section')
                areasl = pd.DataFrame(areas.loc[areas['Section']==sec])
                surf = gmsh.model.addDiscreteEntity(SURFACE)
                gmsh.model.setEntityName(SURFACE, surf, sec)

                areas3 = pd.DataFrame(areasl.loc[areasl['Joint4'] == 'nan'])
                areas3['nodes'] = areas3.loc[:,['Node1', 'Node2', 'Node3']].values.tolist()
                gmsh.model.mesh.addElementsByType(surf, TRIANGLE3, areas3['ElemTag'].to_list(), areas3['nodes'].explode().to_list())
            
                areas3 = pd.DataFrame(areasl.loc[areas['Joint4'] != 'nan'])
                areas3['nodes'] = areas3.loc[:,['Node1', 'Node2', 'Node3', 'Node4']].values.tolist()
                gmsh.model.mesh.addElementsByType(surf, QUADRANGLE4, areas3['ElemTag'].to_list(), areas3['nodes'].explode().to_list())

                if physicals == 'sections':
                    gmsh.model.addPhysicalGroup(SURFACE, [surf], name="section: " + sec)

        elif entities == 'types':
            areas3 = pd.DataFrame(areas.loc[areas['Joint4'] == 'nan'])
            areas3['nodes'] = areas3.loc[:,['Node1', 'Node2', 'Node3']].values.tolist()
            surf = gmsh.model.addDiscreteEntity(SURFACE)
            gmsh.model.setEntityName(SURFACE, surf, 'Triangle3')
            gmsh.model.mesh.addElementsByType(surf, TRIANGLE3, areas3['ElemTag'].to_list(), areas3['nodes'].explode().to_list())

            areas3 = pd.DataFrame(areas.loc[areas['Joint4'] != 'nan'])
            areas3['nodes'] = areas3.loc[:,['Node1', 'Node2', 'Node3', 'Node4']].values.tolist()
            surf = gmsh.model.addDiscreteEntity(SURFACE)
            gmsh.model.setEntityName(SURFACE, surf, 'Quadrangle4')
            gmsh.model.mesh.addElementsByType(surf, QUADRANGLE4, areas3['ElemTag'].to_list(), areas3['nodes'].explode().to_list())
        else:
            raise ValueError('entities must be "types", "sections" or "elements"')

        # PHYSICALS
        if physicals == 'sections' and entities == 'elements':
            for row in sect.itertuples():
                sec = getattr(row, 'SectionName')
                lst = elems.loc[elems['Section']==sec]['ElemTag'].values
                gmsh.model.addPhysicalGroup(CURVE, lst, name="section: " + sec)

            for row in areasect.itertuples():
                sec = getattr(row, 'Section')
                lst = areas.loc[areas['Section']==sec]['ElemTag'].values
                gmsh.model.addPhysicalGroup(SURFACE, lst, name="section: " + sec)

        if False:
            logging.debug("Processing FEM mesh...")
            gmsh.model.add("FEM mesh")
            # prepares the GMSH model
            njoins = coordsauto.shape[0]
            logging.info(f"Processing nodes ({njoins})...")
#            coordsauto.insert(0, "JoinTag", np.arange(1, njoins+1), False)
#            coordsauto['Joint'] = coordsauto['Joint'].astype(str)
#            coordsauto['Joint2'] = coordsauto.loc[:, 'Joint']
#            coordsauto.set_index('Joint', inplace=True)
#            coordsauto['coord'] = coordsauto.apply(lambda x: np.array([x['XorR'], x['Y'], x['Z']]),axis=1) 
#            lst1 = coordsauto['coord'].explode().to_list()
            point = gmsh.model.addDiscreteEntity(POINT)
            gmsh.model.mesh.addNodes(POINT, point, ijoins, lst1)

        logging.debug("Processing GMSH intialization...")
        
        gmsh.model.setAttribute("Materials", ["Concrete:Stiff:30000000",  "Concrete:Poiss:0.2", "Steel:Stiff:20000000", "Steel:Poiss:0.3"])

        gmsh.option.setNumber("Mesh.SaveAll", 1)

        #size = gmsh.model.getBoundingBox(-1, -1)
        gmsh.write(filename)

        # # Launch the GUI to see the results:
        # if '-nopopup' not in sys.argv:
        #     gmsh.fltk.run()

        gmsh.finalize()

        return self._filename + ".msh"


    def to_msh_and_open(self, model: str = 'geometry', entities: str = 'types', physicals: str = ''):

        s = self.to_msh(model, entities, physicals)

        gmsh.initialize()
        
        gmsh.option.setNumber("Mesh.Lines", 1)
        gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
        gmsh.option.setNumber("Mesh.LineWidth", 5)
        gmsh.option.setNumber("Mesh.ColorCarousel", colors[entities])

        gmsh.open(s)
        if '-nopopup' not in sys.argv:
            gmsh.fltk.run()

        gmsh.finalize()


    def copy(self):
        return copy.deepcopy(self)
