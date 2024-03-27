############################################################################
#  This Python file is part of PyFEM, the code that accompanies the book:  #
#                                                                          #
#    'Non-Linear Finite Element Analysis of Solids and Structures'         #
#    R. de Borst, M.A. Crisfield, J.J.C. Remmers and C.V. Verhoosel        #
#    John Wiley and Sons, 2012, ISBN 978-0470666449                        #
#                                                                          #
#  Copyright (C) 2011-2023. The code is written in 2011-2012 by            #
#  Joris J.C. Remmers, Clemens V. Verhoosel and Rene de Borst and since    #
#  then augmented and  maintained by Joris J.C. Remmers.                   #
#  All rights reserved.                                                    #
#                                                                          #
#  The latest stable version can be downloaded from the web-site:          #
#     http://www.wiley.com/go/deborst                                      #
#                                                                          #
#  A github repository, with the most up to date version of the code,      #
#  can be found here:                                                      #
#     https://github.com/jjcremmers/PyFEM                                  #
#                                                                          #
#  The code is open source and intended for educational and scientific     #
#  purposes only. If you use PyFEM in your research, the developers would  #
#  be grateful if you could cite the book.                                 #  
#                                                                          #
#  Disclaimer:                                                             #
#  The authors reserve all rights but do not guarantee that the code is    #
#  free from errors. Furthermore, the authors shall not be liable in any   #
#  event caused by the use of the program.                                 #
############################################################################

import sys, os, io
from pathlib import Path
sys.path.insert(0, os.getcwd() )

from datetime import datetime, timedelta

# from pyfem.io.InputReader   import InputReader
# from pyfem.io.OutputManager import OutputManager
# from pyfem.solvers.Solver   import Solver
from .pyfem.io.InputReader   import InputReader
from .pyfem.io.OutputManager import OutputManager
from .pyfem.solvers.Solver   import Solver

def run(filename: str):
  # captures the current working directory
  safe_cwd = os.getcwd()
  path = Path(safe_cwd)
  path = path / filename
  fname = path.name
  os.chdir(str(path.parent))

  # Capture the output in a StringIO object
  captured_output = io.StringIO()
  # Redirect the output of the function to the StringIO object
  original_stdout = sys.stdout
  sys.stdout = captured_output
  original_stderr = sys.stderr
  sys.stderr = captured_output

  t1 = datetime.now()
  print(f"Started at time = {t1:%Y-%m-%d %H:%M:%S}\n")

  props,globdat = InputReader( [None, fname] )

  solver = Solver        ( props , globdat )
  output = OutputManager ( props , globdat )

  while globdat.active:
    solver.run( props , globdat )
    output.run( props , globdat )

  t2 = datetime.now()
  total = (t2-t1).total_seconds()

  print(f"Finished at time = {t2:%Y-%m-%d %H:%M:%S}")
  print(f"Time elapsed = {total} [s].\n")
  print("PyFem analysis terminated successfully.")

  # Restores the original working directory
  os.chdir(safe_cwd)

  # Restore the original stdout and stderr
  sys.stdout = original_stdout
  sys.stderr = original_stderr

  # Get the captured output as a formatted string
  formatted_output = captured_output.getvalue()

  # Write output to a file
  path = Path(filename)
  fname = path.parent / path.stem
  fname = fname.with_suffix(".txt")
  with open(fname, "w") as f:
    f.write(formatted_output)

  print("PyFem analysis terminated successfully.")

