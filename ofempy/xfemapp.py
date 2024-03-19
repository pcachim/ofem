import gmsh
import sys
import json

params = [
    {
        "type":"string",
        "name":"ONELAB Context/Point Template/2Condition",
        "values":["Supports"],
        "choices":["Supports", "Point loads", "Point displacements"],
    },
    {
        "type":"string",
        "name":"ONELAB Context/Point Template/3Add",
        "values":["Some action on ONELAB Context/Curve Template"],
        "attributes":{"Macro":"Action", "Aspect":"MiddleButton"}
    },
    {
        "type":"string",
        "name":"ONELAB Context/Point Template/4Close",
        "values":["Some other action on ONELAB Context/Curve Template"],
        "attributes":{"Macro":"Action", "Aspect":"RightReturnButton"}
    },

    {
        "type":"number",
        "name":"ONELAB Context/Curve Template/1Value",
        "values":[20],
        "min":0,
        "max":100,
        "step":0.1
    },
    {
        "type":"number",
        "name":"ONELAB Context/Curve Template/2Value",
        "values":[20],
        "min":0,
        "max":100,
        "step":0.1
    },
    {
        "type":"string",
        "name":"ONELAB Context/Curve Template/3Action",
        "values":["Some action on ONELAB Context/Curve Template"],
        "attributes":{"Macro":"Action", "Aspect":"MiddleButton"}
    },
    {
        "type":"string",
        "name":"ONELAB Context/Curve Template/4Other action",
        "values":["Some other action on ONELAB Context/Curve Template"],
        "attributes":{"Macro":"Action", "Aspect":"RightReturnButton"}
    },
    {
        "type":"number",
        "name":"ONELAB Context/Surface Template/0Material",
        "values":[1],
        "choices":[0, 1, 2],
        "valueLabels":{"User-defined":0, "Steel":1, "Concrete":2},
        "attributes":
            {
                "ServerActionHideMatch":"ONELAB Context/Surface Template/1.*",
                "ServerActionShowMatch 0":"ONELAB Context/Surface Template/1.*",
                "ServerActionSet 1":"%10Cond, 205, %11Diff, 97",
                "ServerActionSet 2":"%10Cond, 37, %11Diff, 12"
            }
    },
    {
        "type":"number",
        "name":"ONELAB Context/Surface Template/10Cond",
        "label":"Conductivity [Wm⁻¹K⁻¹]",
        "values":[205],
        "min":0.1,
        "max":500,
        "step":0.1,
        "visible":False
    },
    {
        "type":"number",
        "name":"ONELAB Context/Surface Template/11Diff",
        "label":"Diffusivity [mm²s⁻¹]",
        "values":[97],
        "min":10,
        "max":1200,
        "step":0.1,
        "visible":False
    },
    {
        "type":"string",
        "name":"ONELAB/Button",
        "values":["Run", "run"],
        "visible":False
    },
    {
        "type":"string",
        "name":"ONELAB/Button",
        "values":["Ofelia", "ofelia"],
        "visible":False
    },
    {
        "type":"number",
        "name":"0Modules/Solver/xFEM/1Some flag",
        "values":[0],
        "choices":[0, 1]
    },
    {
        "type":"number",
        "name":"0Modules/Solver/xFEM/2Some parameter",
        "values":[1.234],
        "min":0,
        "max":10,
        "step":0.1
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
        "name":"0Modules/Solver/xFEM/5Supports",
        "values":["select supports"],
        "attributes":{"Macro":"Action", "Aspect":"Button"}
    },
    {
        "type":"string",
        "name":"0Modules/Solver/Ofelia/6Some other action",
        "values":["do something else"],
        "attributes":{"Macro":"Action", "Aspect":"Button"}
    },
    {
        "type":"string",
        "name":"1xFEM/1Title",
        "values":["Problem title"]
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/1Supports",
        "values":["select supports"],
        "attributes":{"Macro":"Action", "Aspect":"Button"}
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/2Materials",
        "values":["select supports"],
        "attributes":{"Macro":"Action", "Aspect":"Button"}
    },
    {
        "type":"string",
        "name":"1xFEM/Geometry/3Sections",
        "values":["select supports"],
        "choices":["Supports", "Point loads", "Point displacements"]
    },
    {
        "type":"string",
        "name":"1xFEM/Load cases/11Load cases",
        "values":["DEAD"],
        "choices":["DEAD", "ADL", "Q", "S"]
    },
    {
        "type":"string",
        "name":"1xFEM/Load cases/12New case name",
        "values":["New case name"],
    },
    {
        "type":"string",
        "name":"1xFEM/Load cases/13Add case",
        "values":["add case"],
        "attributes":{"Macro":"Action", "Aspect":"Button"}
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/10Points",
        "values":["point loads"],
        "attributes":{"Macro":"Action", "Aspect":"LeftButton"}
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/11dir X",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/12dir Y",
        "values":[0],
        "visible": False
	},
    {
        "type":"number",
        "name":"1xFEM/Loads/13dir Z",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/14rot X",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/15rot Y",
        "values":[0],
        "visible": False
    },
    {
        "type":"number",
        "name":"1xFEM/Loads/16rot Z",
        "values":[0],
        "visible": False
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/2Lines",
        "values":["line loads"],
        "attributes":{"Macro":"Action", "Aspect":"MiddleButton"}
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/3Areas",
        "values":["area loads"],
        "attributes":{"Macro":"Action", "Aspect":"RightButton"}
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/4Displacements",
        "values":["line loads"],
        "attributes":{"Macro":"Action", "Aspect":"MiddleButton"}
    },
    {
        "type":"string",
        "name":"1xFEM/Loads/5Temperature",
        "values":["line loads"],
        "attributes":{"Macro":"Action", "Aspect":"MiddleButton"}
    }
]

params_dict = { k['name']: k for k in params }


def xfemApp():
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
    gmsh.model.addPhysicalGroup(1, [1], name = "sup: 111000")	
    gmsh.model.addPhysicalGroup(2, [1], name = "asec: laje")	
    gmsh.model.addPhysicalGroup(1, [1, 2, 3], name = "lsec: viga")	
    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)
    e = gmsh.model.getPhysicalGroups()
    f = gmsh.model.mesh.getNodesForPhysicalGroup(1, 1)

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
            my_list = {0: [], 1: [], 2: [], 3: []}
            # user clicked on "Some action"
            gmsh.onelab.setString("ONELAB/Action", [""])
            gmsh.fltk.setStatusMessage(
                    "Please select an entity (or press 'q' to quit)", True)
            while True:
                r, ent = gmsh.fltk.selectEntities()
                if gmsh.fltk.isAvailable() == 0: 
                    return 0
                if r and len(ent):
                    my_list[ent[0][0]].append(ent[0][1])
                else:
                    gmsh.fltk.showContextWindow(0, my_list[0][0])
                    break
            gmsh.fltk.setStatusMessage("", True)

        elif action[0] == "point loads":
            my_list = {0: [], 1: [], 2: [], 3: []}
            gmsh.onelab.setString("ONELAB/Action", [""])

            params_dict["1xFEM/Loads/11dir X"]["visible"] = True
            params_dict["1xFEM/Loads/12dir Y"]["visible"] = True
            params_dict["1xFEM/Loads/13dir Z"]["visible"] = True
            params_dict["1xFEM/Loads/14rot X"]["visible"] = True
            params_dict["1xFEM/Loads/15rot Y"]["visible"] = True
            params_dict["1xFEM/Loads/16rot Z"]["visible"] = True
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
                    my_list[ent[0][0]].append(ent[0][1])
                else:
                    gmsh.fltk.setStatusMessage("", True)

                    case = gmsh.onelab.get_string("1xFEM/Load cases/11Load cases")[0]
                    fx = gmsh.onelab.getNumber("1xFEM/Loads/11dir X")[0]
                    fy = gmsh.onelab.getNumber("1xFEM/Loads/12dir Y")[0]
                    fz = gmsh.onelab.getNumber("1xFEM/Loads/13dir Z")[0]
                    mx = gmsh.onelab.getNumber("1xFEM/Loads/14rot X")[0]
                    my = gmsh.onelab.getNumber("1xFEM/Loads/15rot Y")[0]
                    mz = gmsh.onelab.getNumber("1xFEM/Loads/16rot Z")[0]

                    params_dict["1xFEM/Loads/11dir X"]["visible"] = False
                    params_dict["1xFEM/Loads/12dir Y"]["visible"] = False
                    params_dict["1xFEM/Loads/13dir Z"]["visible"] = False
                    params_dict["1xFEM/Loads/14rot X"]["visible"] = False
                    params_dict["1xFEM/Loads/15rot Y"]["visible"] = False
                    params_dict["1xFEM/Loads/16rot Z"]["visible"] = False
                    params_list = list(params_dict.values())
                    gmsh.onelab.set(json.dumps(params_list))
                    gmsh.fltk.update()

                    break


            print('Added point load = ', case)

        elif action[0] == 'add case':
            newcase = gmsh.onelab.get_string("1xFEM/Load cases/12New case name")[0]
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


