/*********************************************************************/
/*                                                                   */
/* wrigldat                                                          */
/* Writes the s3dmesh data in a _gl.dat format.                      */
/*                                                                   */
/* Version: 1.0                                                      */
/* Date   : 18-07-1994                                               */
/* Authors: Paulo Cachim                                             */
/*                                                                   */
/*********************************************************************/

#include <math.h>
#include <stdio.h>
#include <string.h>
#include <aa/cutil.h>
#include <hc/hcfile.h>
#include <hc/hcstring.h>
#include <s3d.h>

/*  ntype:          1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 */
int n_dofn[] = { 0, 2, 2, 2, 3, 3, 6, 6, 3, 6, 3, 2, 3, 3, 3, 3, 2 };
int n_dime[] = { 0, 2, 2, 2, 3, 2, 3, 3, 3, 3, 3, 2, 3, 2, 2, 3, 2 };

void wrigldat (
   int nmats,
   int nselp,
   int nspen,
   int *ielnp,
   int *ielps,
   int *matno,
   int *n_mats,
   int *n_spen,
   int *ns_nod,
   int *ns_typ,
   s3dmesh mesh,
   char *jname
) {

   int idime;
   int idofn;
   int ielem;
   int imats;
   int ispen;
   int inode;
   int ipoin;
   int ipren;
   int iprop;
   int iselp;
   int ivfix;
   int ldime;
   int ndime;
   int ndofn;
   int nnode;
   int ntype;
   int *cdofn;
   char repyn;
   char ermsg[82];
   char fname[82];
   FILE *cha60;

/* Open the output file */

   strcpy (fname,jname);
   strcat (fname,"_gl.dat");
   if (ExistFile (fname)) {
      wwamsg ("File exists!",0);
      askcha ("Overwrite",'y','n','n',&repyn);
      if (repyn == 'n') return;
   } /* if */
   cha60=OpenFile (fname,"w");

/* Calculate some auxiliary parameters */

   for (iselp=1, ndime=0 ; iselp <= nselp ; iselp++) {
      ntype=ns_typ[iselp];
      ldime=n_dime[ntype];
      if (ndime == 0) ndime=ldime;
      if (ndime != ldime) wermsg ("Elements must be all 2D or all 3D",0);
   } /* for (iselp) */

   dimei1 (&cdofn,mesh.npoin);   zeroi1 (cdofn,mesh.npoin);

   for (ielem=1 ; ielem <= mesh.nelem ; ielem++) {
      iselp=ielps[ielem];
      ntype=ns_typ[iselp];
      ndofn=n_dofn[ntype];
      for (inode=1 ; inode <= mesh.lnode[ielem] ; inode++) {
         ipoin=mesh.lnods[ielem][inode];
         if (ndofn > cdofn[ipoin]) cdofn[ipoin]=ndofn;
      } /* for (inode) */
   } /* for (ielem) */

/* Write file jobname_gl.dat */

   fprintf (cha60,"### Main title of the problem\n");
   fprintf (cha60,"Main title - Units (F,L)\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Main parameters\n");
   fprintf (cha60,"%5d # nelem (n. of elements in the mesh)\n",mesh.nelem);
   fprintf (cha60,"%5d # npoin (n. of points in the mesh)\n",mesh.npoin);
   fprintf (cha60,
   "%5d # nvfix (n. of points with fixed degrees of freedom)\n",mesh.nvfix);
   fprintf (cha60,"%5d # ncase (n. of load cases)\n",1);
   fprintf (cha60,"%5d # nselp (n. of sets of element parameters)\n",nselp);
   fprintf (cha60,
   "%5d # nmats (n. of sets of material properties)\n",nmats);
   fprintf (cha60,
   "%5d # nspen (n. of sets of element nodal properties)\n",nspen);
   fprintf (cha60,
   "%5d # nmdim (n. of geometric dimensions)\n",ndime);
   fprintf (cha60,
   "%5d # nnscs (n. of nodes with specified coordinate systems)\n",0);
   fprintf (cha60,
   "%5d # nsscs (n. of sets of specified coordinate systems)\n",0);
   fprintf (cha60,
   "%5d # nncod (n. of nodes with constrained d.o.f.)\n",0);
   fprintf (cha60,
   "%5d # nnecc (n. of nodes with eccentric connections)\n",0);

   fprintf (cha60,"\n");
   fprintf (cha60,"### Sets of element parameters\n");

   for (iselp=1 ; iselp <= nselp ; iselp++) {
      fprintf (cha60,"# iselp\n");
      fprintf (cha60," %6d\n",iselp);
      fprintf (cha60,"# element parameters\n");
      fprintf (cha60,
         "%5d # ntype (n. of element type)\n",ns_typ[iselp]);
      fprintf (cha60,
         "%5d # nnode (n. of nodes per element)\n",ns_nod[iselp]);
      fprintf (cha60,
         "%5d # ngauq (n. of Gaussian quadrature) (stiffness)\n",1);
      fprintf (cha60,
         "%5d # ngaus (n. of Gauss points in the formulation) (stiffness)\n",2);
      fprintf (cha60,
         "%5d # ngstq (n. of Gaussian quadrature) (stresses)\n",1);
      fprintf (cha60,
         "%5d # ngstr (n. of Gauss points in the formulation) (stresses)\n",2);
   } /* for (ltype) */

   fprintf (cha60,"\n");
   fprintf (cha60,"### Sets of material properties\n");
   fprintf (cha60,
   "### (Young modulus, Poisson ratio, mass/volume and thermic coeff.\n");
   fprintf (cha60,
   "###  Modulus of subgrade reaction, normal and shear stifness)\n");

   for (imats=1 ; imats <= nmats ; imats++) {
      ntype=n_mats[imats];
      if (ntype == 10) {
         fprintf (cha60,"# imats         subre\n");
         fprintf (cha60,"  %5d        1.0e+7\n",imats);
      } else if (ntype == 11 || ntype == 12) {
         fprintf (cha60,"# imats         stift        stifn\n");
         fprintf (cha60,"  %5d        1.0e+2       1.0e+9\n",imats);
      } else {
         fprintf (cha60,
         "# imats         young        poiss        dense        alpha\n");
         fprintf (cha60,
         "  %5d       29.0e+6         0.20          ",imats);
	 fprintf (cha60,"2.5       1.0e-5\n");
      } /* if */
   } /* for (iselp) */

   fprintf (cha60,"\n");
   fprintf (cha60,"### Sets of element nodal properties\n");

   for (ispen=1 ; ispen <= nspen ; ispen++) {
      iselp=n_spen[ispen];
      ntype=ns_typ[iselp];
      nnode=ns_nod[iselp];

      fprintf (cha60,"# ispen\n");
      fprintf (cha60," %6d\n",ispen);
      if (ntype == 1 || ntype == 5 || ntype == 6 || ntype == 9 || ntype == 11 || ntype == 12) {
         fprintf (cha60,"# inode       thick\n");
         for (inode=1 ; inode <= nnode ; inode++) {
            fprintf (cha60," %6d        0.25\n",inode);
         } /* for (inode) */
      } else if (ntype == 7) {
         fprintf (cha60,"# inode       barea        binet");
         fprintf (cha60,"        bin2l        bin3l        bangl(deg)\n");
         for (inode=1 ; inode <= nnode ; inode++) {
            fprintf (cha60," %6d        0.01       1.0e-3",inode);
            fprintf (cha60,"      1.0e-3        1.0e-4     0.0\n",inode);
         } /* for (inode) */
      } else if (ntype == 13 || ntype == 14) {
         fprintf (cha60,"# inode       barea        biner\n");
         for (inode=1 ; inode <= nnode ; inode++) {
            fprintf (cha60," %6d        0.01       1.0e-3\n",inode);
         } /* for (inode) */
      } else if (ntype == 15) {
         fprintf (cha60,"# inode        barea        binet");
         fprintf (cha60,"        bin2l        bin3l        eccen(deg)\n");
         for (inode=1 ; inode <= nnode ; inode++) {
            fprintf (cha60," %6d        0.01       1.0e-3",inode);
            fprintf (cha60,"      1.0e-3        1.0e-4    -0.2\n",inode);
         } /* for (inode) */
      } else if (ntype == 8 || ntype == 16) {
         fprintf (cha60,"# inode        barea\n");
         for (inode=1 ; inode <= nnode ; inode++) {
            fprintf (cha60," %6d        0.25\n",inode);
         } /* for (inode) */
      } /* if */
   } /* for (ispen) */

   fprintf (cha60,"\n");
   fprintf (cha60,
   "### Element parameter index, material properties index, element nodal\n");
   fprintf (cha60,
   "### properties index and list of the nodes of each element\n");
   fprintf (cha60,"# ielem ielps matno ielnp       lnods ...\n");

   for (ielem=1 ; ielem <= mesh.nelem ; ielem++) {

      fprintf (cha60," %6d %5d %5d",ielem,ielps[ielem],matno[ielem]);

      if (ielnp[ielem]) {
         fprintf (cha60," %5d",ielnp[ielem]);
      } else {
         fprintf (cha60,"      ");
      } /* if */

      for (inode=1 ; inode <= mesh.lnode[ielem] ; inode++) {
         fprintf (cha60," %5d",mesh.lnods[ielem][inode]);
      } /* for (inode) */

      fprintf (cha60,"\n");

   } /* for (ielem) */

   fprintf (cha60,"\n");
   fprintf (cha60,"### Coordinates of the points\n");
   if (ndime == 2) {
      fprintf (cha60,
      "# ipoin            coord-x            coord-y\n");
   } else {
      fprintf (cha60,
      "# ipoin            coord-x            coord-y            coord-z\n");
   } /* if */
   for (ipoin=1 ; ipoin <= mesh.npoin ; ipoin++) {
      fprintf (cha60," %6d ",ipoin);
      for (idime=1 ; idime <= ndime ; idime++) {
         fprintf (cha60,"   %16.8lf",mesh.coord[ipoin][idime]);
      } /* for (idime) */
      fprintf (cha60,"\n");
   } /* for (ipoin) */

   fprintf (cha60,"\n");
   fprintf (cha60,
"### Points with fixed degrees of freedom and fixity codes (1-fixed;0-free)\n");
   fprintf (cha60,"# ivfix  nofix       ifpre ...\n");
   for (ivfix=1 ; ivfix <= mesh.nvfix ; ivfix++) {
      ipoin=mesh.nofix[ivfix];
      ndofn=cdofn[ipoin];
      fprintf (cha60,"%6d %6d   ",ivfix,ipoin);
#if 1
      for (idofn=1 ; idofn <= ndofn ; idofn++) {
         fprintf (cha60,"%3d",1);
      } /* for (idofn) */
#else
      if (fabs (mesh.coord[ipoin][1]-0.0) < 1.0e-5 ||
          fabs (mesh.coord[ipoin][1]-10.001) < 1.0e-5) {
         fprintf (cha60,"%3d",1);
      } else {
         fprintf (cha60,"%3d",0);
      } /* if */
      if (fabs (mesh.coord[ipoin][2]-0.0) < 1.0e-5 ||
          fabs (mesh.coord[ipoin][2]-7.0) < 1.0e-5) {
         fprintf (cha60,"%3d",1);
      } else {
         fprintf (cha60,"%3d",0);
      } /* if */
      if (fabs (mesh.coord[ipoin][3]+2.74) < 1.0e-5) {
         fprintf (cha60,"%3d",1);
      } else {
         fprintf (cha60,"%3d",0);
      } /* if */
#endif
      fprintf (cha60,"\n");
         
   } /* for (ivfix) */

   fprintf (cha60,"\n");
   fprintf (cha60,"### Sets of specified coordinate systems\n");
   fprintf (cha60,"# isscs\n");
   fprintf (cha60,"# ivect    vect1    vect2    vect3\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Nodes with specified coordinate systems\n");
   fprintf (cha60,"# inscs inosp itycs\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Nodes with linear constraints\n");
   fprintf (cha60,"# incod\n");
   fprintf (cha60,"# csnod csdof nmnod\n");
   fprintf (cha60,"# imnod cmnod cmdof  wedof\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Nodes with eccentric connections\n");
   fprintf (cha60,"# inecc  esnod   emnod    eccen...\n");

   fprintf (cha60,"\n");
   fprintf (cha60,
   "# ===================================================================\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Load case n. %8d\n",1);

   fprintf (cha60,"\n");
   fprintf (cha60,"### Title of the load case\n");
   fprintf (cha60,"First load case title\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Load parameters\n");
   fprintf (cha60,
"%5d # nplod (n. of point loads in nodal points)\n",0);
   fprintf (cha60,
"%5d # ngrav (gravity load flag: 1-yes;0-no)\n",0);
   fprintf (cha60,
"%5d # nedge (n. of edge loads) (F.E.M. only)\n",0);
   fprintf (cha60,
"%5d # nface (n. of face loads) (F.E.M. only)\n",0);
   fprintf (cha60,
"%5d # ntemp (n. of points with temperature variation) (F.E.M. only)\n",0);
   fprintf (cha60,
"%5d # nudis (n. of uniformly distributed loads ",0);
   fprintf (cha60,"(3d frames and trusses only)\n");
   fprintf (cha60,
"%5d # nepoi (n. of element point loads) (3d frames and trusses only)\n",0);
   fprintf (cha60,
"%5d # nprva (n. of prescribed and non zero degrees of freedom)\n",0);
 
   fprintf (cha60,"\n");
   fprintf (cha60,
   "### Point loads in nodal points (loaded point and load value)\n");
   fprintf (cha60,"### (global coordinate system)\n");
   fprintf (cha60,"### ntype =          1,2,3\n");
   fprintf (cha60,"# iplod  lopop    pload-x  pload-y\n");
   fprintf (cha60,"### ntype =            4,8\n");
   fprintf (cha60,"# iplod  lopop    pload-x  pload-y  pload-z\n");
   fprintf (cha60,"### ntype =              5\n");
   fprintf (cha60,"# iplod  lopop    pload-z pload-tx pload-ty\n");
   fprintf (cha60,"### ntype =      4,6,7,8,9\n");
   fprintf (cha60,"# iplod  lopop    pload-x  pload-y  pload-z");
   fprintf (cha60," pload-tx pload-ty pload-tz\n");
   fprintf (cha60,"### ntype =          13,14\n");
   fprintf (cha60,"# iplod  lopop    pload-x  pload-y pload-tz\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Gravity load (gravity acceleration)\n");
   fprintf (cha60,"### (global coordinate system)\n");
   fprintf (cha60,"### ntype = 1,2,3,13,14,16\n");
   fprintf (cha60,"#      gravi-x      gravi-y\n");
   fprintf (cha60,"### ntype =              5\n");
   fprintf (cha60,"#      gravi-z\n");
   fprintf (cha60,"### ntype =   4,6,7,8,9,15\n");
   fprintf (cha60,"#      gravi-x      gravi-y      gravi-z\n");

   fprintf (cha60,"\n");
   fprintf (cha60,
   "### Edge load (loaded element, loaded points and load value)\n");
   fprintf (cha60,"### (local coordinate system)\n");
   fprintf (cha60,"# iedge  loele\n");
   fprintf (cha60,"### ntype = 1,2,3,13,14\n");
   fprintf (cha60,"# lopoe       press-t   press-n\n");
   fprintf (cha60,"### ntype =           4\n");
   fprintf (cha60,"# lopoe       press-t   press-nt   press-nn\n");
   fprintf (cha60,"# lopon ...\n");
   fprintf (cha60,"### ntype =           5\n");
   fprintf (cha60,"# lopoe       press-n   press-mb   press-mt\n");
   fprintf (cha60,"### ntype =         6,9\n");
   fprintf (cha60,"# lopoe       press-t   press-nt   press-nn");
   fprintf (cha60,"   press-mb   press-mt\n");

   fprintf (cha60,"\n");
   fprintf (cha60,
   "### Face load (loaded element, loaded points and load value)\n");
   fprintf (cha60,"### (local coordinate system)\n");
   fprintf (cha60,"# iface  loelf\n");
   fprintf (cha60,"### ntype = 1,2,3\n");
   fprintf (cha60,"# lopof      prfac-s1   prfac-s2\n");
   fprintf (cha60,"### ntype =     4\n");
   fprintf (cha60,"# lopof      prfac-s1   prfac-s2    prfac-n\n");
   fprintf (cha60,"### ntype =     5\n");
   fprintf (cha60,"# lopof       prfac-n   prfac-mb   prfac-mt\n");
   fprintf (cha60,"### ntype =   6,9\n");
   fprintf (cha60,"# lopof      prfac-s1   prfac-s2    prfac-n");
   fprintf (cha60,"  prfac-ms2  prfac-ms1\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Uniformly distributed load in 3d frame ");
   fprintf (cha60,"or truss elements (loaded element\n");
   fprintf (cha60,"### and load value) (local coordinate system)\n");
   fprintf (cha60,"### ntype =     7\n");
   fprintf (cha60,"# iudis  loelu    udisl-x    udisl-y    udisl-z  ");
   fprintf (cha60," udisl-tx   udisl-ty   udisl-tz\n");
   fprintf (cha60,"### ntype =     8\n");
   fprintf (cha60,"# iudis  loelu    udisl-x    udisl-y    udisl-z\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"### Element point load in 3d frame or truss ");
   fprintf (cha60,"elements (loaded element, distance\n");
   fprintf (cha60,"### to the left end and load value) ");
   fprintf (cha60,"(global coordinate system)\n");
   fprintf (cha60,"### ntype =     7\n");
   fprintf (cha60,"# iepoi loelp   xepoi   epoil-x  epoil-y  epoil-z");
   fprintf (cha60," epoil-tx epoil-ty epoil-tz\n");
   fprintf (cha60,"### ntype =     8\n");
   fprintf (cha60,"# iepoi loelp   xepoi   epoil-x  epoil-y  epoil-z\n");

   fprintf (cha60,"\n");
   fprintf (cha60,
   "### Thermal load (loaded point and temperature variation)\n");
   fprintf (cha60,"# itemp  lopot     tempn\n");

   fprintf (cha60,"\n");
   fprintf (cha60,
"### Prescribed variables (point, degree of freedom and prescribed value)\n");
   fprintf (cha60,"### (global coordinate system)\n");
   fprintf (cha60,"# iprva  nnodp  ndofp    prval\n");

   fprintf (cha60,"\n");
   fprintf (cha60,"END_OF_FILE\n");

   fclose (cha60);

} /* wrigldat */
