import os
import json
from datetime import datetime
import argparse

def load_prompt_template(prompt_template_path):
    with open(prompt_template_path, "r", encoding="utf-8") as f:
        return f.read()

def create_jsonl_files(directory, topics_data, prompt_template, model, num_runs=10, max_requests_per_batch=5000):
    """
    Creates multiple JSONL files, each with a limited number of requests.
    If the last batch has fewer than min_requests_in_last_batch requests, 
    those requests are added to the previous batch.
    """
    all_requests = []
    batch_counter = 1

    # sort files in directory
    files = os.listdir(directory)
    files.sort(key=lambda x: int(os.path.splitext(x)[0]))

    for file_name in files:
        if not file_name.endswith('.txt'):
            continue

        file_path = os.path.join(directory, file_name)
        file_id = os.path.splitext(file_name)[0]

        # if int(file_id) >= 10013:
        #     continue  # Only process files with file_id < 10013

        # print(f"Processing file: {file_name}")

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        formatted_prompt = prompt_template.replace("{{content}}", content)

        for run in range(1, num_runs + 1):
            request_body = {
                "custom_id": f"{file_id}_run{run}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": f"You are a historian working with the correspondence of Heinrich Bullinger (1504-1575). You have a list of topics here: {topics_data}. You identify these topics for each letter in the correspondence."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "max_tokens": 500
                }
            }
            all_requests.append(request_body)

    # Split into smaller batches
    batch_files = []    
    for i in range(0, len(all_requests), max_requests_per_batch):
        batch_requests = all_requests[i:i + max_requests_per_batch]

        # Create a new batch
        file_ids_in_batch = set(int(req["custom_id"].split("_")[0]) for req in batch_requests)
        min_file_id = min(file_ids_in_batch)
        max_file_id = max(file_ids_in_batch)

        batch_name = f"batches_to_process_gpt-4o/batch_{model}_{datetime.today().strftime('%Y%m%d_%H%M%S')}_part_{min_file_id}-{max_file_id}.jsonl"

        # Ensure the directory exists
        os.makedirs(os.path.dirname(batch_name), exist_ok=True)

        with open(batch_name, "w", encoding="utf-8") as f:
            for request in batch_requests:
                f.write(json.dumps(request) + "\n")

        # Add batch to batch_files list
        batch_files.append({"batch_name": batch_name, "requests": batch_requests, "min_file_id": min_file_id, "max_file_id": max_file_id})


    # Save the batch file names
    final_batch_files = [batch['batch_name'] for batch in batch_files]

    print(f"✅ Created {len(final_batch_files)} batch files")

    # Save batch file names to a text file
    with open("latest_batches.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_batch_files))

    return final_batch_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create JSONL files for batch processing.")

    parser.add_argument("--directory", "-d", required=True, help="Directory with .txt files")
    parser.add_argument("--topics_file", "-t", required=True, help="JSON file with topic definitions")
    parser.add_argument("--prompt_template", "-p", required=True, help="Prompt template file path")
    parser.add_argument("--model", "-m", default="gpt-4o", help="Model name (e.g., gpt-4o)")
    parser.add_argument("--num_runs", "-n", type=int, default=10, help="Number of runs per file")
    parser.add_argument("--max_requests_per_batch", type=int, default=20000, help="Max requests per JSONL batch")
    args = parser.parse_args()

    directory_path = args.directory
    topics_file = args.topics_file
    prompt_template_file = args.prompt_template
    model = args.model
    num_runs = args.num_runs
    max_requests_per_batch = args.max_requests_per_batch

    with open(topics_file, "r", encoding="utf-8") as f:
        topics_data = json.load(f)

    topics = "\n".join([f"{key}: {value['description']}" for key, value in topics_data.items()])
    prompt_template = load_prompt_template(prompt_template_file)

    batch_files = create_jsonl_files(directory_path, topics, prompt_template, model, num_runs, max_requests_per_batch)
    print(f"✅ Batch files saved: {batch_files}")
