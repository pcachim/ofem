import modelmsh as msh
import math
import os
import logging
import pathlib
from modelmsh import ofemlib
from pathlib import Path
from modelmsh import pyfemrun

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.")

# pyfemrun.run("modelmsh/examples/ch02/PatchTest3.pro")
pyfemrun.run("modelmsh/examples/ch09/frame.pro")

logging.debug("Test finished.")
