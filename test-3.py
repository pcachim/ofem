import math
import os
import logging
import pathlib
from src import libofempy, pyfemrun
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logging.debug("Test started.")

# pyfemrun.run("ofempy/examples/ch02/PatchTest3.pro")
pyfemrun.run("examples/ch09/frame.pro")

logging.debug("Test finished.")
