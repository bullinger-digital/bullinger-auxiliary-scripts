import json
import collections
import re
import csv
import argparse
import os

"""
Usage:
python process_results.py \
    --input_file annotations/models/merged_annotated_batches_gpt-4o.jsonl \
    --topics_file topics.json \
    --num_runs 10
"""

parser = argparse.ArgumentParser(description="Process batch JSONL results and calculate topic percentages.")
parser.add_argument("--input_file", "-i", required=True, help="Input merged JSONL file")
parser.add_argument("--topics_file", "-t", required=True, help="JSON file with topic definitions")
parser.add_argument("--num_runs", "-n", type=int, required=True, help="Expected number of runs per file")

args = parser.parse_args()

# Load topics from JSON file
with open(args.topics_file, "r", encoding="utf-8") as f:
    topics_data = json.load(f)
topics_list = list(topics_data.keys())

# make a list of empty files
empty_files = []
with open("empty_files2.txt", "r", encoding="utf-8") as f:
    for line in f:
        empty_file = re.sub(".txt", "", line.strip())
        empty_files.append(empty_file)


# Data structures
file_topic_counts = collections.defaultdict(lambda: collections.Counter())
file_run_counts = collections.defaultdict(set)

# Read and process the JSONL file
with open(args.input_file, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, start=1):
        if not line.strip():
            continue  # Skip blank lines

        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error on line {line_num}: {e}")
            continue

        custom_id = data.get("custom_id", "")
        match = re.match(r"(\d+)_run(\d+)", custom_id)
        if not match:
            continue

        file_id, run_number = match.groups()
        run_number = int(run_number)
        if file_id in empty_files:
            continue
        file_run_counts[file_id].add(run_number)

        try:
            content = data["response"]["body"]["choices"][0]["message"]["content"]
            cleaned_content = re.sub(r"^```json\n|\n```$", "", content.strip())
            topics_response = json.loads(cleaned_content)
            topics = topics_response.get("predefined_topics", [])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue  # Skip malformed responses

        for topic in topics:
            if topic in topics_list:
                file_topic_counts[file_id][topic] += 1

output_csv = args.input_file.replace(".jsonl", ".csv")

# Write CSV
with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["File ID"] + topics_list)

    for file_id in sorted(file_run_counts.keys(), key=int):
        topic_counts = file_topic_counts[file_id]
        percentages = [(topic_counts[topic] / args.num_runs) * 100 for topic in topics_list]
        writer.writerow([file_id] + percentages)

# Summary
expected_runs = args.num_runs
total_missing_runs = sum(
    max(0, expected_runs - len(runs)) for runs in file_run_counts.values()
)

print(f"\n✅ CSV saved to: {output_csv}")
print(f"\n📉 Total missing runs across all files: {total_missing_runs} (expected {expected_runs} per file)")