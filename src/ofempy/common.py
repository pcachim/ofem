# dimensions
POINT = 0
NODE = 0
LINE = 1
CURVE = 1
AREA = 2
SURFACE = 2
SURF = 2
SOLID = 3
VOLUME = 3

# supports
FREE = -1
HINGED = 0 # 1110
FIXED = 1 # 1111
HORIZONTAL = 1100
VERTICAL = 1010
ROTATION = 1001
HOR_ROT = 1101
VER_ROT = 1011

# gmsh color codes
gmsh_colors = {
    "entity": 1,
    "physical": 2,
    "type": 0
}

gmsh_ofem_types = {
    0: "point",
    1: "line",
    2: "area",
    3: "solid"}

ofem_meshio = {
    "point": "vertex",
    "line2": "line",
    "line3": "line3",
    "area3": "triangle",
    "area4": "quad",
    "area6": "triangle6", # not working
    "area8": "quad8",
    "area9": "quad9",
    "area10": "triangle10", # not working
    "solid4": "tetra",
    "solid5": "pyramid", # not working
    "solid6": "wedge", # not working
    "solid8": "hexahedron",
    "solid10": "tetra10", # not working
    "solid14": "pyramid14", # not working
    "solid18": "wedge18", # not working
    "solid20": "hexahedron20",
    "solid27": "hexahedron27"  # not working
}
meshio_ofem = {v: k for k, v in ofem_meshio.items()}

ofem_basic = {
    "point": "point",
    "line2": "line",
    "line3": "line",
    "area3": "area",
    "area4": "area",
    "area6": "area", # not working
    "area8": "area",
    "area9": "area",
    "area10": "area", # not working
    "solid4": "solid",
    "solid5": "solid", # not working
    "solid6": "solid", # not working
    "solid8": "solid",
    "solid10": "solid", # not working
    "solid14": "solid", # not working
    "solid18": "solid", # not working
    "solid20": "solid",
    "solid27": "solid"  # not working
}

ofem_gmsh = {
    "point": 15,
    "line2": 1,
    "line3": 8,
    "area3": 2,
    "area4": 3,
    "area6": 9, # not working
    "area8": 16,
    "area9": 10,
    "area10": 18, # not working
    "solid4": 4,
    "solid5": 7, # not working
    "solid6": 6, # not working
    "solid8": 5,
    "solid10": 11, # not working
    "solid14": 14, # not working
    "solid18": 13, # not working
    "solid20": 17,
    "solid27": 12  # not working
}
gmsh_ofem = {v: k for k, v in ofem_gmsh.items()}

ofem_gmsh_dim = {
    "point": 0,
    "line2": 1,
    "line3": 1,
    "area3": 2,
    "area4": 2,
    "area6": 2, # not working
    "area8": 2,
    "area9": 2,
    "area10": 2, # not working
    "solid4": 3,
    "solid5": 3, # not working
    "solid6": 3, # not working
    "solid8": 3,
    "solid10": 3, # not working
    "solid14": 3, # not working
    "solid18": 3, # not working
    "solid20": 3,
    "solid27": 3  # not working
}

ofem_nnodes = {
    "point": 1,
    "line2": 2,
    "line3": 3,
    "area3": 3,
    "area4": 4,
    "area6": 6, # not working
    "area8": 8,
    "area9": 9,
    "area10": 10, # not working
    "solid4": 4,
    "solid5": 5, # not working
    "solid6": 6, # not working
    "solid8": 8,
    "solid10": 10, # not working
    "solid14": 14, # not working
    "solid18": 18, # not working
    "solid20": 20,
    "solid27": 27  # not working
}


meshio_gmsh = {
    "line": 1,
    "triangle": 2,
    "quad": 3,
    "tetra": 4,
    "hexahedron": 5,
    "wedge": 6,
    "pyramid": 7,
    "line3": 8,
    "triangle6": 9,
    "quad9": 10,
    "tetra10": 11,
    "hexahedron27": 12,
    "wedge18": 13,
    "pyramid14": 14,
    "vertex": 15,
    "quad8": 16,
    "hexahedron20": 17,
    "triangle10": 18
}
gmsh_meshio = {v: k for k, v in meshio_gmsh.items()}

ofem_femix = {
    # ntype, nnode, nsec, gaussq, ngaus, gausqst, ngausqst, 
    "point": (0, 1, 0, 0, 0, 0, 0),
    "line2": (7, 2, 1, 1, 2, 1, 2),
    "line3": (14, 3, 1, 1, 2, 1, 2),
    "area3": (9, 3, 1, 3, 1, 3, 1), # triangle
    "area4": (9, 4, 1, 1, 2, 1, 2), # quad
    "area6": (9, 6, 1, 3, 3, 3, 3), # triangle
    "area8": (9, 8, 1, 1, 2, 1, 2), # quad
    "area9": (9, 9, 1, 1, 2, 1, 2), # quad
    "area10": (9, 10, 1, 3, 3, 3, 3), # triangle
    "solid4": (4, 4, 0, 1, 2, 1, 2), # tetra
    "solid5": (4, 5, 0, 1, 2, 1, 2), # pyramid
    "solid6": (4, 6, 0, 1, 2, 1, 2), # wedge, tetra
    "solid8": (4, 8, 0, 1, 2, 1, 2), # cube
    "solid10": (4, 10, 0, 1, 2, 1, 2),
    "solid14": (4, 14, 0, 1, 2, 1, 2),
    "solid18": (4, 18, 0, 1, 2, 1, 2),
    "solid20": (4, 20, 0, 1, 2, 1, 2), # cube
    "solid27": (4, 27, 0, 1, 2, 1, 2) # cube
}

meshio_femix = {
    "line": (7, 2, 1, 1, 2, 1, 2),
    "triangle": (9, 3, 1, 3, 1, 3, 1),
    "quad": (9, 4, 1, 1, 2, 1, 2),
    "tetra": (4, 4, 0, 1, 2, 1, 2),
    "hexahedron": (4, 8, 0, 1, 2, 1, 2),
    "wedge": (4, 6, 0, 1, 2, 1, 2),
    "pyramid": (4, 5, 0, 1, 2, 1, 2),
    "line3": (14, 3, 1, 1, 2, 1, 2),
    "triangle6": (9, 6, 1, 3, 3, 3, 3),
    "quad9": (9, 9, 1, 1, 2, 1, 2),
    "tetra10": (4, 10, 0, 1, 2, 1, 2),
    "hexahedron27": (4, 27, 0, 1, 2, 1, 2),
    "wedge18": (4, 18, 0, 1, 2, 1, 2),
    "pyramid14": (4, 14, 0, 1, 2, 1, 2),
    "vertex": (0, 1, 0, 0, 0, 0, 0),
    "quad8": (9, 8, 1, 1, 2, 1, 2),
    "hexahedron20": (4, 20, 0, 1, 2, 1, 2),
    "triangle10": (9, 10, 1, 3, 3, 3, 3)
}

meshio_sections = {
    "line": 1,
    "triangle": 2,
    "quad": 2,
    "tetra": 3,
    "hexahedron": 3,
    "wedge": 3,
    "pyramid": 3,
    "line3": 1,
    "triangle6": 2,
    "quad9": 2,
    "tetra10": 3,
    "hexahedron27": 3,
    "wedge18": 3,
    "pyramid14": 3,
    "vertex": 0,
    "quad8": 2,
    "hexahedron20": 3,
    "triangle10": 2
}

gmsh_nnode = {
    1: 2,
    2: 3,
    3: 4,
    4: 4,
    5: 8,
    6: 6,
    7: 5,
    8: 3,
    9: 6,
    10: 9,
    11: 10,
    12: 27,
    13: 18,
    14: 14,
    15: 1,
    16: 8,
    17: 20,
    18: 10
}


sections_meshio = {
    0: "point",
    1: "curve",
    2: "area",
    3: "volume",
}

sections = {
    "point": {"material": 'spring'},
    "line": {"area": 0.001, "torsion": 0.00001, "inertia2": 0.0001, "inertia3": 0.00001, "angle": 0.0, "material": 'steel'},
    "area": {"thick": 0.25, "material": 'concrete'},
    "volume": {"material": 'concrete'}
}

materials = {
    'point': {
        "young": 200000000.0,
        "poisson": 0.2,
        "weight": 77.0,
        "thermal": 1.0e-6},
    'line': {
        "young": 200000000.0,
        "poisson": 0.2,
        "weight": 77.0,
        "thermal": 1.0e-6,
        "shear": 8000000.0,
        "mass": 7850.0,
        "damping": 0.02,
        "design": "steel"},
    'area': {
        "young": 30000000.0,
        "poisson": 0.2,
        "weight": 25.0,
        "thermal": 1.0e-6,
        "shear": 8000000.0,
        "mass": 2500.0,
        "damping": 0.05,
        "design": "concrete"},
    'volume': {
        "young": 30000000.0,
        "poisson": 0.2,
        "weight": 25.0,
        "thermal": 1.0e-6,
        "shear": 8000000.0,
        "mass": 2500.0,
        "damping": 0.05,
        "design": "concrete"},
    'interface': {
        "stift": 1.0e6,
        "stifn": 1.0e10},
    'soil': {
        "subre": 1.0e6},
    'spring': {
        "stift": 1.0e6,
        "stifn": 1.0}
}


s2k_femix = {
    "frame": (7, 2, 1, 1, 2, 1, 2),
    "triangle": (9, 3, 1, 3, 3, 3, 3),
    "quad": (9, 4, 1, 1, 2, 1, 2)
}

ofemstruct_tables = [
    "General",
    "CoordinateSystems",
    "Materials",
    "BarSections",
    "FrameSections",
    "SpringSections",
    "ShellSections",
    "coords",
    "elements",
    "supports",
    "NodeBoundaries",
    "Combinations",
    "LoadCases",
    "NodalLoads",
    "Information",
]
