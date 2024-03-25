import pandas as pd

# Sample dataframe
data = {'column1': ['x', 'y', 'z', 'a', 'b']}
df = pd.DataFrame(data)

# List of excluded values
exclude_list = ['y', 'z']

# Select rows where column1 values are not in exclude_list
filtered_df = df[~df['column1'].isin(exclude_list)]

print(filtered_df)