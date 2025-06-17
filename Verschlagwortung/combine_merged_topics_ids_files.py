"""
This script merges two CSV files containing topic annotations for files or documents and produced by the MixtureOfExperts.py script. Can be used in case if new annotations are added to the existing files. 

columns in the CSV files:
1. File ID (int): A unique identifier for a document or file.
2. Topics (str): A string-formatted list of integer topic IDs, e.g., "[2, 5]", "[10]".

"""

import pandas as pd
import ast
import argparse
import os

argparser = argparse.ArgumentParser(description="Combine two CSV files with topics and merge them by File ID.")
argparser.add_argument("file1", type=str, help="Path to the first CSV file with .")
argparser.add_argument("file2", type=str, help="Path to the second CSV file.")
args = argparser.parse_args()
file1 = args.file1
file2 = args.file2

# Load the two CSV files
df1 = pd.read_csv(file1, encoding='utf-8')
df2 = pd.read_csv(file2, encoding='utf-8')

# Convert the string list in 'Topics' column into actual Python lists
df1["Topics"] = df1["Topics"].apply(ast.literal_eval)
df2["Topics"] = df2["Topics"].apply(ast.literal_eval)

# Combine the two DataFrames
combined = pd.concat([df1, df2])

# Group by File ID and merge topics
combined = (
    combined.groupby("File ID")["Topics"]
    .apply(lambda topic_lists: sorted(set(x for sublist in topic_lists for x in sublist)))
    .reset_index()
)

# Save to CSV
combined.to_csv("merged_topics_ids.csv", index=False)
print("✅ Merged file saved as 'merged_topics.csv'")
