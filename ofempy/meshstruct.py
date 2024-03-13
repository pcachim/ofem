"""_summary_line = "This modules generates and calculates simple structures with simple geometries" # for summary file
"""

import sys
import gmsh
import numpy as np
import pathlib
#import eurocodepy as ec
from . import libofempy
from .common import *
from . import gmshhandler

# slabs
RECTANGULAR = 1
TRIANGULAR = 2
CIRCULAR = 3
CIRCULAR_QUARTER = 4
CIRCULAR_WITH_HOLE = 5
CIRCULAR_SEGMENT = 6
POLYGON = 7

# beams
LINEAR2D = 101
CURVED2D = 102
SPATIAL3D = 103
FRAME2D = 112
FRAME3D = 113
BUILDING3D = 120

# supports
FREE = -1
HINGED = 0 # 1110
FIXED = 1 # 1111
HORIZONTAL = 1100
VERTICAL = 1010
ROTATION = 1001
HOR_ROT = 1101
VER_ROT = 1011


def rotate_point(point1: tuple, point2: tuple, angle: float) -> tuple:
    """Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in radians.
    """
    ox, oy, _ = point1
    px, py = point2
    qx = ox + np.cos(angle) * (px - ox) - np.sin(angle) * (py - oy)
    qy = oy + np.sin(angle) * (px - ox) + np.cos(angle) * (py - oy)
    return qx, qy


def Circle(center: tuple, radius: float, msize: float = 0.3):
    gmsh.model.add("slab")
    pt1 = gmsh.model.geo.addPoint(center[0], center[1], center[2], msize)
    pt2 = gmsh.model.geo.addPoint(center[0]+radius, center[1], center[2], msize)
    pt3 = gmsh.model.geo.addPoint(center[0]-radius, center[1], center[2], msize)
    sf1 = gmsh.model.geo.addCircleArc(pt2, pt1, pt3)
    sf2 = gmsh.model.geo.addCircleArc(pt3, pt1, pt2)
    circle = gmsh.model.geo.addCurveLoop([sf1, sf2])
    area = gmsh.model.geo.addPlaneSurface([circle])
    gmsh.model.geo.synchronize()
    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(2)


def CircleWithHole2(center: tuple, radius_ext: float,  radius_int: float, msize: float = 0.6):
    gmsh.model.add("slab")
    pt1 = gmsh.model.geo.addPoint(center[0], center[1], center[2], msize)
    pt2 = gmsh.model.geo.addPoint(center[0]+radius_int, center[1], center[2], msize)
    pt3 = gmsh.model.geo.addPoint(center[0]-radius_int, center[1], center[2], msize)
    sf1 = gmsh.model.geo.addCircleArc(pt2, pt1, pt3)
    sf2 = gmsh.model.geo.addCircleArc(pt3, pt1, pt2)
    circle1 = gmsh.model.geo.addCurveLoop([sf1, sf2])
    #circ_int = gmsh.model.geo.addPlaneSurface([circle])

    pt1 = gmsh.model.geo.addPoint(center[0], center[1], center[2], msize)
    pt2 = gmsh.model.geo.addPoint(center[0]+radius_ext, center[1], center[2], msize)
    pt3 = gmsh.model.geo.addPoint(center[0]-radius_ext, center[1], center[2], msize)
    sf1 = gmsh.model.geo.addCircleArc(pt2, pt1, pt3)
    sf2 = gmsh.model.geo.addCircleArc(pt3, pt1, pt2)
    circle2 = gmsh.model.geo.addCurveLoop([sf1, sf2])
    circ_out = gmsh.model.geo.addPlaneSurface([circle2, circle1])


    gmsh.model.geo.synchronize()
    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(2)


def CircleWithHole(center: tuple, radius_ext: float, radius_int: float, msize: float = 0.3):
    gmsh.model.add("slab")
    circ_out = gmsh.model.occ.addDisk(center[0], center[1], center[2], radius_ext, radius_ext)
    circ_int = gmsh.model.occ.addDisk(center[0], center[1], center[2], radius_int, radius_int)
    a, b = gmsh.model.occ.cut([(2, circ_out)], [(2, circ_int)])

    gmsh.model.occ.synchronize()

    # for e in gmsh.model.getEntities(1):
    #     gmsh.model.addPhysicalGroup(1, [e[1]], name = "fix: free%d"%e[1])

    # gmsh.model.mesh.setSize(gmsh.model.getEntities(-1), msize)

    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(2)
    return 


def CircleSegment(center: tuple, radius: float, startangle: float, endangle: float, msize: float = 0.3):
    gmsh.model.add("slab")
    angle = endangle - startangle
    pt1 = gmsh.model.geo.addPoint(center[0], center[1], center[2], msize)
    pn2 = rotate_point(center, (center[0]+radius, center[1]), startangle)
    pt2 = gmsh.model.geo.addPoint(pn2[0], pn2[1], center[2], msize)
    pn3 = rotate_point(center, (center[0]+radius, center[1]), endangle)
    pt3 = gmsh.model.geo.addPoint(pn3[0], pn3[1], center[2], msize)
    sf1 = gmsh.model.geo.addCircleArc(pt2, pt1, pt3)
    sf2 = gmsh.model.geo.addLine(pt3, pt1)
    sf3 = gmsh.model.geo.addLine(pt1, pt2)
    circle = gmsh.model.geo.addCurveLoop([sf1, sf2, sf3],)
    area = gmsh.model.geo.addPlaneSurface([circle])
    gmsh.model.geo.synchronize()
    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(2)
    return area


def CirleQuarter(center: tuple, radius: float, angle: float, msize: float = 0.3):
    gmsh.model.add("slab")
    pt1 = gmsh.model.geo.addPoint(center[0], center[1], center[2], msize)
    pn2 = rotate_point(center, (center[0]+radius, center[1]), angle)
    pt2 = gmsh.model.geo.addPoint(pn2[0], pn2[1], center[2], msize)
    pn3 = rotate_point(center, (center[0], center[1]+radius), angle)
    pt3 = gmsh.model.geo.addPoint(pn3[0], pn3[1], center[2], msize)
    sf1 = gmsh.model.geo.addCircleArc(pt2, pt1, pt3)
    sf2 = gmsh.model.geo.addLine(pt3, pt1)
    sf3 = gmsh.model.geo.addLine(pt1, pt2)
    circle = gmsh.model.geo.addCurveLoop([sf1, sf2, sf3],)
    area = gmsh.model.geo.addPlaneSurface([circle])
    gmsh.model.geo.synchronize()
# To generate a curvilinear mesh and optimize it to produce provably valid
# curved elements (see A. Johnen, J.-F. Remacle and C. Geuzaine. Geometric
# validity of curvilinear finite elements. Journal of Computational Physics
# 233, pp. 359-372, 2013; and T. Toulorge, C. Geuzaine, J.-F. Remacle,
# J. Lambrechts. Robust untangling of curvilinear meshes. Journal of
# Computational Physics 254, pp. 8-26, 2013), you can uncomment the following
# lines:
#
# gmsh.option.setNumber("Mesh.ElementOrder", 2)
# gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(2)
    return area


def Rectangle(bleft: tuple, width: float, height: float, angle: float, msize: float = 0.3):
    gmsh.model.add("slab")
    pt1 = gmsh.model.geo.addPoint(bleft[0]      , bleft[1]       , bleft[2], msize)
    pn2 = rotate_point(bleft, (bleft[0]+width, bleft[1]), angle)
    pt2 = gmsh.model.geo.addPoint(pn2[0], pn2[1], bleft[2], msize)
    pn3 = rotate_point(bleft, (bleft[0]+width, bleft[1]+height), angle)
    pt3 = gmsh.model.geo.addPoint(pn3[0], pn3[1], bleft[2], msize)
    pn4 = rotate_point(bleft, (bleft[0], bleft[1]+height), angle)
    pt4 = gmsh.model.geo.addPoint(pn4[0], pn4[1], bleft[2], msize)
    sf1 = gmsh.model.geo.addLine(pt1, pt2)
    sf2 = gmsh.model.geo.addLine(pt2, pt3)
    sf3 = gmsh.model.geo.addLine(pt3, pt4)
    sf4 = gmsh.model.geo.addLine(pt4, pt1)
    circle = gmsh.model.geo.addCurveLoop([sf1, sf2, sf3, sf4],)
    area = gmsh.model.geo.addPlaneSurface([circle])
    gmsh.model.geo.synchronize()
    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(2)
    return area


def Triangle(point1: tuple, point2: tuple, point3: tuple, angle: float, msize: float = 0.3):
    pt1 = gmsh.model.geo.addPoint(point1[0], point1[1], point1[2], msize)
    pn2 = rotate_point(point1, point2, angle)
    pt2 = gmsh.model.geo.addPoint(pn2[0], pn2[1], point2[2], msize)
    pn2 = rotate_point(point1, point3, angle)
    pt3 = gmsh.model.geo.addPoint(pn2[0], pn2[1], point3[2], msize)
    sf1 = gmsh.model.geo.addLine(pt1, pt2)
    sf2 = gmsh.model.geo.addLine(pt2, pt3)
    sf3 = gmsh.model.geo.addLine(pt3, pt1)
    circle = gmsh.model.geo.addCurveLoop([sf1, sf2, sf3])
    area = gmsh.model.geo.addPlaneSurface([circle])
    gmsh.model.geo.synchronize()
    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(2)
    return area


def Polygon(points: tuple, msize: float = 0.3):
    pt = []
    ln = []
    for i in range(len(points)):
        k = gmsh.model.geo.addPoint(points[i][0], points[i][1], points[i][2], msize)
        pt.append(k)
    pt.append(pt[0])
    for i in range(len(points)):
        k = gmsh.model.geo.addLine(pt[i], pt[i+1])
        ln.append(k)
    poly = gmsh.model.geo.addCurveLoop(ln)
    area = gmsh.model.geo.addPlaneSurface([poly])
    gmsh.model.geo.synchronize()
    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(2)
    return area


def LinearBeam(points: tuple, msize: float = 0.3):
    pt = []
    ln = []
    lenb = 0
    k = gmsh.model.geo.addPoint(0.0, 0.0, 0.0, msize)
    pt.append(k)
    for i in range(len(points)):
        lenb += points[i]
        k = gmsh.model.geo.addPoint(lenb, 0.0, 0.0, msize)
        pt.append(k)

    for i in range(len(points)):
        k = gmsh.model.geo.addLine(pt[i], pt[i+1])
        ln.append(k)

    gmsh.model.geo.synchronize()
    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(1)
    return pt, ln


def CurvedBeam(points: tuple, msize: float = 0.3):
    pt = []
    ln = []
    len = 0
    k = gmsh.model.geo.addPoint(0.0, 0.0, 0.0, msize)
    pt.append(k)
    for i in range(len(points)):
        k = gmsh.model.geo.addPoint(points[i][0], points[i][1], 0.0, msize)
        pt.append(k)

    for i in range(len(points)):
        k = gmsh.model.geo.addLine(pt[i], pt[i+1])
        ln.append(k)

    gmsh.model.geo.synchronize()
    # gmsh.option.setNumber("Mesh.ElementOrder", 2)
    # gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)
    gmsh.model.mesh.generate(1)
    return pt, ln


def SpatialBeam(points: tuple, msize: float = 0.3):
    pt = []
    ln = []
    for i in range(len(points)):
        k = gmsh.model.geo.addPoint(points[i][0], points[i][1], points[i][2], msize)
        pt.append(k)
    for i in range(len(points)-1):
        k = gmsh.model.geo.addLine(pt[i], pt[i+1])
        ln.append(k)
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(2)
    return pt, ln


class Slab:
    
    def __init__(self) -> None:
        if not gmsh.is_initialized():
            gmsh.initialize()
        return
    
    def addGeometry(self, geometry: int, *args, **kwargs):
        """_summary_

        Args:
            geometry (int): _description_

        Raises:
            ValueError: _description_
        """
        gmsh.model.add("slab")
        if geometry == RECTANGULAR:
            msize = 0.3 if len(args) < 5 else args[4]
            Rectangle(args[0], args[1], args[2], args[3], msize)
        elif geometry == TRIANGULAR:
            msize = 0.3 if len(args) < 5 else args[4]
            Triangle(args[0], args[1], args[2], args[3], msize)
        elif geometry == CIRCULAR:
            msize = 0.3 if len(args) < 3 else args[2]
            Circle(args[0], args[1], msize)
        elif geometry == CIRCULAR_QUARTER:
            msize = 0.3 if len(args) < 4 else args[3]
            CirleQuarter(args[0], args[1], args[2], msize)
        elif geometry == CIRCULAR_WITH_HOLE:
            msize = 0.3 if len(args) < 4 else args[3]
            CircleWithHole2(args[0], args[1], args[2], msize)
        elif geometry == CIRCULAR_SEGMENT:
            msize = 0.3 if len(args) < 5 else args[4]
            CircleSegment(args[0], args[1], args[2], args[3], msize)
        elif geometry == POLYGON:
            msize = 0.3 if len(args) < 2 else args[1]
            Polygon(args[0], msize)
        else:
            raise ValueError("Invalid slab geometry type.")
        
        if len(kwargs) > 0:
            self.addParameters(**kwargs)
        return
    
    def addParameters(self, **kwargs):
        self.fixno = {}
        if "boundary" in kwargs:
            bounddary_condition = kwargs["boundary"]
            # if len(bounddary_condition) != len (bounds):
            #     raise ValueError("Invalid boundary conditions.")
            for i, b in enumerate(bounddary_condition):
                bounds, _, _ = gmsh.model.mesh.getNodes(1, i+1, includeBoundary=True)
                if b == FREE:
                    pass
                elif b in [FIXED, HINGED]:
                    for inode in bounds:
                        self.fixno[inode] = b if inode not in self.fixno else max(b, self.fixno[inode])
                else:
                    raise ValueError("Invalid boundary conditions.")
        
        if "material" in kwargs:
            self.material = kwargs["material"]
        
        if "thick" in kwargs:
            self.thick = kwargs["thick"]
        
        if "load" in kwargs:
            self.load = float(kwargs["load"])

        return

    def to_ofem(self, mesh_file: str):
        """Writes a femix .gldat mesh file

        Args:
            mesh_file (str): the name of the file to be written
        """
        ndime = 3

        path = pathlib.Path(mesh_file)
        if path.suffix.lower() != ".gldat":
            mesh_file = path.with_suffix('').resolve() + ".gldat"

        jobname = str(path.parent / (path.stem + ".ofem"))
        ofem_file = libofempy.OfemSolverFile(jobname, overwrite=True)

        nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(2, includeBoundary=True)
        coordlist = dict(zip(nodeTags, np.arange(len(nodeTags))))
        nodelist = dict(zip(nodeTags, np.arange(1, len(nodeTags)+1)))
        listnode = {v: k for k, v in nodelist.items()}
        # coords = np.array(nodeCoords).reshape(-1, 3)
        # sorted_dict_by_keys = {key: coordlist[key] for key in sorted(coordlist)}
        eleTypes, eleTags, eleNodes = gmsh.model.mesh.getElements(2)
        elemlist = dict(zip(np.arange(1, 1+len(eleTags[0])), eleTags[0]))
        self.nelems = len(eleTags[0])
        self.npoints = len(nodeTags)
        self.nmats = 1
        self.nsections = 1
        self.nspecnodes = len(self.fixno)
        ndime = 3
        props = meshio_femix[gmsh_meshio[eleTypes[0]]]
        ntype = props[0]
        nnode = props[1]

        with open(mesh_file, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write("Slab mesh\n")

            file.write("\n")
            file.write("### Main parameters\n")
            file.write("%5d # nelem (n. of elements in the mesh)\n" % self.nelems)
            file.write("%5d # npoin (n. of points in the mesh)\n" % self.npoints)
            file.write("%5d # nvfix (n. of points with fixed degrees of freedom)\n" % self.nspecnodes)
            file.write("%5d # ncase (n. of load cases)\n" % 1)
            file.write("%5d # nselp (n. of sets of element parameters)\n" % 1)
            file.write("%5d # nmats (n. of sets of material properties)\n" % 1)
            file.write("%5d # nspen (n. of sets of element nodal properties)\n" % 1)
            file.write("%5d # nmdim (n. of geometric dimensions)\n" % 2)
            file.write("%5d # nnscs (n. of nodes with specified coordinate systems)\n" % 0)
            file.write("%5d # nsscs (n. of sets of specified coordinate systems)\n" % 0)
            file.write("%5d # nncod (n. of nodes with constrained d.o.f.)\n" % 0)
            file.write("%5d # nnecc (n. of nodes with eccentric connections)\n" % 0)

            file.write("\n")
            file.write("### Sets of element parameters\n")
            file.write("# iselp\n")
            file.write(" %6d\n" % 1)
            file.write("# element parameters\n")
            file.write("%5d # ntype (n. of element type)\n" % 5)
            file.write("%5d # nnode (n. of nodes per element)\n" % props[1])
            file.write("%5d # ngauq (n. of Gaussian quadrature) (stiffness)\n" % props[3])
            file.write("%5d # ngaus (n. of Gauss points in the formulation) (stiffness)\n" % props[4])
            file.write("%5d # ngstq (n. of Gaussian quadrature) (stresses)\n" % props[5])
            file.write("%5d # ngstr (n. of Gauss points in the formulation) (stresses)\n" % props[6])

            file.write("\n")
            file.write("### Sets of material properties\n")
            file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
            file.write("# imats         young        poiss        dense        alpha\n")
            file.write("  %5d  %16.3f %16.3f %16.3f %16.3f\n" % (1,
                self.material['E'],self.material['nu'],self.material['rho'],self.material['alpha']))

            file.write("\n")
            file.write("### Sets of element nodal properties\n")
            file.write("# ispen\n")
            file.write(" %6d\n" % 1)
            file.write("# inode       thick\n")
            for inode in range(1, nnode+1):
                file.write(" %6d     %15.3f\n" % (inode, self.thick))

            file.write("\n")
            file.write("### Element parameter index, material properties index, element nodal\n")
            file.write("### properties index and list of the nodes of each element\n")
            file.write("# ielem ielps matno ielnp       lnods ...\n")
            count = 0
            for i, elem in enumerate(eleTags[0]):
                file.write(" %6d %5d %5d %5d    " % (i+1, 1, 1, 1))
                for inode in range(nnode):
                    # file.write(" %8d" % eleNodes[0][count])
                    file.write(" %8d" % nodelist[eleNodes[0][count]])
                    count += 1
                file.write("\n")

            file.write("\n")
            file.write("### Coordinates of the points\n")
            file.write("# ipoin            coord-x            coord-y            coord-z\n")
            icount = 1
            for i, ipoin in enumerate(nodeTags):
                node_tag = listnode[i+1]
                node = coordlist[node_tag]
                count = int(3*node)
                file.write(" %6d    %16.8lf   %16.8lf\n" % (i+1, nodeCoords[count], nodeCoords[count+1]))
                icount += 1

            file.write("\n")
            file.write("### Points with fixed degrees of freedom and fixity codes (1-fixed0-free)\n")
            file.write("# ivfix  nofix       ifpre ...\n")
            count = 1
            for i, fix in self.fixno.items():
                sup = " 1  1  1" if fix==FIXED else " 1  0  0"
                file.write(" %6d %6d      %s\n" % (count, nodelist[i], sup))
                count += 1

            file.write("\n")
            file.write("# ===================================================================\n")

            file.write("\n")
            file.write("### Load case n. %8d\n" % 1)

            file.write("\n")
            file.write("### Title of the load case\n")
            file.write("Uniform distributed load\n")

            file.write("\n")
            file.write("### Load parameters\n")
            file.write("%5d # nplod (n. of point loads in nodal points)\n" % 0)
            file.write("%5d # ngrav (gravity load flag: 1-yes0-no)\n" % 0)
            file.write("%5d # nedge (n. of edge loads) (F.E.M. only)\n" % 0)
            file.write("%5d # nface (n. of face loads) (F.E.M. only)\n" % self.nelems)
            file.write("%5d # ntemp (n. of points with temperature variation) (F.E.M. only)\n" % 0)
            file.write("%5d # nudis (n. of uniformly distributed loads " % 0)
            file.write("(3d frames and trusses only)\n")
            file.write("%5d # nepoi (n. of element point loads) (3d frames and trusses only)\n" % 0)
            file.write("%5d # nprva (n. of prescribed and non zero degrees of freedom)\n" % 0)

            file.write("\n")
            file.write("### Face load (loaded element, loaded points and load value)\n")
            file.write("### (local coordinate system)\n")
            count = 0
            for i, elem in enumerate(eleTags[0]):
                file.write("# iface  loelf\n")
                file.write(" %5d %5d\n" % (i+1, i+1))
                file.write("# lopof       prfac-n   prfac-mb   prfac-mt\n")
                for j in range(nnode):
                    # inode = eleNodes[0][count]
                    inode = nodelist[eleNodes[0][count]]
                    file.write(" %5d %16.3f %16.3f %16.3f\n" % (inode, self.load, 0.0, 0.0))
                    count += 1

            file.write("\n")
            file.write("END_OF_FILE\n")

        if path.suffix.lower() == ".gldat":
            combo_file = str(path.parent / path.stem) + ".cmdat"
        
        with open(combo_file, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write("Slab mesh\n")

            file.write("### Number of combinations\n")
            file.write("      2 # ncomb (number of combinations)\n\n")

            file.write("### Combination title\n")
            file.write("G\n")
            file.write("### Combination number\n")
            file.write("# combination n. (icomb) and number off load cases in combination (ncase)\n")
            file.write("# icomb    lcase\n")
            file.write("      1        1\n")
            file.write("### Coeficients\n")
            file.write("# load case number (icase) and load coefficient (vcoef)\n")
            file.write("# icase      vcoef\n")
            file.write("      1       1.00\n")
            file.write("\n")

            file.write("### Combination title\n")
            file.write("1.35G\n")
            file.write("### Combination number\n")
            file.write("# combination n. (icomb) and number off load cases in combination (ncase)\n")
            file.write("# icomb    lcase\n")
            file.write("      2        1\n")
            file.write("### Coeficients\n")
            file.write("# load case number (icase) and load coefficient (vcoef)\n")
            file.write("# icase      vcoef\n")
            file.write("      1       1.35\n")
            file.write("\n")

            file.write("END_OF_FILE\n")

        jobname = str(path.parent / path.stem)

        ofem_file.add(mesh_file)
        ofem_file.add(combo_file)
        txt = libofempy.solver(jobname)

        options = {'csryn': 'n', 'ksres': 2, 'lcaco': 'c'}
        # codes = [ofemlib.DI_CSV, ofemlib.AST_CSV, ofemlib.EST_CSV, ofemlib.RS_CSV]
        codes = [libofempy.DI_CSV, libofempy.AST_CSV, libofempy.EST_CSV]
        txt = libofempy.results(jobname, codes, **options)

        df = libofempy.get_csv_from_ofem(jobname, libofempy.DI_CSV)
        for i in range(1, 4):
            t1 = gmsh.view.add("disp-" + str(i))
            dff = df.loc[df['icomb'] == 1]
            dff['new_label'] = dff['point'].apply(lambda x: listnode[x])
            # gmsh.view.addHomogeneousModelData(
            #         t1, 0, "slab", "NodeData", dff["point"].values, dff['disp-'+str(i)].values) 
            gmsh.view.addHomogeneousModelData(
                    t1, 0, "slab", "NodeData", dff["new_label"].values, dff['disp-'+str(i)].values) 
            gmsh.view.option.setNumber(t1, "Visible", 0)

        t1 = gmsh.view.add("deformed mesh")
        dff = df.loc[df['icomb'] == 1]
        dff['new_label'] = dff['point'].apply(lambda x: listnode[x])
        npoin = dff.shape[0]
        displ = np.stack([np.zeros(npoin), np.zeros(npoin), dff['disp-1'].values], axis=1).reshape(3*npoin)
        gmsh.view.addHomogeneousModelData(
                t1, 0, "slab", "NodeData", dff["new_label"].values, displ, numComponents=3) 

        df = libofempy.get_csv_from_ofem(jobname, libofempy.AST_CSV)
        for i in range(1, 6):
            t1 = gmsh.view.add("str_avg-" + str(i))
            dff = df.loc[df['icomb'] == 1]
            dff['new_label'] = dff['point'].apply(lambda x: listnode[x])
            gmsh.view.addHomogeneousModelData(
                    t1, 0, "slab", "NodeData", dff['new_label'].values, dff['str-'+str(i)].values) 
            gmsh.view.option.setNumber(t1, "Visible", 0)

        df = libofempy.get_csv_from_ofem(jobname, libofempy.EST_CSV)
        unique_values = [elemlist.get(item, item) for item in df["element"].unique().tolist()]
        for i in range(1, 6):
            t1 = gmsh.view.add("str_eln-" + str(i))
            dff = df.loc[df['icomb'] == 1]
            gmsh.view.addHomogeneousModelData(
                    t1, 0, "slab", "ElementNodeData", unique_values, dff['str-'+str(i)].values) 
            gmsh.view.option.setNumber(t1, "Visible", 0)

        return

    def getNodes(self):
        nodes = gmshhandler.getNodes(gmsh.model)
        return

    def getElements(self):
        elems = gmshhandler.getElementShell(gmsh.model)
        return

    def getBoundaries(self):
        bounds = gmshhandler.getBoundaries(gmsh.model)
        return
    
    def run(self):

        # Launch the GUI to see the results:
        if '-nopopup' not in sys.argv:
            gmsh.fltk.run()

        gmsh.finalize()

    
class Beam:
    def __init__(self) -> None:
        if not gmsh.is_initialized():
            gmsh.initialize()
        return
    
    def addGeometry(self, geometry: int, *args, **kwargs):
        """_summary_

        Args:
            geometry (int): _description_

        Raises:
            ValueError: _description_
        """

        gmsh.model.add("beam")
        if geometry == LINEAR2D:
            msize = 0.3 if len(args) < 2 else args[1]
            LinearBeam(args[0], msize)
        elif geometry == CURVED2D:
            msize = 0.3 if len(args) < 3 else args[2]
            CurvedBeam(args[0], args[1], msize)
        elif geometry == SPATIAL3D:
            msize = 0.3 if len(args) < 3 else args[2]
            SpatialBeam(args[0], msize)
        else:
            raise ValueError("Invalid beam geometry type.")
        
        if len(kwargs) > 0:
            self.addParameters(**kwargs)
        return

    def addParameters(self, **kwargs):
        self.fixno = {}
        # if "boundary" in kwargs:
        #     bounddary_condition = kwargs["boundary"]
        #     # if len(bounddary_condition) != len (bounds):
        #     #     raise ValueError("Invalid boundary conditions.")
        #     for i, b in enumerate(bounddary_condition):
        #         bounds, _, _ = gmsh.model.mesh.getNodes(1, i+1, includeBoundary=True)
        #         if b == FREE:
        #             pass
        #         elif b == FIXED or b == HINGE, HORIZONTAL, VERTICAL, ROTATION, HOR_ROT, VER_ROTD:
        #             for inode in bounds:
        #                 self.fixno[inode] = b if inode not in self.fixno else max(b, self.fixno[inode])
        #         else:
        #             raise ValueError("Invalid boundary conditions.")

        if "material" in kwargs:
            self.material = kwargs["material"]

        if "thick" in kwargs:
            self.thick = kwargs["thick"]

        if "load" in kwargs:
            self.load = float(kwargs["load"])

        return

    def to_ofem(self, mesh_file: str):
        """Writes a femix .gldat mesh file

        Args:
            mesh_file (str): the name of the file to be written
        """
        ndime = 3
        
        path = pathlib.Path(mesh_file)
        if path.suffix.lower() != ".gldat":
            mesh_file = path.with_suffix('').resolve() + ".gldat"

        jobname = str(path.parent / (path.stem + ".ofem"))
        ofem_file = libofempy.OfemSolverFile(jobname, overwrite=True)

        nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(1, includeBoundary=True)
        coordlist = dict(zip(nodeTags, np.arange(len(nodeTags))))
        # coords = np.array(nodeCoords).reshape(-1, 3)
        # sorted_dict_by_keys = {key: coordlist[key] for key in sorted(coordlist)}
        eleTypes, eleTags, eleNodes = gmsh.model.mesh.getElements(1)
        elemlist = dict(zip(np.arange(1, 1+len(eleTags[0])), eleTags[0]))
        self.nelems = len(eleTags[0])
        self.npoints = len(nodeTags)
        self.nmats = 1
        self.nsections = 1
        self.nspecnodes = len(self.fixno)
        ndime = 3
        props = meshio_femix[gmsh_meshio[eleTypes[0]]]
        ntype = props[0]
        nnode = props[1]

        with open(mesh_file, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write("Beam mesh\n")

            file.write("\n")
            file.write("### Main parameters\n")
            file.write("%5d # nelem (n. of elements in the mesh)\n" % self.nelems)
            file.write("%5d # npoin (n. of points in the mesh)\n" % self.npoints)
            file.write("%5d # nvfix (n. of points with fixed degrees of freedom)\n" % self.nspecnodes)
            file.write("%5d # ncase (n. of load cases)\n" % 1)
            file.write("%5d # nselp (n. of sets of element parameters)\n" % 1)
            file.write("%5d # nmats (n. of sets of material properties)\n" % 1)
            file.write("%5d # nspen (n. of sets of element nodal properties)\n" % 1)
            file.write("%5d # nmdim (n. of geometric dimensions)\n" % 2)
            file.write("%5d # nnscs (n. of nodes with specified coordinate systems)\n" % 0)
            file.write("%5d # nsscs (n. of sets of specified coordinate systems)\n" % 0)
            file.write("%5d # nncod (n. of nodes with constrained d.o.f.)\n" % 0)
            file.write("%5d # nnecc (n. of nodes with eccentric connections)\n" % 0)

            file.write("\n")
            file.write("### Sets of element parameters\n")
            file.write("# iselp\n")
            file.write(" %6d\n" % 1)
            file.write("# element parameters\n")
            file.write("%5d # ntype (n. of element type)\n" % 7)
            file.write("%5d # nnode (n. of nodes per element)\n" % props[1])
            file.write("%5d # ngauq (n. of Gaussian quadrature) (stiffness)\n" % props[3])
            file.write("%5d # ngaus (n. of Gauss points in the formulation) (stiffness)\n" % props[4])
            file.write("%5d # ngstq (n. of Gaussian quadrature) (stresses)\n" % props[5])
            file.write("%5d # ngstr (n. of Gauss points in the formulation) (stresses)\n" % props[6])

            file.write("\n")
            file.write("### Sets of material properties\n")
            file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
            file.write("# imats         young        poiss        dense        alpha\n")
            file.write("  %5d  %16.3f %16.3f %16.3f %16.3f\n" % (1,
                self.material['E'],self.material['nu'],self.material['rho'],self.material['alpha']))

            file.write("\n")
            file.write("### Sets of element nodal properties\n")
            file.write("# ispen\n")
            file.write(" %6d\n" % 1)
            file.write("# inode       barea        binet        bin2l        bin3l        bangl(deg)\n")
            for inode in range(1, nnode+1):
                file.write(" %6d     %15.3f  %15.3f   %15.3f   %15.3f   %15.3f\n" % (inode,
                    self.area, self.inertia, self.inertia2, self.inertia3, self.angle))

            file.write("\n")
            file.write("### Element parameter index, material properties index, element nodal\n")
            file.write("### properties index and list of the nodes of each element\n")
            file.write("# ielem ielps matno ielnp       lnods ...\n")
            count = 0
            for i, elem in enumerate(eleTags[0]):
                file.write(" %6d %5d %5d %5d    " % (i+1, 1, 1, 1))
                for inode in range(nnode):
                    file.write(" %8d" % eleNodes[0][count])
                    count += 1
                file.write("\n")

            file.write("\n")
            file.write("### Coordinates of the points\n")
            file.write("# ipoin            coord-x            coord-y            coord-z\n")
            icount = 1
            for i, ipoin in enumerate(nodeTags):
                node = coordlist[i+1]
                count = int(3*node)
                file.write(" %6d    %16.8lf   %16.8lf   %16.8lf\n" % (i+1, 
                            nodeCoords[count], nodeCoords[count+1], nodeCoords[count+2]))
                icount += 1

            file.write("\n")
            file.write("### Points with fixed degrees of freedom and fixity codes (1-fixed0-free)\n")
            file.write("# ivfix  nofix       ifpre ...\n")
            count = 1
            for i, fix in self.fixno.items():
                if fix==FIXED:
                    file.write(" %6d %6d      1  1  1  1  1  1\n" % (count, i))
                elif fix == HINGED:
                    file.write(" %6d %6d      1  1  1  1  0  1\n" % (count, i))
                elif fix == HORIZONTAL:
                    file.write(" %6d %6d      1  0  1  1  0  1\n" % (count, i))
                elif fix == VERTICAL:
                    file.write(" %6d %6d      0  1  1  1  0  1\n" % (count, i))
                elif fix == ROTATION:
                    file.write(" %6d %6d      0  0  1  1  1  1\n" % (count, i))
                elif fix == HOR_ROT:
                    file.write(" %6d %6d      1  0  1  1  1  1\n" % (count, i))
                elif fix == VER_ROT:
                    file.write(" %6d %6d      0  1  1  1  1  1\n" % (count, i))
                else:
                    continue

                count += 1

            file.write("\n")
            file.write("# ===================================================================\n")

            file.write("\n")
            file.write("### Load case n. %8d\n" % 1)

            file.write("\n")
            file.write("### Title of the load case\n")
            file.write("Uniform distributed load\n")

            file.write("\n")
            file.write("### Load parameters\n")
            file.write("%5d # nplod (n. of point loads in nodal points)\n" % 0)
            file.write("%5d # ngrav (gravity load flag: 1-yes0-no)\n" % 0)
            file.write("%5d # nedge (n. of edge loads) (F.E.M. only)\n" % 0)
            file.write("%5d # nface (n. of face loads) (F.E.M. only)\n" % 0)
            file.write("%5d # ntemp (n. of points with temperature variation) (F.E.M. only)\n" % 0)
            file.write("%5d # nudis (n. of uniformly distributed loads\n" % self.nelems)
            file.write("%5d # nepoi (n. of element point loads) (3d frames and trusses only)\n" % 0)
            file.write("%5d # nprva (n. of prescribed and non zero degrees of freedom)\n" % 0)

            file.write("\n")
            file.write("### Uniformly distributed load in 3d frame elements (loaded element\n")
            file.write("### and load value) (local coordinate system)\n")
            file.write("# iudis  loelu    udisl-x    udisl-y    udisl-z   udisl-tx   udisl-ty   udisl-tz\n")            
            count = 0
            for i, elem in enumerate(eleTags[0]):
                for j in range(nnode):
                    file.write(" %5d %5d %16.3f %16.3f %16.3f %16.3f %16.3f %16.3f\n" % (i, elemlist[elem], 
                                0.0, 0.0, self.load, 0.0, 0.0, 0.0))
                    count += 1

            file.write("\n")
            file.write("END_OF_FILE\n")

        if path.suffix.lower() == ".gldat":
            mesh_file = str(path.parent / path.stem) + ".cmdat"
        
        with open(mesh_file, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write("Beam mesh\n")

            file.write("### Number of combinations\n")
            file.write("      2 # ncomb (number of combinations)\n\n")

            file.write("### Combination title\n")
            file.write("G\n")
            file.write("### Combination number\n")
            file.write("# combination n. (icomb) and number off load cases in combination (ncase)\n")
            file.write("# icomb    lcase\n")
            file.write("      1        1\n")
            file.write("### Coeficients\n")
            file.write("# load case number (icase) and load coefficient (vcoef)\n")
            file.write("# icase      vcoef\n")
            file.write("      1       1.00\n")
            file.write("\n")

        jobname = str(path.parent / path.stem)
        libofempy.solver(jobname)

        options = {'csryn': 'n', 'ksres': 2}
        codes = [libofempy.DI_CSV, libofempy.AST_CSV, libofempy.EST_CSV, libofempy.RS_CSV]
        libofempy.results(jobname, codes, **options)

        df = libofempy.get_csv_from_ofem(jobname, libofempy.DI_CSV)
        for i in range(1, 4):
            t1 = gmsh.view.add("disp-" + str(i))
            gmsh.view.addHomogeneousModelData(
                    t1, 0, "beam", "NodeData", df["point"].values, df['disp-'+str(i)].values) 
            gmsh.view.option.setNumber(t1, "Visible", 0)

        df = libofempy.get_csv_from_ofem(jobname, libofempy.AST_CSV)
        for i in range(1, 6):
            t1 = gmsh.view.add("str_avg-" + str(i))
            gmsh.view.addHomogeneousModelData(
                    t1, 0, "beam", "NodeData", df['point'].values, df['str-'+str(i)].values) 
            gmsh.view.option.setNumber(t1, "Visible", 0)

        df = libofempy.get_csv_from_ofem(jobname, libofempy.EST_CSV)
        unique_values = [elemlist.get(item, item) for item in df["element"].unique().tolist()]
        for i in range(1, 6):
            t1 = gmsh.view.add("str_eln-" + str(i))
            gmsh.view.addHomogeneousModelData(
                    t1, 0, "beam", "ElementNodeData", unique_values, df['str-'+str(i)].values) 
            gmsh.view.option.setNumber(t1, "Visible", 0)

        return

    def run(self):
        # Launch the GUI to see the results:
        if '-nopopup' not in sys.argv:
            gmsh.fltk.run()

        gmsh.finalize()



