import os
import json
import time
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

def upload_jsonl_file(jsonl_file):
    """
    Uploads the JSONL file to OpenAI.
    """
    url = "https://api.openai.com/v1/files"
    with open(jsonl_file, "rb") as f:
        files = {
            "file": (jsonl_file, f),
            "purpose": (None, "batch")
        }
        response = requests.post(url, headers=HEADERS, files=files)

    response.raise_for_status()
    file_id = response.json()["id"]
    print(f"✅ File uploaded. File ID: {file_id}")
    return file_id

def submit_batch_request(file_id):
    """
    Submits the batch request for processing.
    """
    url = "https://api.openai.com/v1/batches"
    data = {
        "input_file_id": file_id,
        "endpoint": "/v1/chat/completions",
        "completion_window": "24h",
    }

    print("🔹 Submitting batch request...")

    response = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=data)

    if response.status_code != 200:
        print("❌ Error:", response.text)
        return None

    response.raise_for_status()
    batch_id = response.json()["id"]
    print(f"✅ Batch submitted. Batch ID: {batch_id}")
    return batch_id

def wait_for_batch_completion(batch_id):
    """
    Waits until the batch processing is complete.
    """
    url = f"https://api.openai.com/v1/batches/{batch_id}"
    while True:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        status = response.json()["status"]
        if status == "completed":
            print("✅ Batch processing completed!")
            return response.json()["output_file_id"]
        elif status in ["failed", "cancelled"]:
            print(f"❌ Batch failed: {status}")
            return None
        else:
            print(f"⏳ Batch still processing... (status: {status})")
            time.sleep(60)  # Wait 1 minute before checking again

def download_batch_results(output_file_id, batch_name):
    """
    Downloads and processes the batch results.
    """
    url = f"https://api.openai.com/v1/files/{output_file_id}/content"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    os.makedirs("annotations/batch_annos", exist_ok=True)

    results_file = f"annotations/batch_annos/{batch_name}_results.jsonl"
    with open(results_file, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"✅ Results downloaded: {results_file}")

if __name__ == "__main__":
    # # Load the latest batch file name
    # try:
    #     with open("latest_batches.txt", "r", encoding="utf-8") as f:
    #         batch_files = [line.strip() for line in f.readlines()]

    # except FileNotFoundError:
    #     print("❌ No batch file found. Please run `create_batch.py` first.")
    #     exit(1)
    batch_dir = "batches_to_process_gpt-4o"

    for jsonl_file in os.listdir(batch_dir):
        if not jsonl_file.endswith(".jsonl"):
            continue
        print(f"Processing batch file: {jsonl_file}")

        jsonl_file_path = os.path.join(batch_dir, jsonl_file)
        file_id = upload_jsonl_file(jsonl_file_path)

        batch_id = submit_batch_request(file_id)
        output_file_id = wait_for_batch_completion(batch_id)

        if output_file_id:
            download_batch_results(output_file_id, jsonl_file.replace(".jsonl", ""))

