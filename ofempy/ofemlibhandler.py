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
        ofem_file = ofemlib.OfemSolverFile(jobname, overwrite=True)

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
        for i, k in enumerate(dict(ntypes.items())):
            ntypes[k] = i+1
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
                    file.write("  %5d  %10.3f %10.3f %10.3f %10.3f\n" % 
                        (imat, mat.young, mat.poisson, mat.weight, mat.alpha))
                elif mtype == "spring":
                    file.write("### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n")
                    file.write("# imats         stifn        stift-1        stift-2\n")
                    file.write("# imats         subre\n")
                    file.write("  %5d  %10.3f %10.3f %10.3f %10.3f\n" % 
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
                elemen = struct.elements.loc[element]
                etype = elemen.type
                ielps = ntypes[etype] 
                matno = values[3]
                ielnp = values[1]
                nnode = values[2]
                file.write(" %6d %5d %5d %5d    " % (ielem, ielps, matno, ielnp))
                if False:
                    nodecolumnlist = struct.mesh.get_list_node_columns(etype)
                    nodelist = elemen[ nodecolumnlist ]
                    for inode in range(nnode):
                        inode = nodecolumnlist[inode]
                        inode = nodelist[inode]
                        lnode = struct.mesh.points.at[inode, 'id']
                        # file.write(" %8d" % eleNodes[0][count])
                        file.write(" %8d" % lnode)
                else:
                    nodelist = elemen[ struct.mesh.get_list_node_columns(etype) ]
                    for inode in nodelist:
                        file.write(" %8d" % struct.mesh.points.at[inode , 'id'])
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

            cases = struct.get_cases()

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
                file.write("Uniform distributed load\n")

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
                file.write(" iplod  lopop    pload-x    pload-y    pload-z");
                file.write("   pload-tx   pload-ty   pload-tz\n");
                count = 1
                for poin, values in cases[case]["point"].items():
                    file.write(" %5d %5d  " % (count, struct.points.at[str(poin), 'id']))
                    file.write(" %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f" % cases[case]["poin"])
                    file.write("\n")
                    count += 1

                # FACE LOADS
                file.write("\n")
                file.write("### Face load (loaded element, loaded points and load value)\n")
                file.write("### (local coordinate system)\n")
                count = 1
                for elem, values in cases[case]["area"].items():
                    file.write("# iface  loelf\n")
                    file.write(" %6d %6d\n" % (count, struct.elements.at[str(elem), 'id']))
                    file.write("# lopof     prfac-s1   prfac-s2    prfac-n  prfac-ms2  prfac-ms1\n")      
                    etype = struct.elements.loc[elem].type
                    nodelist = elemen[ struct.mesh.get_list_node_columns(etype) ]
                    for inode in nodelist:
                        file.write(" %6d" % struct.mesh.points.at[inode , 'id'])
                        file.write(" %10.3f %10.3f %10.3f %10.3f %10.3f\n" % 
                            (values[0], values[1], values[2], 0.0, 0.0))
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
                    file.write(" %5d %5d  " % (count, struct.elements.at[str(elem), 'id']))
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

        # LOAD COMBINATIONS

        combos = struct.get_combos()
        cmdatname = str(path.parent / (path.stem + ".cmdat"))

        with open(cmdatname, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write(struct.title + "\n")

            file.write("### Number of combinations\n")
            file.write("%6d # ncomb (number of combinations)\n\n" % len(combos))

            for i, combo in enumerate(combos.keys()):
                file.write("### Combination title\n")
                file.write(combo + "\n")
                file.write("### Combination number\n")
                file.write("# combination n. (icomb) and number of load cases in combination (ncase)\n")
                file.write("# icomb    lcase\n")
                file.write(" %6d   %6d\n" % (i+1, len(combos[combo]['coefs'])))
                file.write("### Coeficients\n")
                file.write("# load case number (icase) and load coefficient (vcoef)\n")
                file.write("# icase      vcoef\n")
                for icase, coef in combos[combo]['coefs'].items():
                    file.write(" %6d  %10.3f\n" % (cases[icase]['index'], coef))
                file.write("\n")

            file.write("END_OF_FILE\n")

        ofem_file.add(gldatname)
        ofem_file.add(cmdatname)

        return
