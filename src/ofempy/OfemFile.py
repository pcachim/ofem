import io
import os
import pathlib
import zipfile
import pandas as pd
import datetime


ofemfilessuffix = ['.log', 
    '.gldat', '.cmdat', '.nldat', '.srdat',
    '_gl.bin', '_re.bin', '_di.bin', '_sd.bin', '_st.bin', 
    '_nl.bin', '_sn.bin', '_ff.bin', '_st.bin',
    '_di.csv', '_avgst.csv', '_elnst.csv', 
    '_gpstr.csv', '_react.csv', '_fixfo.csv', '_csv.info']


def compress_ofem(filename: str):
    """_summary_

    Args:
        filename (str): the name of the file to be read

    Returns:
        error code: 0 if no error, 1 if error
    """""""""
    path = pathlib.Path(filename + '.ofem')
    mode = 'w' if not path.exists() else 'a'
    jobname = pathlib.Path(filename).stem
    with zipfile.ZipFile(filename + '.ofem', mode) as ofemfile:
        files = ofemfile.namelist()
        for suffix in ofemfilessuffix:
            fname = filename + suffix
            arcname = jobname + suffix
            if pathlib.Path(fname).exists() and arcname not in files:
                ofemfile.write(fname, arcname=arcname, compress_type=zipfile.ZIP_DEFLATED)

    remove_ofem_files(filename)
    return


def add_to_ofem(filename: str, file_to_add: str):
    """_summary_

    Args:
        filename (str): the name of the file to be read

    Returns:
        error code: 0 if no error, 1 if error
    """""""""
    jobname = pathlib.Path(filename).name
    with zipfile.ZipFile(filename + '.ofem', 'a') as ofemfile:
        ofemfile.write(file_to_add, arcname=jobname, compress_type=zipfile.ZIP_DEFLATED)

    os.remove(file_to_add)
    return


def remove_ofem_files(filename: str):
    for suffix in ofemfilessuffix:
        fname = filename + suffix
        if pathlib.Path(fname).exists():
            os.remove(fname)
    return


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class OfemFile:
    def __init__(self, filename: str):
        path = pathlib.Path(filename)
        if path.suffix.lower() != '.ofem':
            path = pathlib.Path(filename + ".ofem")
        mode = 'w' if not path.exists() else 'a'

        self.filename = filename
        self.path = path
        self.parent = path.parent
        self.stem = path.stem
        self.name = path.name
        self.ofemfile = None
        
        with zipfile.ZipFile(self.filename, mode) as ofemfile:
            self.ofemfile = ofemfile

        self.operations = []        
        self.operations.append({"type": "creation","comment":"","time": now()})
        return

    def ExtractAll(self):
        path = pathlib.Path(self.filename)
        with zipfile.ZipFile(self.filename, 'r') as ofemfile:
            ofemfile.extractall(path.parent)
        return

    def ExtractBin(self):
        path = pathlib.Path(self.filename)
        if path.exists():
            with zipfile.ZipFile(self.filename, 'r') as ofemfile:
                # listOfFileNames = ofemfile.namelist()
                for fileName in ofemfile.namelist():
                    if fileName.endswith('.bin'):
                        ofemfile.extract(fileName, path.parent)
        return

    def ExtractDat(self):
        path = pathlib.Path(self.filename)
        if path.exists():
            with zipfile.ZipFile(self.filename, 'r') as ofemfile:
                # listOfFileNames = ofemfile.namelist()
                for fileName in ofemfile.namelist():
                    if fileName.endswith('dat'):
                        ofemfile.extract(fileName, path.parent)
        return

    def Run(self):
        return

    def AddFile(self, filename: str, delete: bool = True):
        path = pathlib.Path(filename)

        if self.stem != path.stem:
            raise ValueError("file name '" + filename + "' does not match the ofem file name '" + self.filename + "'")
        
        arcname = path.name
        with zipfile.ZipFile(self.filename, 'a') as ofemfile:
            ofemfile.write(filename, arcname=arcname, compress_type=zipfile.ZIP_DEFLATED)

        if delete:
            os.remove(filename)
        return

    def AddFiles(self, filenames: list, delete: bool = True):
        for file in filenames:
            self.AddFile(file, delete)
        return    

    def RemoveFile(self):
        return

    def ExtractFile(self):
        return

    def Clean(self):
        for suffix in ofemfilessuffix:
            fname = self.jobname + suffix
            if pathlib.Path(fname).exists():
                os.remove(fname)
        return

    def CleanResults(self):
        # remove all '.bin' and .'csv' files in the .ofem file
        for suffix in ofemfilessuffix:
            fname = self.jobname + suffix
            if pathlib.Path(fname).exists():
                os.remove(fname)
        return

    def Remove(self):
        path = pathlib.Path(self.filename)
        if path.exists():
            path.unlink()
        return

    def ReadDataframe(self, code: str) -> pd.DataFrame:
        """reads a dataframe from the ofem file

        Args:
            code (str): type of data to read (di, elnst, avgst, gpstr, react, fixfo)

        Returns:
            pd.DataFrame: a dataframe with the data
        """

        path = pathlib.Path(self.filename)
        if code in ["di", "elnst","avgst","gpstr","react","fixfo"]:
            file_to_extract = pathlib.Path(self.jobname + '_' + code + '.csv')
        else:
            raise ValueError("code '" + code + "' not recognized")
            
        with zipfile.ZipFile(self.filename, 'r') as ofemfile:
            with ofemfile.open(file_to_extract.name) as file:
                df = pd.read_csv(file, sep=';')

        self.operations.append({"type": "readdataframe", "comment": code, "time": now()})
        return df