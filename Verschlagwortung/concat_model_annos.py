"""
This script concatenates two CSV files containing topic annotations for each File ID.
It is intended for combining new annotations with existing ones.

Both input files must have identical columns.
"""

import pandas as pd
import argparse

# Argument parser for command line usage
argparser = argparse.ArgumentParser(description="Concatenate two CSV files with topic annotations.")
argparser.add_argument("file1", type=str, help="Path to the first CSV file.")
argparser.add_argument("file2", type=str, help="Path to the second CSV file.")
argparser.add_argument("--output_file", "-o", type=str, default="concatenated_annotations.csv", help="Path to save the output file.")
args = argparser.parse_args()

# Load both CSVs
df1 = pd.read_csv(args.file1, encoding='utf-8')
df2 = pd.read_csv(args.file2, encoding='utf-8')

# Concatenate rows
combined = pd.concat([df1, df2], ignore_index=True)
# sort by File ID to ensure consistent order
combined.sort_values(by="File ID", inplace=True)

# Optional: drop duplicate File IDs (keep first occurrence)
# combined = combined.drop_duplicates(subset="File ID", keep="first")

# Save the result
combined.to_csv(args.output_file, index=False, encoding='utf-8')
print(f"✅ Concatenated file saved as '{args.output_file}'")
