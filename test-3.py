import math
import os
import logging
import pathlib
from ofempy import libofempy, pyfemrun
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.")

# pyfemrun.run("modelmsh/examples/ch02/PatchTest3.pro")
pyfemrun.run("examples/ch09/frame.pro")

logging.debug("Test finished.")
