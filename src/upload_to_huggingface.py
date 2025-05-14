import os
import datasets
import huggingface_hub
import json
import glob
from dotenv import load_dotenv
load_dotenv()
import yaml

def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def login_to_hf():
    """
    Login to Hugging Face
    """
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
    huggingface_hub.login()

def load_data_to_json(data_path, output_json_path):
    """
    Load markdown files from a folder, process each file, and update a JSON file.
    
    Args:
        data_path: Path to the folder containing markdown files
        
    Returns:
        data_list: List of dictionaries containing processed data
    """
    
    # Find all markdown files in the directory
    markdown_files = glob.glob(os.path.join(data_path, "*.md"))
    
    for file_path in markdown_files:
        file_name = os.path.basename(file_path)
        
        # Read entire file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Create dictionary for current file
        file_data = {
            "file_name": file_name,
            "markdown": content
        }
        save_to_json(file_data, output_json_path)
        # Add to list of data
    
def save_to_json(data, output_json_path, flag='a'):
    """
    Save processed data to a JSONL file (JSON Lines format)
    
    Args:
        data: Dictionary containing data to save
        output_json_path: Path to save the JSONL file
        flag: 'a' for append, 'w' for write
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    
    # Create the file if it doesn't exist
    if not os.path.exists(output_json_path) and flag == 'a':
        flag = 'w'
    
    # For JSONL format, write one JSON object per line
    with open(output_json_path, flag, encoding='utf-8') as json_file:
        json_file.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    print(f"Saved data to {output_json_path}")

def push_data_to_hf(json_path, hf_repo_name):
    dataset = datasets.load_dataset("json", data_files=json_path)
    print(dataset)
    dataset.push_to_hub(hf_repo_name)

if __name__ == "__main__":
    login_to_hf()   
    config = load_config("config/setting.yaml")
    load_data_to_json(config["md_processed_dir"], config["jsonl_output"])
    push_data_to_hf(config["jsonl_output"], config["hf_repo"])