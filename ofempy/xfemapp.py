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
        "closed": True
    },
    {
        "type":"number",
        "name":"1xFEM/3Some choice",
        "values":[20],
        "choices":[20, 10],
        "valueLabels":{"Choice 1": 20, "Choice 2": 10}
    },
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
        "closed": False
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/10Supports/11Support list",
        "values":[""],
        "choices":[""],
        "closed": False
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/10Supports/12Code",
        "values":["111000"],
        "visible": False
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/20Sections/1Section name",
        "values":["select"],
        "choices":["linesec", "areasec", "solidsec"]
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/30Materials/1Material name",
        "values":["select"],
        "choices":["concrete", "steel", "timber"]
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

def xfemApp():
    physical_groups = {}
    supports = []
    point_loads = []
    line_loads = []
    area_loads = []
    load_cases = [
        {'name': 'DEAD', 'type': 'dead', 'gravity': 1},
        {'name': 'ADL', 'type': 'dead', 'gravity': 0},
        {'name': 'Q', 'type': 'live', 'gravity': 0},
        {'name': 'S', 'type': 'snow', 'gravity': 0},
        {'name': 'Wx', 'type': 'wind', 'gravity': 0},
        {'name': 'Wy', 'type': 'wind', 'gravity': 0},
        {'name': 'Wx-', 'type': 'wind', 'gravity': 0},
        {'name': 'Wy-', 'type': 'wind', 'gravity': 0},
        {'name': 'T', 'type': 'temp', 'gravity': 0}
    ]
    
    gmsh.initialize(sys.argv)

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
    # gmsh.model.addPhysicalGroup(1, [1], name = "sup: 111000")	
    # gmsh.model.addPhysicalGroup(2, [1], name = "asec: laje")	
    # gmsh.model.addPhysicalGroup(1, [1], name = "lsec: viga")
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
            diffus = gmsh.onelab.getNames("ONELAB Context/.*([0-9]+)/11Diffusivity")
            #print("parameters = ", gmsh.onelab.get())
            s = gmsh.onelab.getString('1xFEM/Loads/1Test')
            print("ONELAB check...")
            gmsh.fltk.update()

        elif action[0] == "reset":
            # user clicked on "Reset database"
            gmsh.onelab.setString("ONELAB/Action", [""])
            gmsh.onelab.set(parameters)
            gmsh.fltk.update()

        elif action[0] == "run":
            # user clicked on "Run"
            gmsh.onelab.setString("ONELAB/Action", [""])
            runSolver()

        elif action[0] == "check pysical":
            pass

        elif action[0] == "select supports":
            text = "sup: 111000"
            my_list = {0: [], 1: [], 2: [], 3: []}
            gmsh.onelab.setString("ONELAB/Action", [""])

            # Add the support to list
            newcode = gmsh.onelab.get_string("1xFEM/Geometry/10Supports/12Code")[0]
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
            newcase = gmsh.onelab.get_string("1xFEM/Load cases/12Load case name")[0]
            ltype = gmsh.onelab.get_string("1xFEM/Load cases/13Type")[0]
            gravity = gmsh.onelab.getNumber("1xFEM/Load cases/14gravity")[0]
            load_cases.append({
                'name': newcase,
                'type': ltype,
                'gravity': gravity
            })
            
            params_dict["1xFEM/Load cases/11Load cases"]["choices"].append(newcase)
            params_list = list(params_dict.values())
            gmsh.onelab.set(json.dumps(params_list))
            
            gmsh.onelab.setString("ONELAB/Action", [""])
            gmsh.fltk.update()
            print('Added new load case = ', newcase)

        elif len(action[0]):
            gmsh.onelab.setString("ONELAB/Action", [""])
            
            print('Action to perform = ', action[0])

        return 1

    if "-nopopup" not in sys.argv:
        gmsh.fltk.initialize()
        # show the contents of the solver menu
        gmsh.fltk.openTreeItem("0Modules/XFEM")
        while gmsh.fltk.isAvailable() and checkForEvent():
            gmsh.fltk.wait()
    else:
        runSolver()

    gmsh.finalize()

    return

if __name__ == "__main__":
	xfemApp()


