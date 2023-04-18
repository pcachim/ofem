import os
import pandas as pd
import pathlib
import zipfile
from . import femixlib


class ofem_handler:

    def __init__(self, fname):
        self._fname = fname
        self._ofem = fname + '.ofem'

        self.path = pathlib.Path(fname)

    @property
    def jobname(self):
        return self._fname

    def to_ofem(self):
        """
        Convert a GLDAT file to OFEM file
        """
        femixlib.convert_to_ofem(self._fname)
