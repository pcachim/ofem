import eel
import os
import pandas as pd
import openpyxl
from random import randint
import sap2000

pathname = f'{os.path.dirname(os.path.realpath(__file__))}/'
# Set web files folder
eel.init(pathname + 'web')


# Exposing the random_python function to javascript
@eel.expose    
def random_python():
    print("Random function running")
    return randint(1,100)


@eel.expose
def read_SAP2000_excel_xl():
    filename = pathname + 'sap2000_test.xlsx'
    wb_obj = openpyxl.load_workbook(filename)

    filename = pathname + 'tables.txt'
    with open(filename, 'w') as f:
        for xl in wb_obj.worksheets:
            f.write(xl.title +'\n')
        f.close()


@eel.expose
def read_SAP2000_excel():
    filename = pathname + 'sap2000_test.xlsx'
    df = pd.read_excel(filename, sheet_name=None, skiprows=lambda x: x in [0, 2])

    filename = pathname + 'tables.txt'
    with open(filename, 'w') as f:
        f.close()

@eel.expose
def read_SAP2000_s2k():
    filename = pathname + 'sap2000_test.s2k'   
    s2k = sap2000.sap2000()
    s2k.read_s2k(filename)
    db = s2k.s2kDatabase

    return

# Start the index.html file
eel.start("index.html")