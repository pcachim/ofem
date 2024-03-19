import json

with open('ofempy-gmsh.json', 'r') as f:
    data = json.load(f)

with open('safe-gmsh.json', 'w') as f:
    json.dump(data, f, indent=4)