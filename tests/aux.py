import pandas as pd
import os

print(os.getcwd())

dfd = pd.read_excel("tests/OfemDataFile.xlsx", sheet_name=None, skiprows=[2])

with open('aux.txt', 'w') as f:
    f.write("ofem_tables = [\n")
    for df in dfd:
        f.write(f'"{df}",\n')
    f.write("]\n\n")