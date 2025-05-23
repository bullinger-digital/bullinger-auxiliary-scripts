import os
import json

# Directory containing the JSONL files
input_dir = "batch_annos"
output_file = "annotations/models/merged_annotated_batches_gpt-4o.jsonl"

# Open the output file in write mode
with open(output_file, "w", encoding="utf-8") as outfile:
    # Loop through all files in the directory
    for filename in sorted(os.listdir(input_dir)):  # Sorted for consistency
        if filename.endswith(".jsonl"):  # Process only .jsonl files
            file_path = os.path.join(input_dir, filename)
            with open(file_path, "r", encoding="utf-8") as infile:
                for line in infile:
                    outfile.write(line)  # Write each line to the output file

print(f"Merged JSONL files into {output_file}")
