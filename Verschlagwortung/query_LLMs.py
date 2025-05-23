import os
from openai import OpenAI
import requests
import json
import re
from datetime import datetime
import argparse

"""
This script processes text files in a specified directory, queries the OpenAI API to identify central topics, and saves the results to a JSON file. It can handle multiple runs for each file and allows for incremental saving of results.

Usage example:

python3 query_LLMs.py \
  --directory test_files/original \
  --topics_file topics/topics4_en.json \
  --prompt_template prompts/noExplain2.txt \
  --model deepseek-chat \
  --num_runs 10 \
  --delete_existing
"""

def call_openai(data):
    """
    Make a POST request to the OpenAI API with the given data.
    """
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'
        },
        data=json.dumps(data)
    )
    response.raise_for_status()
    return response

def call_openai_deepseek(model, messages):
    """
    Make a POST request to the OpenAI API with the given data.
    """

    client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
    model=model,
    messages=messages,
    stream=False
    )
    
    return response

def load_topics_as_string(json_file):
    """
    Load topics and their descriptions from a JSON file.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            topics_data = json.load(f)

        # Generate a string representation of the topics for the system message
        topics_str = "\n".join([f"{key}: {value['description']}" for key, value in topics_data.items()])
        return topics_str
    
    except FileNotFoundError:
        print(f"Error: The file {json_file} was not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: The file {json_file} is not a valid JSON file.")
        return {}

def query_openai_api(content, prompt_template, topics_data, model="gpt-4"):
    """
    Query the OpenAI API to identify the central topics of a text.
    """
    

    # Create a prompt with only the new content
    formatted_prompt = prompt_template.replace("{{content}}", content)
    
    # Prepare the messages to send to OpenAI
    prompt = [
        {"role": "system", "content": f"You are a historian working with the correspondence of Heinrich Bullinger (1504-1575). You have a list of topics here: {topics_data}. You identify these topics for each letter in the correspondence."},
        {"role": "user", "content": formatted_prompt}
    ]

    data = {
        "model": model,
        "messages": prompt
    }

    try:
        if "deepseek" in model:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY environment variable is not set.")
            response = call_openai_deepseek(model, prompt)          
            return response.choices[0].message.content
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set.")
            # Use the OpenAI API
            response = call_openai(data)
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error querying OpenAI API: {e}")
        return None


def process_files(directory, prompt_template, topics_data, output_file, model="gpt-4", num_runs=5):
    """
    Process text files in a directory to identify central topics.
    Save results incrementally after each file is processed.
    """
    if os.path.exists(output_file):
        # Load existing results to avoid overwriting progress
        with open(output_file, 'r', encoding='utf-8') as f:
            file_topics = json.load(f)
    else:
        file_topics = {}

    unprocessed_files = []

    # Iterate over all text files in the directory
    for file_name in os.listdir(directory):
        if file_name.endswith('.txt'):
            file_path = os.path.join(directory, file_name)
            file_id = os.path.splitext(file_name)[0]

            # Skip if the file has already been processed
            if file_id in file_topics:
                if not file_topics[file_id]:  # Check if the values are empty
                    print(f"Reprocessing file {file_name} due to empty values.")
                else:
                    print(f"Skipping {file_name} (already processed).")
                    continue

            file_topics[file_id] = {}

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                print(f"Processing file: {file_name}")

                for run in range(1, num_runs + 1):
                    print(f"Run {run} for file {file_name}")
                    response = query_openai_api(content, prompt_template, topics_data, model=model)
                    # print("response", response)
                    if response:
                        try:
                            # Fix incorrectly formatted JSON (remove extra curly braces)
                            response = re.sub(r'{{\s*', '{', response)  # Replace opening {{
                            response = re.sub(r'\s*}}', '}', response)  # Replace closing }}

                            json_match = re.search(r'{.*}', response, re.DOTALL)
                            if json_match:
                                json_content = json_match.group()
                                parsed_json = json.loads(json_content)
                                print("parsed_json", parsed_json)
                                if 'predefined_topics' in parsed_json:
                                    try:
                                        parsed_json['predefined_topics'].sort()
                                    except Exception as e:
                                        print(f"Error sorting predefined topics: {e}")
                                        # continue
                                file_topics[file_id][f"run{run}"] = parsed_json
                                
                            else:
                                print(f"Unexpected format in response for file {file_name}: {response}")
                                unprocessed_files.append(file_name)
                                continue
                        except (SyntaxError, ValueError) as e:
                            print(f"Error evaluating response for file {file_name}: {e}\nResponse: {response}")
                            unprocessed_files.append(file_name)
                            continue
                    else:
                        print(f"Failed to process file: {file_name}")
                        unprocessed_files.append(file_name)
                        continue

                # Save progress incrementally after processing each file
                save_results(output_file, file_topics)

            except Exception as e:
                print(f"Error reading file {file_name}: {e}")
                unprocessed_files.append(file_name)

    return file_topics, unprocessed_files

def save_results(output_file, results):
    """
    Save the results to a JSON file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving results to {output_file}: {e}")

import os
import argparse
from datetime import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process text files and generate topic annotations.")
    
    parser.add_argument("--output_file", "-o", type=str, default=None,
                        help="Path to the output JSON file. If not provided, a default path is used.")
    
    parser.add_argument("--model", "-m", type=str, default="deepseek-chat",
                        help="Model to use, e.g., 'gpt-4o' or 'deepseek-chat'")
    
    parser.add_argument("--directory", "-d", type=str, required=True,
                        help="Path to the directory containing text files.")
    
    parser.add_argument("--topics_file", "-t", type=str, required=True,
                        help="Path to the JSON file with topic definitions.")
    
    parser.add_argument("--prompt_template", "-p", type=str, required=True,
                        help="Path to the text file with the prompt template.")
    
    parser.add_argument("--delete_existing", "-x", action="store_true",
                        help="Delete existing output file if it exists.")
    
    parser.add_argument("--num_runs", "-n", type=int, default=5,
                        help="Number of times to run topic detection per file.")
    
    args = parser.parse_args()
    model = args.model
    directory_path = args.directory
    topics_file = args.topics_file
    prompt_template_file = args.prompt_template
    delete_existing = args.delete_existing
    num_runs = args.num_runs


    # Check if the directory exists    
    # Extract identifiers from file paths
    test_set_name = os.path.basename(directory_path)
    prompt_name = os.path.splitext(os.path.basename(prompt_template_file))[0]
    topics_round = os.path.splitext(os.path.basename(topics_file))[0]

    if args.output_file:
        output_file = args.output_file
    else:
        output_file = f"annotations/models/{model}_{datetime.today().strftime('%Y%m%d')}_{test_set_name}_{prompt_name}_{topics_round}.json"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if delete_existing:
        try:
            os.remove(output_file)
            print(f"Deleted existing file: {output_file}")
        except FileNotFoundError:
            print(f"No existing file found to delete: {output_file}")


    # Load prompt template
    with open(prompt_template_file, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Load topics from JSON file
    topics_data = load_topics_as_string(topics_file)

    if topics_data:
        # Process files and identify topics
        results, unprocessed_files = process_files(
            directory_path,
            prompt_template,
            topics_data,
            output_file,
            model=model,
            num_runs=args.num_runs
        )

        # Write unprocessed files to file
        with open("unprocessed_files.txt", 'w', encoding='utf-8') as f:
            for file in sorted(unprocessed_files):
                print("unprocessed_files.txt", file)
                f.write(file + "\n")
    else:
        print("No topics data loaded. Exiting.")

