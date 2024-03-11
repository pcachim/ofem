import pathlib
#import eurocodepy as ec
from . import ofemlib
from . import ofemmesh
from .common import *

class Handler:

    @staticmethod
    def to_ofempy(struct: ofemmesh.OfemStruct, mesh_file: str):
        """Writes a femix .gldat mesh file

        Args:
            mesh_file (str): the name of the file to be written
        """
        ndime = 3

        path = pathlib.Path(mesh_file)

        jobname = str(path.parent / (path.stem + ".ofem"))
        ofem_file = ofemlib.OfemlibFile(jobname, overwrite=True)

        # nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(2, includeBoundary=True)
        # coordlist = dict(zip(nodeTags, np.arange(len(nodeTags))))
        # nodelist = dict(zip(nodeTags, np.arange(1, len(nodeTags)+1)))
        # listnode = {v: k for k, v in nodelist.items()}
        # # coords = np.array(nodeCoords).reshape(-1, 3)
        # # sorted_dict_by_keys = {key: coordlist[key] for key in sorted(coordlist)}
        # eleTypes, eleTags, eleNodes = gmsh.model.mesh.getElements(2)
        # elemlist = dict(zip(np.arange(1, 1+len(eleTags[0])), eleTags[0]))
        nelems = struct.mesh.num_elements
        npoints = struct.mesh.num_points
        ncases = struct.num_load_cases
        # materials
        nmats = struct.num_materials
        mat_types = dict(struct.materials['type'].value_counts())
        mat_map = dict(zip(struct.materials['material'].tolist(), range(1, nmats+1)))
        # sections
        nsections = struct.num_sections
        sec_types = dict(struct.element_sections['section'].value_counts())
        sec_list = struct.sections['section'].tolist()
        count = 0
        section_map = {}
        element_secs = {}
        iel = 0
        for elem in struct.elements.itertuples():
            ielem = elem.element
            sec = struct.element_sections.loc[struct.element_sections['element'] == ielem, 'section'].values[0]
            mat = struct.sections.loc[struct.sections['section'] == sec, 'material'].values[0]
            nnode = ofem_nnodes[elem.type]
            key = (sec, nnode)
            if key not in section_map:
                count += 1  
                section_map[(sec, nnode)] = count
            iel += 1
            element_secs[ielem] = [iel, section_map[(sec, nnode)], nnode, mat_map[mat]]
        # supports
        nspecnodes = struct.num_supports
        # element types
        ntypes = dict(struct.elements['type'].value_counts())
        nselp = len(ntypes)
        ndime = 3
        ele_types = [ofem_femix[n] for n in ntypes.keys()]

        # prepare the database for elments and nooes base 1
        struct.mesh.set_points_elems_id(1)
        struct.set_indexes()

        gldatname = str(path.parent / (path.stem + ".gldat"))
        with open(gldatname, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write(struct.title + "\n")

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
            for mat in struct.materials.itertuples():
                matn = mat.material 
                imat = mat_map[matn]
                mtype = mat.type.lower()
                if mtype == "isotropic":
                    file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
                    file.write("# imats         young        poiss        dense        alpha\n")
                    file.write("  %5d  %16.3f %16.3f %16.3f %16.3f\n" % 
                        (imat, mat.young, mat.poisson, mat.weight, mat.alpha))
                elif mtype == "spring":
                    file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
                    file.write("# imats         stifn        stift-1        stift-2\n")
                    file.write("# imats         subre\n")
                    file.write("  %5d  %16.3f %16.3f %16.3f %16.3f\n" % 
                        (i+1,
                        struct.materials['k'][i], 0.0, 0.0, 0.0))
                else:
                    raise ValueError("Material type not recognized")

            file.write("\n")
            file.write("### Sets of element nodal properties\n")
            for key, ispen in section_map.items():
                secname = key[0]
                nnode = key[1]
                section = struct.sections.loc[secname]
                sec_type = section.type.lower()
                file.write("# ispen\n")
                file.write(" %6d\n" % ispen)
                if sec_type == "area":
                    file.write("# inode       thick\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d     %15.3f\n" % (inode, section['thick']))
                elif sec_type == "line":
                    file.write(
                        "# inode       barea        binet        bin2l        bin3l        bangl(deg)\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d     %15.3f     %15.3f     %15.3f     %15.3f     %15.3f\n" % 
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
                ielps = ntypes[struct.elements.loc[element].type]  
                matno = values[3]
                ielnp = values[1]
                nnode = values[2]
                elemen = struct.elements.loc[element]
                etype = elemen.type
                file.write(" %6d %5d %5d %5d    " % (ielem, ielps, matno, ielnp))
                nodecolumnlist = struct.mesh.get_list_node_columns(etype)
                nodelist = elemen[ nodecolumnlist ]
                for inode in range(nnode):
                    icol = nodecolumnlist[inode]
                    inode = nodelist[icol]
                    lnode = struct.mesh.points.at[inode, 'id']
                    # file.write(" %8d" % eleNodes[0][count])
                    file.write(" %8d" % lnode)
                file.write("\n")

            file.write("\n")
            file.write("### Coordinates of the points\n")
            file.write("# ipoin            coord-x            coord-y            coord-z\n")
            icount = 1
            for point in struct.mesh.points.itertuples():
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
            for fix in struct.supports.itertuples():
                point = struct.mesh.points.loc[fix.point].id
                file.write(" %6d %6d      " % (count, point))
                if ndime == 2:
                    file.write("%6d %6d\n" % (fix.ux, fix.uy, 0))
                else:
                    file.write("%6d %6d %6d %6d %6d %6d\n" % (fix.ux, fix.uy, fix.uz, fix.rx, fix.ry, fix.rz))
                count += 1
                
            # LOADCASES - preparing the load cases
            
            
            
            # LOADCASES - writing the load cases
            for i in range(ncases):
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
                file.write("%5d # nface (n. of face loads) (F.E.M. only)\n" % nelems)
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
                        file.write(" %5d %16.3f %16.3f %16.3f\n" % (inode, load, 0.0, 0.0))
                        count += 1

            file.write("\n")
            file.write("END_OF_FILE\n")

        # LOAD COMBINATIONS
        
        cmdatname = str(path.parent / (path.stem + ".cmdat"))
        with open(cmdatname, 'w') as file:

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

        ofem_file.add(gldatname)
        ofem_file.add(cmdatname)

        return
