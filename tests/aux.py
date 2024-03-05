import pandas as pd
import numpy as np
import os
import meshio

print(os.getcwd())

# dfd = pd.read_excel("tests/OfemDataFile.xlsx", sheet_name=None, skiprows=[2])

# with open('aux.txt', 'w') as f:
#     f.write("ofem_tables = [\n")
#     for df in dfd:
#         f.write(f'"{df}",\n')
#     f.write("]\n\n")

df = pd.DataFrame(columns = ["id", "tag", "syst", "x", "y", "z"])
df.loc[3] = [1, "1", "global", 1.0, 1.0, 0.0]
df.loc[1] = [2, "2", "global", 1.0, 0.0, 0.0]
df.loc[1] = [2, "2", "global", 5.0, 0.0, 0.0]
print (df)
df.to_excel("lixo.xlsx", index=False)
df = pd.read_excel("lixo.xlsx")
print (df)
coords=np.array(df[["x", "y", "z"]])
print(coords[1].sum())