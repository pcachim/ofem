import gmsh
import sys
import json
import re
import numpy as np

params = [
    {
        "type":"string",
        "name":"ONELAB/Button",
        "values":["xFEM", "xFEM"],
        "visible":False,
    },
    # {
    #     "type":"number",
    #     "name":"1xFEM/3Some choice",
    #     "values":[20],
    #     "choices":[20, 10],
    #     "valueLabels":{"Choice 1": 20, "Choice 2": 10}
    # },
    {
        "type":"string",
        "name":"1xFEM/1Title",
        "values":["Problem title"]
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/10Supports/14Add support",
        "values":["select supports"],
        "attributes":{"Macro":"Action", "Aspect":"Button"},
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/10Supports/11Support list",
        "values":["111111"],
        "choices":["111111"],
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/20Sections/10Section name",
        "values":["beam"],
        "choices":["beam"]
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/20Sections/12Material",
        "values":["concrete"],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/20Sections/141Area",
        "values":[0.15],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/20Sections/142Inertia2",
        "values":[0.003],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/20Sections/143Inertia3",
        "values":[0.001],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/20Sections/144Torsion",
        "values":[0.000001],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/20Sections/16Thick",
        "values":[0.25],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/20Sections/18Design",
        "values":[0],
        "choices":[0, 1],
        "visible": False
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/20Sections/191Add frame",
        "values":["add section line"],
        "attributes":{"Macro":"Action", "Aspect":"Button"},
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/20Sections/192Add area",
        "values":["add section area"],
        "attributes":{"Macro":"Action", "Aspect":"Button"},
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/20Sections/193Add solid",
        "values":["add section solid"],
        "attributes":{"Macro":"Action", "Aspect":"Button"},
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/15Materials/10Material name",
        "values":["concrete"],
        "choices":["concrete"]
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/15Materials/11Young [E]",
        "values":[30000000]
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/15Materials/12Poisson",
        "values":[0.2],
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/15Materials/13Weight",
        "values":[25],
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/15Materials/14Thermal",
        "values":[1.0e-5],
    },
    {
        "type":"number",
        "name":"1xFEM/Geometry/15Materials/15Shear [G]",
        "values":[12500000],
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/15Materials/18Add material",
        "values":["add material"],
        "attributes":{"Macro":"Action", "Aspect":"Button"},
    },
    {
        "type":"string",
        "name":"1xFEM/Load cases/11Load cases",
        "values":["DEAD"],
        "choices":["DEAD", "ADL", "Q", "S", "Wx", "Wy", "Wx-", "Wy-", "T"]
    },
    {
        "type":"string",
        "name":"1xFEM/Load cases/12Load case name",
        "values":["New_case_name"],
        "visible": False
    },
    {
        "type":"string",
        "name":"1xFEM/Load cases/13Type",
        "values":["live"],
        "choices":["dead", "live", "snow", "wind", "seism", "temp", "other"]
    },
    {
        "type":"number",
        "name":"1xFEM/Load cases/14gravity",
        "values":["0"],
        "min":0,
        "max":1,
    },
    {
        "type":"string",
        "name":"1xFEM/Load cases/20Add case",
        "values":["add case"],
        "attributes":{"Macro":"Action", "Aspect":"Button"}
    },
    {
        "type":"number",
        "name":"1xFEM/Load cases/30Create combinations",
        "values":[0],
        "choices": [0, 1]
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/10Point loads",
        "values":["point loads"],
        "attributes":{"Macro":"Action", "Aspect":"LeftButton"},
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/11fx",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/12fy",
        "values":[0],
        "visible": False
	},
    {
        "type":"number",
        "name":"1xFEM/Loads/13fz",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/14mx",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/15my",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/16mz",
        "values":[0],
        "visible": False
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/20Line loads",
        "values":["line loads"],
        "attributes":{"Macro":"Action", "Aspect":"MiddleButton"}
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/21px",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/22py",
        "values":[0],
        "visible": False
	},
    {
        "type":"number",
        "name":"1xFEM/Loads/23pz",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/24mx",
        "values":[0],
        "visible": False
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/30Area loads",
        "values":["area loads"],
        "attributes":{"Macro":"Action", "Aspect":"RightButton"}
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/31px",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/32py",
        "values":[0],
        "visible": False
	},
    {
        "type":"number",
        "name":"1xFEM/Loads/33pz",
        "values":[0],
        "visible": False
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/4Displacements",
        "values":["displacements loads"],
        "attributes":{"Macro":"Action", "Aspect":"MiddleButton"}
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/5Temperature",
        "values":["temperature loads"],
        "attributes":{"Macro":"Action", "Aspect":"MiddleButton"}
    }
]

params_dict = { k['name']: k for k in params }

def temp():
    return False

def xfemApp():
    physical_groups = {}
    sections = []
    materials = []
    point_loads = []
    line_loads = []
    area_loads = []
    load_cases = [
        {'case': 'DEAD', 'type': 'dead', 'gravity': 1},
        {'case': 'ADL', 'type': 'dead', 'gravity': 0},
        {'case': 'Q', 'type': 'live', 'gravity': 0},
        {'case': 'S', 'type': 'snow', 'gravity': 0},
        {'case': 'Wx', 'type': 'wind', 'gravity': 0},
        {'case': 'Wy', 'type': 'wind', 'gravity': 0},
        {'case': 'Wx-', 'type': 'wind', 'gravity': 0},
        {'case': 'Wy-', 'type': 'wind', 'gravity': 0},
        {'case': 'T', 'type': 'temp', 'gravity': 0}
    ]
    
    gmsh.initialize(sys.argv)
    gmsh.option.setNumber("Geometry.Surfaces",1)

    if len(sys.argv) > 1:
        gmsh.open(sys.argv[1])

    parameters = json.dumps( list(params_dict.values()) )
    gmsh.onelab.set(parameters)

    gmsh.model.geo.add_point(0, 0, 0)
    gmsh.model.geo.add_point(1, 0, 0)
    gmsh.model.geo.add_point(1, 1, 0)
    gmsh.model.geo.add_line(1, 2)
    gmsh.model.geo.add_line(2, 3)
    gmsh.model.geo.add_line(3, 1)
    gmsh.model.geo.add_curve_loop([1, 2, 3])
    gmsh.model.geo.add_plane_surface([1])
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(2)

    def runSolver():
        with open("parameters-gmsh.json", "w") as f:
            s = gmsh.onelab.get()
            f.write(s)

        with open("parameters-gmsh.txt", "w") as f:
            diffus = gmsh.onelab.getNames("ONELAB Context/.*([0-9]+)/11Diffusivity")
            for d in diffus:
                f.write(d % "=" % gmsh.onelab.getNumber(d))

    def checkForEvent():
        action = gmsh.onelab.getString("ONELAB/Action")
        if len(action) < 1:
            # no action requested
            pass

        elif action[0] == "check":
            # database was changed: update/define new parameters depending on new
            # state
            gmsh.onelab.setString("ONELAB/Action", [""])
            # diffus = gmsh.onelab.getNames("ONELAB Context/.*([0-9]+)/11Diffusivity")
            #print("parameters = ", gmsh.onelab.get())
            print("ONELAB check...")
            print(f"before update: {params_dict["1xFEM/Geometry/15Materials/10Material name"]["values"][0]}")
            gmsh.fltk.update()
            print(f"after update: {params_dict["1xFEM/Geometry/15Materials/10Material name"]["values"][0]}")

        elif action[0] == "reset":
            # user clicked on "Reset database"
            gmsh.onelab.setString("ONELAB/Action", [""])
            gmsh.onelab.set(parameters)
            gmsh.fltk.update()

        elif action[0] == "run":
            # user clicked on "Run"
            gmsh.onelab.setString("ONELAB/Action", [""])
            runSolver()

        elif action[0] == "add material":
            material = gmsh.onelab.get_string("1xFEM/Geometry/15Materials/10Material name")[0]
            if material not in materials:
                materials.append({
                    'material': material,
                    'young': gmsh.onelab.get_number("1xFEM/Geometry/15Materials/11Young [E]")[0],
                    'poisson': gmsh.onelab.get_number("1xFEM/Geometry/15Materials/12Poisson")[0],
                    'weight': gmsh.onelab.get_number("1xFEM/Geometry/15Materials/13Weight")[0],
                    'thermal': gmsh.onelab.get_number("1xFEM/Geometry/15Materials/14Thermal")[0],
                    'shear': gmsh.onelab.get_number("1xFEM/Geometry/15Materials/15Shear [G]")[0]
                })
                params_dict["1xFEM/Geometry/15Materials/10Material name"]["choices"].append(material)
                params_list = list(params_dict.values())
                gmsh.onelab.set(json.dumps(params_list))
            
            gmsh.onelab.setString("ONELAB/Action", [""])
            gmsh.fltk.update()
            print('Added new material = ', material)

        elif action[0].startswith("add section"):
            my_list = {0: [], 1: [], 2: [], 3: []}
            gmsh.onelab.setString("ONELAB/Action", [""])

            section = gmsh.onelab.get_string("1xFEM/Geometry/20Sections/10Section name")[0]

            if section not in params_dict["1xFEM/Geometry/20Sections/10Section name"]["choices"]:
                params_dict["1xFEM/Geometry/20Sections/10Section name"]["choices"].append(section)
            params_dict["1xFEM/Geometry/20Sections/10Section name"]["values"] = [section]
                    
            params_dict["1xFEM/Geometry/20Sections/12Material"]["visible"] = True
            material = params_dict["1xFEM/Geometry/15Materials/10Material name"]["values"][0]

            params_dict["1xFEM/Geometry/20Sections/12Material"]["values"] = [material]
            params_dict["1xFEM/Geometry/20Sections/18Design"]["visible"] = True
            if action[0] == "add section line":
                dim_target = 1
                params_dict["1xFEM/Geometry/20Sections/141Area"]["visible"] = True
                params_dict["1xFEM/Geometry/20Sections/142Inertia2"]["visible"] = True
                params_dict["1xFEM/Geometry/20Sections/143Inertia3"]["visible"] = True
                params_dict["1xFEM/Geometry/20Sections/144Torsion"]["visible"] = True
                params_dict["1xFEM/Geometry/20Sections/16Thick"]["visible"] = False
            elif action[0] == "add section area":
                dim_target = 2
                params_dict["1xFEM/Geometry/20Sections/141Area"]["visible"] = False
                params_dict["1xFEM/Geometry/20Sections/142Inertia2"]["visible"] = False
                params_dict["1xFEM/Geometry/20Sections/143Inertia3"]["visible"] = False
                params_dict["1xFEM/Geometry/20Sections/144Torsion"]["visible"] = False
                params_dict["1xFEM/Geometry/20Sections/16Thick"]["visible"] = True
            elif action[0] == "add section solid":
                dim_target = 3
                params_dict["1xFEM/Geometry/20Sections/141Area"]["visible"] = False
                params_dict["1xFEM/Geometry/20Sections/142Inertia2"]["visible"] = False
                params_dict["1xFEM/Geometry/20Sections/143Inertia3"]["visible"] = False
                params_dict["1xFEM/Geometry/20Sections/144Torsion"]["visible"] = False
                params_dict["1xFEM/Geometry/20Sections/16Thick"]["visible"] = False

            params_list = list(params_dict.values())
            gmsh.onelab.set(json.dumps(params_list))
            gmsh.fltk.update()

            gmsh.fltk.setStatusMessage(
                    "Please select entities (press 'q' to finish)", True)
            while True:
                r, ent = gmsh.fltk.selectEntities()
                if gmsh.fltk.isAvailable() == 0: 
                    return 0
                if r and len(ent):
                    dim = ent[0][0]
                    if dim != dim_target:
                        continue
                    if ent[0][1] in my_list[dim]:
                        my_list[dim].remove(ent[0][1])
                    else:
                        my_list[dim].append(ent[0][1])
                    message = "Please select entities (press 'q' to finish)\n" + ''.join(str(my_list[dim]))
                    gmsh.fltk.setStatusMessage(message, True)

                else:
                    gmsh.fltk.setStatusMessage("", True)

                    sup_name = "sec: " + section
                    for dim in my_list.keys():
                        if len(my_list[dim]) > 0: # group exists
                            if (dim, section) in physical_groups.keys():
                                tag = physical_groups[(dim, section)]
                                ents = gmsh.model.getEntitiesForPhysicalGroup(dim, tag)
                                gmsh.model.remove_physical_groups([(dim, tag)])
                                ents = np.append(ents, my_list[dim])
                                gmsh.model.addPhysicalGroup(dim, ents, tag, sup_name)
                            else:
                                physical_groups[(dim, section)] = gmsh.model.addPhysicalGroup(dim, my_list[dim], name = sup_name)
                    
                    material = gmsh.onelab.getString("1xFEM/Geometry/20Sections/12Material")[0]
                    design = gmsh.onelab.getNumber("1xFEM/Geometry/20Sections/18Design")[0]
                    params_dict["1xFEM/Geometry/20Sections/12Material"]["visible"] = False
                    params_dict["1xFEM/Geometry/20Sections/18Design"]["visible"] = False
                    
                    if action[0] == "add section line":
                        area = gmsh.onelab.getNumber("1xFEM/Geometry/20Sections/141Area")[0]
                        inertia2 = gmsh.onelab.getNumber("1xFEM/Geometry/20Sections/142Inertia2")[0]
                        inertia3 = gmsh.onelab.getNumber("1xFEM/Geometry/20Sections/143Inertia3")[0]
                        torsion = gmsh.onelab.getNumber("1xFEM/Geometry/20Sections/144Torsion")[0]
                        sections.append({
                            "section": section,
                            "material": material,
                            "area": area,
                            "inertia2": inertia2,
                            "inertia3": inertia3,
                            "torsion": torsion,
                            "design": design
                        })
                        params_dict["1xFEM/Geometry/20Sections/141Area"]["visible"] = False
                        params_dict["1xFEM/Geometry/20Sections/142Inertia2"]["visible"] = False
                        params_dict["1xFEM/Geometry/20Sections/143Inertia3"]["visible"] = False
                        params_dict["1xFEM/Geometry/20Sections/144Torsion"]["visible"] = False
                        params_dict["1xFEM/Geometry/20Sections/18Design"]["visible"] = False
                    elif action[0] == "add section area":
                        thick = gmsh.onelab.getNumber("1xFEM/Geometry/20Sections/16Thick")[0]
                        sections.append({
                            "section": section,
                            "material": material,
                            "thick": thick,
                            "design": design
                        })
                        params_dict["1xFEM/Geometry/20Sections/16Thick"]["visible"] = False
                    elif action[0] == "add section solid":
                        sections.append({
                            "section": section,
                            "material": material,
                            "design": design
                        })
                    
                    params_list = list(params_dict.values())
                    gmsh.onelab.set(json.dumps(params_list))
                    gmsh.fltk.update()

                    break

            print('Added section = ', section)

        elif action[0] == "select supports":
            text = "sup: 111000"
            my_list = {0: [], 1: [], 2: [], 3: []}
            gmsh.onelab.setString("ONELAB/Action", [""])

            # Add the support to list
            # newcode = gmsh.onelab.get_string("1xFEM/Geometry/10Supports/12Code")[0]
            newcode = gmsh.onelab.get_string("1xFEM/Geometry/10Supports/11Support list")[0]
            sequence = re.findall(r'[01]{6}', newcode)[0]    
            params_dict["1xFEM/Geometry/10Supports/11Support list"]["values"] = [sequence]
            if sequence not in params_dict["1xFEM/Geometry/10Supports/11Support list"]["choices"]:     
                if params_dict["1xFEM/Geometry/10Supports/11Support list"]["choices"][0] == "":
                    params_dict["1xFEM/Geometry/10Supports/11Support list"]["choices"] = [sequence]
                else:
                    params_dict["1xFEM/Geometry/10Supports/11Support list"]["choices"].append(sequence)
            params_list = list(params_dict.values())
            gmsh.onelab.set(json.dumps(params_list))
            gmsh.fltk.update()
            
            # Select nodes/elements to add support
            gmsh.fltk.setStatusMessage(
                    "Please select an entity (or press 'q' to quit)", True)

            while True:
                r, ent = gmsh.fltk.selectEntities()
                if gmsh.fltk.isAvailable() == 0: 
                    return 0
                if r and len(ent):
                    # Add elements to lists
                    dim = ent[0][0]
                    if ent[0][1] in my_list[dim]:
                        my_list[dim].remove(ent[0][1])
                    else:
                        my_list[dim].append(ent[0][1])
                    message = "Please select an entity (or press 'q' to quit\n"
                    message += 'points: ' + ''.join(str(my_list[0])) + ' / '
                    message += 'lines: ' + ''.join(str(my_list[1])) + ' / '
                    message += 'areas: ' + ''.join(str(my_list[2]))
                    gmsh.fltk.setStatusMessage(message, True)
                else:
                    # Create or assign to physical groups
                    gmsh.fltk.setStatusMessage("", True)

                    sup_name = "sup: " + sequence
                    for dim in my_list.keys():
                        if len(my_list[dim]) > 0: # group exists
                            if (dim, sequence) in physical_groups.keys():
                                tag = physical_groups[(dim, sequence)]
                                ents = gmsh.model.getEntitiesForPhysicalGroup(dim, tag)
                                gmsh.model.remove_physical_groups([(dim, tag)])
                                ents = np.append(ents, my_list[dim])
                                gmsh.model.addPhysicalGroup(dim, ents, tag, sup_name)
                            else:
                                physical_groups[(dim, sequence)] = gmsh.model.addPhysicalGroup(dim, my_list[dim], name = sup_name)

                    break

            print('Added support = ', sup_name)

        elif action[0] == "point loads":
            my_list = {0: [], 1: [], 2: [], 3: []}
            gmsh.onelab.setString("ONELAB/Action", [""])

            params_dict["1xFEM/Loads/11fx"]["visible"] = True
            params_dict["1xFEM/Loads/12fy"]["visible"] = True
            params_dict["1xFEM/Loads/13fz"]["visible"] = True
            params_dict["1xFEM/Loads/14mx"]["visible"] = True
            params_dict["1xFEM/Loads/15my"]["visible"] = True
            params_dict["1xFEM/Loads/16mz"]["visible"] = True
            params_list = list(params_dict.values())
            gmsh.onelab.set(json.dumps(params_list))
            gmsh.fltk.update()

            gmsh.fltk.setStatusMessage(
                    "Please select an entity (or press 'q' to quit)", True)
            while True:
                r, ent = gmsh.fltk.selectEntities()
                if gmsh.fltk.isAvailable() == 0: 
                    return 0
                if r and len(ent):
                    dim = ent[0][0]
                    if dim != 0:
                        continue
                    if ent[0][1] in my_list[dim]:
                        my_list[dim].remove(ent[0][1])
                    else:
                        my_list[dim].append(ent[0][1])
                    message = "Please select an entity (or press 'q' to quit)\n" + ''.join(str(my_list[0]))
                    gmsh.fltk.setStatusMessage(message, True)

                else:
                    gmsh.fltk.setStatusMessage("", True)

                    case = gmsh.onelab.get_string("1xFEM/Load cases/11Load cases")[0]
                    fx = gmsh.onelab.getNumber("1xFEM/Loads/11fx")[0]
                    fy = gmsh.onelab.getNumber("1xFEM/Loads/12fy")[0]
                    fz = gmsh.onelab.getNumber("1xFEM/Loads/13fz")[0]
                    mx = gmsh.onelab.getNumber("1xFEM/Loads/14mx")[0]
                    my = gmsh.onelab.getNumber("1xFEM/Loads/15my")[0]
                    mz = gmsh.onelab.getNumber("1xFEM/Loads/16mz")[0]
                    
                    for ipoin in my_list[0]:
                        point_loads.append({
                            'point': ipoin,
                            'loadcase': case,
                            'fx': fx,
                            'fy': fy,
                            'fz': fz,
                            'mx': mx,
                            'my': my,
                            'mz': mz
                        })

                    params_dict["1xFEM/Loads/11fx"]["visible"] = False
                    params_dict["1xFEM/Loads/12fy"]["visible"] = False
                    params_dict["1xFEM/Loads/13fz"]["visible"] = False
                    params_dict["1xFEM/Loads/14mx"]["visible"] = False
                    params_dict["1xFEM/Loads/15my"]["visible"] = False
                    params_dict["1xFEM/Loads/16mz"]["visible"] = False
                    params_list = list(params_dict.values())
                    gmsh.onelab.set(json.dumps(params_list))
                    gmsh.fltk.update()

                    break

            print('Added point load = ', case)

        elif action[0] == "line loads":
            my_list = {0: [], 1: [], 2: [], 3: []}
            gmsh.onelab.setString("ONELAB/Action", [""])

            params_dict["1xFEM/Loads/21px"]["visible"] = True
            params_dict["1xFEM/Loads/22py"]["visible"] = True
            params_dict["1xFEM/Loads/23pz"]["visible"] = True
            params_dict["1xFEM/Loads/24mx"]["visible"] = True
            params_list = list(params_dict.values())
            gmsh.onelab.set(json.dumps(params_list))
            gmsh.fltk.update()

            gmsh.fltk.setStatusMessage(
                    "Please select an entity (or press 'q' to quit)", True)
            while True:
                r, ent = gmsh.fltk.selectEntities()
                if gmsh.fltk.isAvailable() == 0: 
                    return 0
                if r and len(ent):
                    dim = ent[0][0]
                    if dim != 1:
                        continue
                    if ent[0][1] in my_list[dim]:
                        my_list[dim].remove(ent[0][1])
                    else:
                        my_list[dim].append(ent[0][1])
                    message = "Please select an entity (or press 'q' to quit)\n" + ''.join(str(my_list[1]))
                    gmsh.fltk.setStatusMessage(message, True)

                else:
                    gmsh.fltk.setStatusMessage("", True)

                    case = gmsh.onelab.get_string("1xFEM/Load cases/11Load cases")[0]
                    fx = gmsh.onelab.getNumber("1xFEM/Loads/21px")[0]
                    fy = gmsh.onelab.getNumber("1xFEM/Loads/22py")[0]
                    fz = gmsh.onelab.getNumber("1xFEM/Loads/23pz")[0]
                    mx = gmsh.onelab.getNumber("1xFEM/Loads/24mx")[0]
                    
                    for ielem in my_list[1]:
                        line_loads.append({
                            'element': ielem,
                            'loadcase': case,
                            'fx': fx,
                            'fy': fy,
                            'fz': fz,
                            'mx': mx
                        })

                    params_dict["1xFEM/Loads/21px"]["visible"] = False
                    params_dict["1xFEM/Loads/22py"]["visible"] = False
                    params_dict["1xFEM/Loads/23pz"]["visible"] = False
                    params_dict["1xFEM/Loads/24mx"]["visible"] = False
                    params_list = list(params_dict.values())
                    gmsh.onelab.set(json.dumps(params_list))
                    gmsh.fltk.update()

                    break


            print('Added point load = ', case)

        elif action[0] == "area loads":
            my_list = {0: [], 1: [], 2: [], 3: []}
            gmsh.onelab.setString("ONELAB/Action", [""])

            params_dict["1xFEM/Loads/31px"]["visible"] = True
            params_dict["1xFEM/Loads/32py"]["visible"] = True
            params_dict["1xFEM/Loads/33pz"]["visible"] = True
            params_list = list(params_dict.values())
            gmsh.onelab.set(json.dumps(params_list))
            gmsh.fltk.update()

            gmsh.fltk.setStatusMessage(
                    "Please select an entity (or press 'q' to quit)", True)
            while True:
                r, ent = gmsh.fltk.selectEntities()
                if gmsh.fltk.isAvailable() == 0: 
                    return 0
                if r and len(ent):
                    dim = ent[0][0]
                    if dim != 2:
                        continue
                    if ent[0][1] in my_list[dim]:
                        my_list[dim].remove(ent[0][1])
                    else:
                        my_list[dim].append(ent[0][1])
                    message = "Please select an entity (or press 'q' to quit)\n" + ''.join(str(my_list[2]))
                    gmsh.fltk.setStatusMessage(message, True)

                else:
                    gmsh.fltk.setStatusMessage("", True)

                    case = gmsh.onelab.get_string("1xFEM/Load cases/11Load cases")[0]
                    fx = gmsh.onelab.getNumber("1xFEM/Loads/31px")[0]
                    fy = gmsh.onelab.getNumber("1xFEM/Loads/32py")[0]
                    fz = gmsh.onelab.getNumber("1xFEM/Loads/33pz")[0]
                    
                    for ielem in my_list[2]:
                        area_loads.append({
                            'element': ielem,
                            'loadcase': case,
                            'fx': fx,
                            'fy': fy,
                            'fz': fz
                        })

                    params_dict["1xFEM/Loads/31px"]["visible"] = False
                    params_dict["1xFEM/Loads/32py"]["visible"] = False
                    params_dict["1xFEM/Loads/33pz"]["visible"] = False
                    params_list = list(params_dict.values())
                    gmsh.onelab.set(json.dumps(params_list))
                    gmsh.fltk.update()

                    break


            print('Added point load = ', case)

        elif action[0] == 'add case':
            newcase = gmsh.onelab.get_string("1xFEM/Load cases/11Load cases")[0]
            list_cases = [d['case'] for d in load_cases]
            if newcase not in list_cases:
                ltype = gmsh.onelab.get_string("1xFEM/Load cases/13Type")[0]
                gravity = gmsh.onelab.getNumber("1xFEM/Load cases/14gravity")[0]
                load_cases.append({
                    'case': newcase,
                    'type': ltype,
                    'gravity': gravity
                })

                params_dict["1xFEM/Load cases/11Load cases"]["choices"].append(newcase)
                params_dict["1xFEM/Load cases/11Load cases"]["values"] = [newcase]
                params_list = list(params_dict.values())
                gmsh.onelab.set(json.dumps(params_list))

                print('Added new load case = ', newcase)
            
            gmsh.onelab.setString("ONELAB/Action", [""])
            gmsh.fltk.update()

        elif len(action[0]):
            gmsh.onelab.setString("ONELAB/Action", [""])
            
            print('Action to perform = ', action[0])

        return 1

    if "-nopopup" not in sys.argv:
        gmsh.fltk.initialize()
        # show the contents of the solver menu
        gmsh.fltk.openTreeItem("1xFEM/Geometry")
        gmsh.fltk.closeTreeItem("1xFEM/Geometry/10Supports")
        gmsh.fltk.closeTreeItem("1xFEM/Geometry/15Materials")
        gmsh.fltk.closeTreeItem("1xFEM/Geometry/20Sections")
        gmsh.fltk.closeTreeItem("1xFEM/Loads")
        gmsh.fltk.closeTreeItem("1xFEM/Load cases")
        while gmsh.fltk.isAvailable() and checkForEvent():
            gmsh.fltk.wait()
    else:
        runSolver()

    gmsh.finalize()

    return

if __name__ == "__main__":
	xfemApp()


