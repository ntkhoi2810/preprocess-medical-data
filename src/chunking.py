import os
import re
from pathlib import Path
import yaml

def load_config(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def split_markdown_into_chunks(input_dir, output_dir, words_per_chunk=1000):
    """
    Split markdown files into chunks and save them as individual .md files
    
    Args:
        input_dir (str): Path to input directory containing markdown files
        output_dir (str): Path to output directory for markdown chunks
        words_per_chunk (int): Approximate number of words per chunk (default: 1000)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    # Find all markdown files in the input directory
    markdown_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    
    # Process each file
    for md_file in markdown_files:
        print(f"Processing {md_file}...")
        
        # Create a directory for this document's chunks
        doc_name = os.path.splitext(os.path.basename(md_file))[0]
        doc_output_dir = os.path.join(output_dir, doc_name)
        os.makedirs(doc_output_dir, exist_ok=True)
        
        # Read file content
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into paragraphs
        paragraphs = content.split("\n\n")
        
        # Initialize variables for chunking
        current_chunk = []
        current_word_count = 0
        chunk_number = 1
        
        # Process each paragraph
        for paragraph in paragraphs:
            # Count words in paragraph
            paragraph_words = len(re.findall(r'\b\w+\b', paragraph))
            
            # If adding this paragraph exceeds the word limit and we already have content,
            # save the current chunk and start a new one
            if current_word_count + paragraph_words > words_per_chunk and current_chunk:
                # Join paragraphs with double newlines to maintain formatting
                chunk_content = "\n\n".join(current_chunk)
                
                # Save chunk to a numbered markdown file
                chunk_filename = f"{chunk_number:03d}.md"
                chunk_path = os.path.join(doc_output_dir, chunk_filename)
                
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    f.write(chunk_content)
                
                print(f"Created chunk {chunk_filename} with approximately {current_word_count} words")
                
                # Reset for next chunk
                current_chunk = [paragraph]
                current_word_count = paragraph_words
                chunk_number += 1
            else:
                # Add paragraph to current chunk
                current_chunk.append(paragraph)
                current_word_count += paragraph_words
        
        # Don't forget to save the last chunk if it has content
        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunk_filename = f"{chunk_number:03d}.md"
            chunk_path = os.path.join(doc_output_dir, chunk_filename)
            
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(chunk_content)
            
            print(f"Created chunk {chunk_filename} with approximately {current_word_count} words")
        
        print(f"Split {doc_name} into {chunk_number} chunks")

if __name__ == "__main__":
    config_path = "./config/setting.yaml"
    config = load_config(config_path)

    input_directory = config['md_raw_dir']
    output_directory = config['md_chunks_dir']
    split_markdown_into_chunks(input_directory, output_directory, config['chunk_size'])
