import json
import pandas as pd
import re
import sys
import os

"""
python convert_deepseek_annos_to_csv.py annotations/models/deepseek-chat_20250320_txts_noExplain2_topics4_en.json
"""

# Input file
input_file = sys.argv[1]
if not os.path.exists(input_file):
    sys.exit(f"❌ File not found: {input_file}")

# Create output file path
output_file = input_file.replace(".json", ".csv")
file_name = os.path.basename(input_file).replace(".json", "")

pattern = r'topic.*'

# Find all matches in the text
topic_type = re.findall(pattern, file_name)[0]

# Load topics
topics_path = f"topics/{topic_type}.json"
if not os.path.exists(topics_path):
    sys.exit(f"❌ Topics file not found: {topics_path}")
with open(topics_path, "r", encoding="utf-8") as f:
    topics_data = json.load(f)
topics = list(topics_data.keys())

# Load JSON results data
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Count topic appearances per file
topic_counts = {}
for file_num, runs in data.items():
    counts = {topic: 0 for topic in topics}
    total_runs = len(runs)

    for run in runs.values():
        for topic in run.get("predefined_topics", []):
            if topic in counts:
                counts[topic] += 1

    # Convert counts to percentages
    percentages = {
        topic: (count / total_runs) * 100 if total_runs > 0 else float('nan')
        for topic, count in counts.items()
    }
    topic_counts[file_num] = percentages

# Convert to DataFrame and clean
df = pd.DataFrame.from_dict(topic_counts, orient="index")
df.index = df.index.astype(int)
df = df.sort_index()
df = df.dropna(how='all')
df = df.loc[:, (df != 0).any(axis=0)]
df[df < 10] = 0  # Apply threshold
df = df.astype(int)

# Save to CSV with index labeled as "File ID"
df.to_csv(output_file, index_label="File ID")
print(f"✅ Saved to {output_file}")
