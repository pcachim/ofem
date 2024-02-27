import numpy as np
import pandas as pd
from pathlib import Path

ofem_tables = [
    "General",
    "CoordinateSystems",
    "Materials",
    "BarSections",
    "FrameSections",
    "SpringSections",
    "ShellSections",
    "Nodes",
    "ShellElements",
    "FrameElements",
    "PointElements",
    "VolumeElements",
    "LinearInterfaceElements",
    "SurfaceInterfaceElements",
    "Boundaries",
    "NodeBoundaries",
    "Combinations",
    "LoadCases",
    "NodalLoads",
    "Information",
]


class OfemDataFile:
    def __init__(self, fname=None):
        if fname is None:
            self._initialize()
        else:
            self.fname = fname
            self.path = Path(fname) 
            self.read()

    def read(self):
        if self.path.suffix == '.csv':
            self.data = pd.read_csv(self.fname)
        elif self.path.suffix == '.dat':
            self.data = pd.read_csv(self.fname, sep='\s+', header=None)
        elif self.path.suffix == '.xlsx':
            self.data = pd.read_excel(self.fname)
        elif self.path.suffix == '.msh':
            self.data = self.read_msh(self.fname)
        elif self.path.suffix == '.s2k':
            self.data = self.read_s2k(self.fname)
        else:
            raise ValueError(f"Unknown file type: {self.path.suffix}")

    def read_msh(self, fname):
        with open(fname, 'r') as f:
            lines = f.readlines()
        data = {'nodes': [], 'elements': [], 'boundaries': []}
        for line in lines:
            if line.startswith('$Nodes'):
                nodes = []
                for line in lines:
                    if line.startswith('$EndNodes'):
                        break
                    nodes.append([float(x) for x in line.split()])
                data['nodes'] = np.array(nodes)
            if line.startswith('$Elements'):
                elements = []
                for line in lines:
                    if line.startswith('$EndElements'):
                        break
                    elements.append([int(x) for x in line.split()])
                data['elements'] = np.array(elements)
            if line.startswith('$PhysicalNames'):
                boundaries = []
                for line in lines:
                    if line.startswith('$EndPhysicalNames'):
                        break
                    boundaries.append([int(x) for x in line.split()])
                data['boundaries'] = np.array(boundaries)
        return data

    def read_s2k(self, fname):
        with open(fname, 'r') as f:
            lines = f.readlines()
        data = {'sections': []}
        for line in lines:
            if line.startswith('TABLE:  "SECTION PROPERTIES 02"'):
                sections = []
                for line in lines:
                    if line.startswith('TABLE:  "SECTION PROPERTIES 03"'):
                        break
                    sections.append([x for x in line.split()])
                data['sections'] = np.array(sections)
        return data
    
    def _initialize(self):
        self.data = {table: pd.DataFrame() for table in ofem_tables}
        self.data["Nodes"] = pd.DataFrame(columns=["Index", "Tag", "X", "Y", "Z", "CoordSyst"])
        self.data["Elements"] = pd.DataFrame(columns=["Index", "Tag", "Type", "Section", "Nodes")
        self.data["Boundaries"] = pd.DataFrame(columns=["Index", "Tag", "Node", "DOF"])
        self.data["Materials"] = pd.DataFrame(columns=["Index", "Tag", "Type", "E", "nu", "rho", "alpha"])  
        self.data["FrameSections"] = pd.DataFrame(columns=["Index", "Tag", "Type", "A", "I2", "I3", "A2", "A3", "It", "angle"])
        self.data["ShellSections"] = pd.DataFrame(columns=["Index", "Tag", "Type", "Thick", "angle"])
        return


if __name__ == "__main__":
    test = OfemDataFile()
    print(test.data)