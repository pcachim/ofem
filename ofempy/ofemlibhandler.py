import sys
import gmsh
import numpy as np
import pathlib
#import eurocodepy as ec
from . import ofemlib
from . import ofemmesh
from .common import *
from . import ofemgmsh

class Handler:

    def to_ofem(self, struct: ofemmesh.OfemStruct, mesh_file: str):
        """Writes a femix .gldat mesh file

        Args:
            mesh_file (str): the name of the file to be written
        """
        ndime = 3

        path = pathlib.Path(mesh_file)

        jobname = str(path.parent / (path.stem + ".ofem"))
        ofem_file = ofemlib.OfemlibFile(jobname, overwrite=True)

        nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes(2, includeBoundary=True)
        coordlist = dict(zip(nodeTags, np.arange(len(nodeTags))))
        nodelist = dict(zip(nodeTags, np.arange(1, len(nodeTags)+1)))
        listnode = {v: k for k, v in nodelist.items()}
        # coords = np.array(nodeCoords).reshape(-1, 3)
        # sorted_dict_by_keys = {key: coordlist[key] for key in sorted(coordlist)}
        eleTypes, eleTags, eleNodes = gmsh.model.mesh.getElements(2)
        # elemlist = dict(zip(np.arange(1, 1+len(eleTags[0])), eleTags[0]))
        self.nelems = struct.mesh.num_elements
        self.npoints = struct.mesh.num_points
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
        self.nspecnodes = struct.num_supports
        # element types
        ntypes = dict(struct.elements['type'].value_counts())
        nselp = len(ntypes)
        ndime = 3
        ele_types = [ofem_femix[n] for n in ntypes.keys()]

        with open(mesh_file, 'w') as file:

            file.write("### Main title of the problem\n")
            file.write("Slab mesh\n")

            file.write("\n")
            file.write("### Main parameters\n")
            file.write("%5d # nelem (n. of elements in the mesh)\n" % self.nelems)
            file.write("%5d # npoin (n. of points in the mesh)\n" % self.npoints)
            file.write("%5d # nvfix (n. of points with fixed degrees of freedom)\n" % self.nspecnodes)
            file.write("%5d # ncase (n. of load cases)\n" % 1)
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
                section = struct.sections.loc[struct.sections['section'] == secname]
                sec_type = str(section['type'].values[0]).lower()
                file.write("# ispen\n")
                file.write(" %6d\n" % ispen)
                if sec_type == "area":
                    file.write("# inode       thick\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d     %15.3f\n" % (inode, section['thick'].values[0]))
                elif sec_type == "line":
                    file.write(
                        "# inode       barea        binet        bin2l        bin3l        bangl(deg)\n")
                    for inode in range(1, nnode+1):
                        file.write(" %6d     %15.3f     %15.3f     %15.3f     %15.3f     %15.3f\n" % 
                            (inode, section["area"].values[0], section["torsion"].values[0],
                            section["inertia2"].values[0], section["inertia3"].values[0], section["angle"].values[0]))
                else:
                    raise ValueError("Section type not recognized")
                        
            file.write("\n")
            file.write("### Element parameter index, material properties index, element nodal\n")
            file.write("### properties index and list of the nodes of each element\n")
            file.write("# ielem ielps matno ielnp       lnods ...\n")
            count = 0
            for element, values in element_secs:
                ielem = values[0]
                ielps = ntypes[struct.elements.loc[struct.elements['element'] == element, 'type'].values[0]]    
                matno = values[3]
                ielnp = values[1]
                nnode = values[2]
                file.write(" %6d %5d %5d %5d    " % (ielem, ielps, matno, ielnp))
                for inode in range(nnode):
        ### mudar a lista para numeral
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
        txt = ofemlib.ofemSolver(jobname)

        options = {'csryn': 'n', 'ksres': 2, 'lcaco': 'c'}
        # codes = [ofemlib.DI_CSV, ofemlib.AST_CSV, ofemlib.EST_CSV, ofemlib.RS_CSV]
        codes = [ofemlib.DI_CSV, ofemlib.AST_CSV, ofemlib.EST_CSV]
        txt = ofemlib.ofemResults(jobname, codes, **options)

        df = ofemlib.get_csv_from_ofem(jobname, ofemlib.DI_CSV)
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

        df = ofemlib.get_csv_from_ofem(jobname, ofemlib.AST_CSV)
        for i in range(1, 6):
            t1 = gmsh.view.add("str_avg-" + str(i))
            dff = df.loc[df['icomb'] == 1]
            dff['new_label'] = dff['point'].apply(lambda x: listnode[x])
            gmsh.view.addHomogeneousModelData(
                    t1, 0, "slab", "NodeData", dff['new_label'].values, dff['str-'+str(i)].values) 
            gmsh.view.option.setNumber(t1, "Visible", 0)

        df = ofemlib.get_csv_from_ofem(jobname, ofemlib.EST_CSV)
        unique_values = [elemlist.get(item, item) for item in df["element"].unique().tolist()]
        for i in range(1, 6):
            t1 = gmsh.view.add("str_eln-" + str(i))
            dff = df.loc[df['icomb'] == 1]
            gmsh.view.addHomogeneousModelData(
                    t1, 0, "slab", "ElementNodeData", unique_values, dff['str-'+str(i)].values) 
            gmsh.view.option.setNumber(t1, "Visible", 0)

        return
